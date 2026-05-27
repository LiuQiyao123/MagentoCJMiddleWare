"""
Magento API客户端
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
import structlog
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.core.exceptions import APIException

logger = structlog.get_logger(__name__)
settings = get_settings()


class MagentoAPIError(APIException):
    """Magento API异常"""
    pass


class MagentoProduct(BaseModel):
    """Magento产品模型"""
    id: Optional[int] = None
    sku: str = Field(description="SKU")
    name: str = Field(description="产品名称")
    price: float = Field(description="价格")
    status: int = Field(description="状态")
    visibility: int = Field(description="可见性")
    type_id: str = Field(description="产品类型")
    attribute_set_id: int = Field(description="属性集ID")
    weight: Optional[float] = Field(description="重量")


class MagentoOrder(BaseModel):
    """Magento订单模型"""
    entity_id: int = Field(description="订单ID")
    increment_id: str = Field(description="订单号")
    status: str = Field(description="订单状态")
    state: str = Field(description="订单状态")
    grand_total: float = Field(description="总金额")
    customer_email: str = Field(description="客户邮箱")
    billing_address: Dict[str, Any] = Field(description="账单地址")
    shipping_address: Dict[str, Any] = Field(description="收货地址")
    items: List[Dict[str, Any]] = Field(description="订单项")


class MagentoClient:
    """Magento API客户端"""
    
    def __init__(self):
        self.base_url = settings.MAGENTO_BASE_URL
        self.api_token = settings.MAGENTO_API_TOKEN
        self.api_user = settings.MAGENTO_API_USER
        self.api_password = settings.MAGENTO_API_PASSWORD
        self.timeout = settings.MAGENTO_TIMEOUT
        self.max_retries = settings.MAGENTO_MAX_RETRIES
        
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
        
    async def initialize(self) -> None:
        """初始化客户端"""
        try:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            
            # 测试连接
            try:
                await self._test_connection()
                logger.info("Magento API connection test passed")
            except Exception as e:
                logger.warning("Magento API connection test failed (non-blocking)", extra={"error": str(e)})
            
            logger.info("Magento API client initialized successfully")
            
        except Exception as e:
            # 初始化本身的错误（如httpx客户端创建失败）仍然抛出
            logger.error("Failed to initialize Magento API client", extra={"error": str(e)})
            raise MagentoAPIError(
                error_code="MAGENTO_INIT_ERROR",
                message="Failed to initialize Magento API client",
                details={"error": str(e)}
            )
    
    async def close(self) -> None:
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _test_connection(self) -> None:
        """测试连接"""
        try:
            # 使用不需要特殊权限的端点进行测试
            response = await self._client.get(
                f"{self.base_url}/rest/V1/directory/currency",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise MagentoAPIError(
                    error_code="MAGENTO_CONNECTION_ERROR",
                    message="Failed to connect to Magento API",
                    details={"status_code": response.status_code}
                )
            
            logger.info("Magento API connection test passed")
            
        except httpx.RequestError as e:
            logger.error("Magento API connection test failed", extra={"error": str(e)})
            raise MagentoAPIError(
                error_code="MAGENTO_NETWORK_ERROR",
                message="Network error during Magento API connection test",
                details={"error": str(e)}
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def _refresh_token(self) -> None:
        """重新获取 Magento admin token（401 时自动调用）"""
        try:
            login_url = f"{self.base_url}/rest/V1/integration/admin/token"
            resp = await self._client.post(
                login_url,
                json={"username": self.api_user, "password": self.api_password},
                headers={"Content-Type": "application/json"}
            )
            if resp.status_code == 200:
                new_token = resp.json()
                if isinstance(new_token, str) and len(new_token) > 20:
                    self.api_token = new_token
                    logger.info("Magento token refreshed automatically")
                    return
            logger.warning("Token refresh failed", extra={"status": resp.status_code, "body": resp.text[:100]})
        except Exception as e:
            logger.error("Token refresh error", extra={"error": str(e)})
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """发送API请求（带自动token刷新）"""
        try:
            url = f"{self.base_url}/rest/V1/{endpoint.lstrip('/')}"
            
            response = await self._client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self._get_headers()
            )
            
            # 401 → token过期 → 刷新后重试一次
            if response.status_code == 401 and retry_count < 1:
                logger.info("Token expired, refreshing...")
                await self._refresh_token()
                response = await self._client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=self._get_headers()
                )
                if response.status_code in [200, 201]:
                    return response.json()
            
            if response.status_code not in [200, 201]:
                raise MagentoAPIError(
                    error_code="MAGENTO_REQUEST_ERROR",
                    message=f"Magento API request failed with status {response.status_code}",
                    details={
                        "status_code": response.status_code,
                        "response": response.text,
                        "endpoint": endpoint
                    }
                )
            
            return response.json()
            
        except httpx.RequestError as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)  # 指数退避
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            logger.error("Magento API network error", extra={"error": str(e), "endpoint": endpoint})
            raise MagentoAPIError(
                error_code="MAGENTO_NETWORK_ERROR",
                message="Network error during Magento API request",
                details={"error": str(e), "endpoint": endpoint}
            )
        except MagentoAPIError:
            raise
        except Exception as e:
            logger.error("Magento API request error", extra={"error": str(e), "endpoint": endpoint})
            raise MagentoAPIError(
                error_code="MAGENTO_REQUEST_ERROR",
                message="Unexpected error during Magento API request",
                details={"error": str(e), "endpoint": endpoint}
            )
    
    # 产品相关接口
    async def get_products(
        self,
        page: int = 1,
        page_size: int = 20,
        search_criteria: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """获取产品列表"""
        params = {
            "searchCriteria[pageSize]": page_size,
            "searchCriteria[currentPage]": page
        }
        
        if search_criteria:
            for key, value in search_criteria.items():
                params[f"searchCriteria[{key}]"] = value
        
        return await self._make_request("GET", "/products", params=params)
    
    async def get_product(self, sku: str) -> Dict[str, Any]:
        """获取单个产品"""
        return await self._make_request("GET", f"/products/{sku}")
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建产品"""
        return await self._make_request("POST", "/products", data={"product": product_data})
    
    async def update_product(self, sku: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新产品"""
        return await self._make_request("PUT", f"/products/{sku}", data={"product": product_data})
    
    async def delete_product(self, sku: str) -> bool:
        """删除产品"""
        result = await self._make_request("DELETE", f"/products/{sku}")
        return result is True
    
    # 库存相关接口
    async def get_stock_item(self, product_id: int) -> Dict[str, Any]:
        """获取库存信息"""
        return await self._make_request("GET", f"/stockItems/{product_id}")
    
    async def update_stock(self, sku: str, qty: int, is_in_stock: bool = True) -> Dict[str, Any]:
        """更新库存"""
        stock_data = {
            "stockItem": {
                "qty": qty,
                "is_in_stock": is_in_stock
            }
        }
        return await self._make_request("PUT", f"/products/{sku}/stockItems/1", data=stock_data)
    
    # 订单相关接口
    async def get_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        search_criteria: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """获取订单列表"""
        params = {
            "searchCriteria[pageSize]": page_size,
            "searchCriteria[currentPage]": page
        }
        
        if search_criteria:
            for key, value in search_criteria.items():
                params[f"searchCriteria[{key}]"] = value
        
        return await self._make_request("GET", "/orders", params=params)
    
    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """获取单个订单"""
        return await self._make_request("GET", f"/orders/{order_id}")
    
    async def update_order_status(self, order_id: int, status: str) -> Dict[str, Any]:
        """更新订单状态"""
        return await self._make_request("POST", f"/orders/{order_id}/status", data={"status": status})
    
    async def create_shipment(self, order_id: int, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建发货单"""
        shipment_data = {
            "items": items,
            "notify": True,
            "appendComment": True,
            "comment": {
                "comment": "Order shipped via CJ Dropshipping",
                "is_visible_on_front": True
            }
        }
        return await self._make_request("POST", f"/order/{order_id}/ship", data=shipment_data)
    
    async def add_tracking_info(
        self,
        order_id: int,
        tracking_number: str,
        carrier_code: str,
        title: str
    ) -> Dict[str, Any]:
        """添加跟踪信息"""
        tracking_data = {
            "entity": {
                "order_id": order_id,
                "parent_id": order_id,
                "track_number": tracking_number,
                "carrier_code": carrier_code,
                "title": title
            }
        }
        return await self._make_request("POST", f"/orders/{order_id}/tracks", data=tracking_data)
    
    # 客户相关接口
    async def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """获取客户信息"""
        return await self._make_request("GET", f"/customers/{customer_id}")
    
    async def get_customer_by_email(self, email: str) -> Dict[str, Any]:
        """根据邮箱获取客户信息"""
        params = {
            "searchCriteria[filterGroups][0][filters][0][field]": "email",
            "searchCriteria[filterGroups][0][filters][0][value]": email,
            "searchCriteria[filterGroups][0][filters][0][conditionType]": "eq"
        }
        return await self._make_request("GET", "/customers/search", params=params)
    
    # 其他接口
    async def get_categories(self) -> Dict[str, Any]:
        """获取商品分类"""
        return await self._make_request("GET", "/categories")
    
    async def get_attributes(self) -> Dict[str, Any]:
        """获取产品属性"""
        return await self._make_request("GET", "/products/attributes")
    
    async def get_attribute_sets(self) -> Dict[str, Any]:
        """获取属性集"""
        return await self._make_request("GET", "/products/attribute-sets/sets/list")


# 全局Magento客户端实例
_magento_client: Optional[MagentoClient] = None


async def get_magento_client() -> MagentoClient:
    """获取Magento客户端实例"""
    global _magento_client
    
    if _magento_client is None:
        _magento_client = MagentoClient()
        await _magento_client.initialize()
    
    return _magento_client


async def close_magento_client() -> None:
    """关闭Magento客户端"""
    global _magento_client
    
    if _magento_client:
        await _magento_client.close()
        _magento_client = None 