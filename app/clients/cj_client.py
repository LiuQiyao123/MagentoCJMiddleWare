"""
CJ Dropshipping API客户端
"""
import asyncio
import hashlib
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import httpx
import structlog
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.core.exceptions import APIException

logger = structlog.get_logger(__name__)
settings = get_settings()


class CJAPIError(APIException):
    """CJ API异常"""
    pass


class CJAuthResponse(BaseModel):
    """CJ认证响应模型"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    
    
class CJProductVariant(BaseModel):
    """CJ产品变体模型"""
    vid: str = Field(description="变体ID")
    sku: str = Field(description="SKU")
    price: float = Field(description="价格")
    original_price: float = Field(description="原价")
    stock: int = Field(description="库存")
    variant_name: str = Field(description="变体名称")
    variant_key: str = Field(description="变体键")
    
    
class CJProduct(BaseModel):
    """CJ产品模型"""
    pid: str = Field(description="产品ID")
    product_name: str = Field(description="产品名称")
    product_name_en: str = Field(description="英文产品名称")
    product_sku: str = Field(description="产品SKU")
    sell_price: float = Field(description="销售价格")
    original_price: float = Field(description="原价")
    product_weight: float = Field(description="产品重量")
    product_unit: str = Field(description="重量单位")
    category_id: str = Field(description="分类ID")
    category_name: str = Field(description="分类名称")
    description: str = Field(description="产品描述")
    product_image: str = Field(description="产品图片")
    variants: List[CJProductVariant] = Field(default_factory=list, description="产品变体")


class CJOrderItem(BaseModel):
    """CJ订单项模型"""
    product_id: str = Field(description="产品ID")
    variant_id: str = Field(description="变体ID")
    quantity: int = Field(description="数量")
    
    
class CJShippingAddress(BaseModel):
    """CJ收货地址模型"""
    country: str = Field(description="国家")
    province: str = Field(description="省份")
    city: str = Field(description="城市")
    address: str = Field(description="详细地址")
    zip: str = Field(description="邮编")
    phone: str = Field(description="电话")
    name: str = Field(description="收件人姓名")
    
    
class CJOrderResponse(BaseModel):
    """CJ订单响应模型"""
    order_id: str = Field(description="订单ID")
    order_number: str = Field(description="订单号")
    status: str = Field(description="订单状态")
    total_amount: float = Field(description="总金额")
    
    
class CJTrackingInfo(BaseModel):
    """CJ物流跟踪信息模型"""
    tracking_number: str = Field(description="跟踪号")
    carrier: str = Field(description="承运商")
    status: str = Field(description="物流状态")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="物流事件")


class CJClient:
    """CJ Dropshipping API客户端"""
    
    def __init__(self):
        self.base_url = settings.CJ_API_BASE_URL
        self.email = settings.CJ_API_EMAIL
        self.password = settings.CJ_API_PASSWORD
        self.timeout = settings.CJ_TIMEOUT
        self.max_retries = settings.CJ_MAX_RETRIES
        
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
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
            
            # 获取访问令牌
            await self._authenticate()
            
            logger.info("CJ API client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize CJ API client", error=str(e))
            raise CJAPIError(
                error_code="CJ_INIT_ERROR",
                message="Failed to initialize CJ API client",
                details={"error": str(e)}
            )
    
    async def close(self) -> None:
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
            
    async def _authenticate(self) -> None:
        """认证获取访问令牌"""
        try:
            # 构造认证请求
            auth_data = {
                "email": self.email,
                "password": self.password
            }
            
            # 发送认证请求
            response = await self._client.post(
                f"{self.base_url}/authentication/getAccessToken",
                json=auth_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise CJAPIError(
                    error_code="CJ_AUTH_ERROR",
                    message="Failed to authenticate with CJ API",
                    details={"status_code": response.status_code, "response": response.text}
                )
            
            result = response.json()
            
            if not result.get("result"):
                raise CJAPIError(
                    error_code="CJ_AUTH_ERROR",
                    message="Authentication failed",
                    details={"response": result}
                )
            
            # 保存访问令牌
            self._access_token = result["data"]["accessToken"]
            self._token_expires_at = datetime.now() + timedelta(seconds=result["data"]["expiresIn"])
            
            logger.info("CJ API authentication successful")
            
        except httpx.RequestError as e:
            logger.error("CJ API authentication network error", error=str(e))
            raise CJAPIError(
                error_code="CJ_NETWORK_ERROR",
                message="Network error during authentication",
                details={"error": str(e)}
            )
        except Exception as e:
            logger.error("CJ API authentication error", error=str(e))
            raise
    
    async def _ensure_authenticated(self) -> None:
        """确保认证状态有效"""
        if not self._access_token or not self._token_expires_at:
            await self._authenticate()
            return
            
        # 检查令牌是否即将过期（提前5分钟刷新）
        if datetime.now() >= self._token_expires_at - timedelta(minutes=5):
            await self._authenticate()
    
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
            await self._ensure_authenticated()
            
            headers = {
                "CJ-Access-Token": self._access_token,
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            # 发送请求
            response = await self._client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers
            )
            
            # 处理响应
            if response.status_code == 401 and retry_count < self.max_retries:
                # 令牌过期，重新认证后重试
                await self._authenticate()
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            if response.status_code not in [200, 201]:
                raise CJAPIError(
                    error_code="CJ_REQUEST_ERROR",
                    message=f"CJ API request failed with status {response.status_code}",
                    details={
                        "status_code": response.status_code,
                        "response": response.text,
                        "endpoint": endpoint
                    }
                )
            
            result = response.json()
            
            if not result.get("result"):
                raise CJAPIError(
                    error_code="CJ_API_ERROR",
                    message="CJ API returned error",
                    details={"response": result, "endpoint": endpoint}
                )
            
            return result
            
        except httpx.RequestError as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)  # 指数退避
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            logger.error("CJ API network error", error=str(e), endpoint=endpoint)
            raise CJAPIError(
                error_code="CJ_NETWORK_ERROR",
                message="Network error during CJ API request",
                details={"error": str(e), "endpoint": endpoint}
            )
        except CJAPIError:
            raise
        except Exception as e:
            logger.error("CJ API request error", error=str(e), endpoint=endpoint)
            raise CJAPIError(
                error_code="CJ_REQUEST_ERROR",
                message="Unexpected error during CJ API request",
                details={"error": str(e), "endpoint": endpoint}
            )
    
    # 产品相关接口
    async def search_products(
        self,
        keyword: Optional[str] = None,
        category_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """搜索产品"""
        params = {
            "current": page,
            "pageSize": page_size
        }
        
        if keyword:
            params["name"] = keyword
        if category_id:
            params["categoryId"] = category_id
            
        return await self._make_request("GET", "/product/list", params=params)
    
    async def get_product_detail(self, product_id: str) -> Dict[str, Any]:
        """获取产品详情"""
        return await self._make_request("GET", f"/product/query", params={"pid": product_id})
    
    async def get_product_variants(self, product_id: str) -> Dict[str, Any]:
        """获取产品变体"""
        return await self._make_request("GET", "/product/variant/query", params={"pid": product_id})
    
    async def get_product_inventory(self, product_id: str, variant_id: Optional[str] = None) -> Dict[str, Any]:
        """获取产品库存"""
        params = {"pid": product_id}
        if variant_id:
            params["vid"] = variant_id
            
        return await self._make_request("GET", "/product/inventory/query", params=params)
    
    # 订单相关接口
    async def create_order(
        self,
        order_number: str,
        products: List[CJOrderItem],
        shipping_address: CJShippingAddress,
        remark: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建订单"""
        order_data = {
            "orderNumber": order_number,
            "shippingAddress": shipping_address.dict(),
            "products": [item.dict() for item in products]
        }
        
        if remark:
            order_data["remark"] = remark
            
        return await self._make_request("POST", "/shopping/order/createOrder", data=order_data)
    
    async def get_order_detail(self, order_id: str) -> Dict[str, Any]:
        """获取订单详情"""
        return await self._make_request("GET", "/shopping/order/getOrderDetail", params={"orderId": order_id})
    
    async def get_order_list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取订单列表"""
        params = {
            "current": page,
            "pageSize": page_size
        }
        
        if status:
            params["status"] = status
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
            
        return await self._make_request("GET", "/shopping/order/getOrderList", params=params)
    
    async def cancel_order(self, order_id: str, reason: str) -> Dict[str, Any]:
        """取消订单"""
        return await self._make_request(
            "POST",
            "/shopping/order/cancelOrder",
            data={"orderId": order_id, "reason": reason}
        )
    
    # 物流相关接口
    async def get_shipping_methods(self, country_code: str) -> Dict[str, Any]:
        """获取物流方式"""
        return await self._make_request("GET", "/logistic/getLogisticList", params={"countryCode": country_code})
    
    async def get_shipping_cost(
        self,
        products: List[Dict[str, Any]],
        country_code: str,
        province: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取物流费用"""
        data = {
            "products": products,
            "countryCode": country_code
        }
        
        if province:
            data["province"] = province
            
        return await self._make_request("POST", "/logistic/freightCalculate", data=data)
    
    async def get_tracking_info(self, order_id: str) -> Dict[str, Any]:
        """获取物流跟踪信息"""
        return await self._make_request("GET", "/logistic/getTrackNumber", params={"orderId": order_id})
    
    async def track_package(self, tracking_number: str, carrier: str) -> Dict[str, Any]:
        """跟踪包裹"""
        return await self._make_request(
            "GET",
            "/logistic/trackPackage",
            params={"trackingNumber": tracking_number, "carrier": carrier}
        )
    
    # 其他接口
    async def get_categories(self) -> Dict[str, Any]:
        """获取商品分类"""
        return await self._make_request("GET", "/product/getCategory")
    
    async def get_popular_categories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门分类（产品数量最多的分类）"""
        try:
            categories_response = await self.get_categories()
            categories = categories_response.get("data", {}).get("list", [])
            
            # 按产品数量排序，返回前N个热门分类
            popular_categories = sorted(
                categories,
                key=lambda x: x.get("productCount", 0),
                reverse=True
            )[:limit]
            
            return popular_categories
            
        except Exception as e:
            logger.error("Failed to get popular categories", error=str(e))
            return []
    
    async def get_category_products(self, category_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取指定分类的所有产品"""
        try:
            products = []
            page = 1
            page_size = 20
            
            while len(products) < limit:
                response = await self.search_products(
                    category_id=category_id,
                    page=page,
                    page_size=min(page_size, limit - len(products))
                )
                
                page_products = response.get("data", {}).get("list", [])
                if not page_products:
                    break
                    
                products.extend(page_products)
                page += 1
                
                # 添加延迟避免API限制
                await asyncio.sleep(0.5)
            
            return products[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get products for category {category_id}", error=str(e))
            return []
    
    async def get_countries(self) -> Dict[str, Any]:
        """获取支持的国家列表"""
        return await self._make_request("GET", "/support/getCountry")
    
    async def validate_address(self, address: CJShippingAddress) -> Dict[str, Any]:
        """验证收货地址"""
        return await self._make_request("POST", "/support/validateAddress", data=address.dict())


# 全局CJ客户端实例
_cj_client: Optional[CJClient] = None


async def get_cj_client() -> CJClient:
    """获取CJ客户端实例"""
    global _cj_client
    
    if _cj_client is None:
        _cj_client = CJClient()
        await _cj_client.initialize()
    
    return _cj_client


async def close_cj_client() -> None:
    """关闭CJ客户端"""
    global _cj_client
    
    if _cj_client:
        await _cj_client.close()
        _cj_client = None 