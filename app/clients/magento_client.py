"""
Magento API客户端
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
import structlog
from pydantic import BaseModel, Field
from requests_oauthlib import OAuth1

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
        self.consumer_key = settings.MAGENTO_CONSUMER_KEY
        self.consumer_secret = settings.MAGENTO_CONSUMER_SECRET
        self.access_token = settings.MAGENTO_ACCESS_TOKEN
        self.access_token_secret = settings.MAGENTO_ACCESS_TOKEN_SECRET
        self.timeout = settings.MAGENTO_TIMEOUT
        self.max_retries = settings.MAGENTO_MAX_RETRIES
        self.verify_ssl = settings.VERIFY_SSL
        self.ssl_cert_path = settings.SSL_CERT_PATH
        
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
            # 配置SSL验证
            verify_ssl = self.ssl_cert_path if self.ssl_cert_path else self.verify_ssl
            
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
                verify=verify_ssl
            )
            
            # 测试连接
            await self._test_connection()
            
            logger.info("Magento API client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Magento API client", error=str(e))
            raise MagentoAPIError(
                message="Failed to initialize Magento API client",
                error_code="MAGENTO_INIT_ERROR",
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
            response = await self._client.get(
                f"{self.base_url}/rest/V1/directory/countries",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise MagentoAPIError(
                    message="Failed to connect to Magento API",
                    error_code="MAGENTO_CONNECTION_ERROR",
                    details={"status_code": response.status_code}
                )
            
            logger.info("Magento API connection test passed")
            
        except httpx.RequestError as e:
            logger.error("Magento API connection test failed", error=str(e))
            raise MagentoAPIError(
                message="Network error during Magento API connection test",
                error_code="MAGENTO_NETWORK_ERROR",
                details={"error": str(e)}
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _get_oauth_headers(self, method: str, url: str, data: Optional[Dict] = None) -> Dict[str, str]:
        """获取OAuth认证头"""
        oauth = OAuth1(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret
        )
        
        # 使用requests库生成OAuth签名
        import requests
        from urllib.parse import urlencode
        
        # 准备请求数据
        if data:
            body = requests.utils.json.dumps(data)
        else:
            body = ""
        
        # 生成OAuth签名
        oauth_request = oauth.sign(
            method=method,
            url=url,
            body=body,
            headers={"Content-Type": "application/json"}
        )
        
        return dict(oauth_request.headers)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """发送API请求"""
        try:
            url = f"{self.base_url}/rest/V1/{endpoint.lstrip('/')}"
            
            # 获取OAuth认证头
            oauth_headers = self._get_oauth_headers(method, url, data)
            headers = {**self._get_headers(), **oauth_headers}
            
            response = await self._client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers
            )
            
            if response.status_code not in [200, 201]:
                raise MagentoAPIError(
                    message=f"Magento API request failed with status {response.status_code}",
                    error_code="MAGENTO_REQUEST_ERROR",
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
            
            logger.error("Magento API network error", error=str(e), endpoint=endpoint)
            raise MagentoAPIError(
                message="Network error during Magento API request",
                error_code="MAGENTO_NETWORK_ERROR",
                details={"error": str(e), "endpoint": endpoint}
            )
        except MagentoAPIError:
            raise
        except Exception as e:
            logger.error("Magento API request error", error=str(e), endpoint=endpoint)
            raise MagentoAPIError(
                message="Unexpected error during Magento API request",
                error_code="MAGENTO_REQUEST_ERROR",
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