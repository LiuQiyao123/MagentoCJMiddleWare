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
from app.utils.rate_limiter import get_rate_limiter, APIEndpoint
from app.utils.token_manager import get_token_manager

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
        self.api_key = settings.CJ_API_KEY
        self.timeout = settings.CJ_TIMEOUT
        self.max_retries = settings.CJ_MAX_RETRIES
        self.verify_ssl = settings.VERIFY_SSL
        self.ssl_cert_path = settings.SSL_CERT_PATH
        
        self._client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
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
            
            logger.info("CJ API client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize CJ API client", error=str(e))
            raise CJAPIError(
                message="Failed to initialize CJ API client",
                error_code="CJ_INIT_ERROR",
                details={"error": str(e)}
            )
    
    async def close(self) -> None:
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
            

    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """发送API请求（内部方法，不包含频率限制）"""
        try:
            # 确保已认证
            await self._ensure_authenticated()
            
            headers = {
                "Authorization": f"Bearer {self._access_token}",
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
                # Token过期，等待一段时间后重新获取token
                logger.warning("CJ API token expired, waiting before refresh...")
                await asyncio.sleep(5)  # 等待5秒避免频率限制
                self._access_token = None
                self._token_expires_at = None
                await self._ensure_authenticated()
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            if response.status_code not in [200, 201]:
                raise CJAPIError(
                    message=f"CJ API request failed with status {response.status_code}",
                    error_code="CJ_REQUEST_ERROR",
                    details={
                        "status_code": response.status_code,
                        "response": response.text,
                        "endpoint": endpoint
                    }
                )
            
            result = response.json()
            
            if not result.get("result"):
                raise CJAPIError(
                    message="CJ API returned error",
                    error_code="CJ_API_ERROR",
                    details={"response": result, "endpoint": endpoint}
                )
            
            return result
            
        except httpx.RequestError as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)  # 指数退避
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            
            logger.error("CJ API network error", error=str(e), endpoint=endpoint)
            raise CJAPIError(
                message="Network error during CJ API request",
                error_code="CJ_NETWORK_ERROR",
                details={"error": str(e), "endpoint": endpoint}
            )
        except CJAPIError:
            raise
        except Exception as e:
            logger.error("CJ API request error", error=str(e), endpoint=endpoint)
            raise CJAPIError(
                message="Unexpected error during CJ API request",
                error_code="CJ_REQUEST_ERROR",
                details={"error": str(e), "endpoint": endpoint}
            )
    
    async def _make_rate_limited_request(
        self,
        method: str,
        endpoint: str,
        api_endpoint: APIEndpoint,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发送带频率限制的API请求"""
        limiter = get_rate_limiter()
        
        try:
            # 获取调用许可
            await limiter.acquire(api_endpoint)
            
            # 执行API调用
            result = await self._make_request(method, endpoint, data, params)
            
            # 报告成功
            limiter.report_success(api_endpoint)
            
            return result
            
        except Exception as e:
            # 报告失败
            limiter.report_error(api_endpoint, str(e))
            raise
    
    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        try:
            # 配置SSL验证
            verify_ssl = self.ssl_cert_path if self.ssl_cert_path else self.verify_ssl
            
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
                verify=verify_ssl
            ) as client:
                response = await client.post(
                    f"{self.base_url}/authentication/getAccessToken",
                    json={
                        "email": self.email,
                        "password": self.api_key
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                logger.info("CJ API response", status_code=response.status_code, response_text=response.text)
                
                if response.status_code != 200:
                    raise CJAPIError(
                        message=f"Failed to get access token: {response.status_code}",
                        error_code="CJ_AUTH_ERROR",
                        details={"status_code": response.status_code, "response": response.text}
                    )
                
                result = response.json()
                logger.info("CJ API parsed response", result=result)
                
                if not result.get("result"):
                    raise CJAPIError(
                        message="Failed to get access token",
                        error_code="CJ_AUTH_ERROR",
                        details={"response": result}
                    )
                
                data = result.get("data", {})
                access_token = data.get("accessToken")
                refresh_token = data.get("refreshToken")
                access_token_expiry = data.get("accessTokenExpiryDate")
                
                logger.info("CJ API token data", 
                          access_token=access_token[:10] + "..." if access_token else None,
                          refresh_token=refresh_token[:10] + "..." if refresh_token else None,
                          expiry=access_token_expiry)
                
                if not access_token:
                    raise CJAPIError(
                        message="No access token in response",
                        error_code="CJ_AUTH_ERROR",
                        details={"response": result}
                    )
                
                # 设置token过期时间（15天）
                self._access_token = access_token
                self._refresh_token = refresh_token
                
                # 解析过期时间
                if access_token_expiry:
                    try:
                        # 解析ISO格式的时间字符串
                        expiry_dt = datetime.fromisoformat(access_token_expiry.replace('Z', '+00:00'))
                        self._token_expires_at = expiry_dt
                    except Exception as e:
                        logger.warning("Failed to parse token expiry date", error=str(e), expiry=access_token_expiry)
                        # 如果解析失败，使用默认15天
                        from datetime import timezone
                        self._token_expires_at = datetime.now(timezone.utc) + timedelta(days=15)
                else:
                    # 如果没有过期时间，使用默认15天
                    from datetime import timezone
                    self._token_expires_at = datetime.now(timezone.utc) + timedelta(days=15)
                
                logger.info("Successfully obtained CJ access token", 
                          expires_at=self._token_expires_at.isoformat())
                return access_token
                
        except Exception as e:
            logger.error("Failed to get access token", error=str(e))
            raise CJAPIError(
                message="Failed to get access token",
                error_code="CJ_AUTH_ERROR",
                details={"error": str(e)}
            )
    
    async def _refresh_access_token(self) -> str:
        """使用refresh token刷新access token"""
        try:
            if not self._refresh_token:
                raise CJAPIError(
                    message="No refresh token available",
                    error_code="CJ_AUTH_ERROR"
                )
            
            # 配置SSL验证
            verify_ssl = self.ssl_cert_path if self.ssl_cert_path else self.verify_ssl
            
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
                verify=verify_ssl
            ) as client:
                response = await client.post(
                    f"{self.base_url}/authentication/refreshAccessToken",
                    json={
                        "refreshToken": self._refresh_token
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                logger.info("CJ API refresh response", status_code=response.status_code, response_text=response.text)
                
                if response.status_code != 200:
                    raise CJAPIError(
                        message=f"Failed to refresh access token: {response.status_code}",
                        error_code="CJ_AUTH_ERROR",
                        details={"status_code": response.status_code, "response": response.text}
                    )
                
                result = response.json()
                logger.info("CJ API refresh parsed response", result=result)
                
                if not result.get("result"):
                    raise CJAPIError(
                        message="Failed to refresh access token",
                        error_code="CJ_AUTH_ERROR",
                        details={"response": result}
                    )
                
                data = result.get("data", {})
                access_token = data.get("accessToken")
                refresh_token = data.get("refreshToken")
                access_token_expiry = data.get("accessTokenExpiryDate")
                
                logger.info("CJ API refresh token data", 
                          access_token=access_token[:10] + "..." if access_token else None,
                          refresh_token=refresh_token[:10] + "..." if refresh_token else None,
                          expiry=access_token_expiry)
                
                if not access_token:
                    raise CJAPIError(
                        message="No access token in refresh response",
                        error_code="CJ_AUTH_ERROR",
                        details={"response": result}
                    )
                
                # 更新token
                self._access_token = access_token
                if refresh_token:
                    self._refresh_token = refresh_token
                
                # 解析过期时间
                if access_token_expiry:
                    try:
                        expiry_dt = datetime.fromisoformat(access_token_expiry.replace('Z', '+00:00'))
                        self._token_expires_at = expiry_dt
                    except Exception as e:
                        logger.warning("Failed to parse refresh token expiry date", error=str(e), expiry=access_token_expiry)
                        self._token_expires_at = datetime.now(timezone.utc) + timedelta(days=15)
                else:
                    self._token_expires_at = datetime.now(timezone.utc) + timedelta(days=15)
                
                logger.info("Successfully refreshed CJ access token", 
                          expires_at=self._token_expires_at.isoformat())
                return access_token
                
        except Exception as e:
            logger.error("Failed to refresh access token", error=str(e))
            raise CJAPIError(
                message="Failed to refresh access token",
                error_code="CJ_AUTH_ERROR",
                details={"error": str(e)}
            )
    
    async def _ensure_authenticated(self) -> None:
        """确保已认证"""
        from datetime import timezone
        
        # 如果已有有效token，直接返回
        if self._access_token and self._token_expires_at and datetime.now(timezone.utc) < self._token_expires_at:
            return
        
        # 清除过期token
        self._access_token = None
        self._token_expires_at = None
        
        # 优先尝试使用refresh token
        if self._refresh_token:
            try:
                logger.info("Attempting to refresh access token...")
                await self._refresh_access_token()
                return
            except Exception as e:
                logger.warning("Failed to refresh token, will try getAccessToken", error=str(e))
                # 如果refresh失败，清除refresh token
                self._refresh_token = None
        
        # 如果refresh失败或没有refresh token，使用getAccessToken
        logger.info("Getting new access token...")
        await self._get_access_token()
    
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
            
        return await self._make_rate_limited_request(
            "GET", 
            "/product/list", 
            APIEndpoint.PRODUCT_SEARCH, 
            params=params
        )
    
    async def get_product_detail(self, product_id: str) -> Dict[str, Any]:
        """获取产品详情"""
        return await self._make_rate_limited_request(
            "GET", 
            f"/product/query", 
            APIEndpoint.PRODUCT_DETAIL, 
            params={"pid": product_id}
        )
    
    async def get_product_variants(self, product_id: str) -> Dict[str, Any]:
        """获取产品变体"""
        return await self._make_rate_limited_request(
            "GET", 
            "/product/variant/query", 
            APIEndpoint.PRODUCT_DETAIL, 
            params={"pid": product_id}
        )
    
    async def get_product_inventory(self, product_id: str, variant_id: Optional[str] = None) -> Dict[str, Any]:
        """获取产品库存"""
        params = {"pid": product_id}
        if variant_id:
            params["vid"] = variant_id
            
        return await self._make_rate_limited_request(
            "GET", 
            "/product/inventory/query", 
            APIEndpoint.PRODUCT_INVENTORY, 
            params=params
        )
    
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
            
        return await self._make_rate_limited_request(
            "POST", 
            "/shopping/order/createOrder", 
            APIEndpoint.ORDER_CREATE, 
            data=order_data
        )
    
    async def get_order_detail(self, order_id: str) -> Dict[str, Any]:
        """获取订单详情"""
        return await self._make_rate_limited_request(
            "GET", 
            "/shopping/order/getOrderDetail", 
            APIEndpoint.ORDER_DETAIL, 
            params={"orderId": order_id}
        )
    
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
            
        return await self._make_rate_limited_request(
            "GET", 
            "/shopping/order/getOrderList", 
            APIEndpoint.ORDER_LIST, 
            params=params
        )
    
    async def cancel_order(self, order_id: str, reason: str) -> Dict[str, Any]:
        """取消订单"""
        return await self._make_rate_limited_request(
            "POST",
            "/shopping/order/cancelOrder",
            APIEndpoint.ORDER_CANCEL,
            data={"orderId": order_id, "reason": reason}
        )
    
    # 物流相关接口
    async def get_shipping_methods(self, country_code: str) -> Dict[str, Any]:
        """获取物流方式"""
        return await self._make_rate_limited_request(
            "GET", 
            "/logistic/getLogisticList", 
            APIEndpoint.SHIPPING_METHODS, 
            params={"countryCode": country_code}
        )
    
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
            
        return await self._make_rate_limited_request(
            "POST", 
            "/logistic/freightCalculate", 
            APIEndpoint.SHIPPING_COST, 
            data=data
        )
    
    async def get_tracking_info(self, order_id: str) -> Dict[str, Any]:
        """获取物流跟踪信息"""
        return await self._make_rate_limited_request(
            "GET", 
            "/logistic/getTrackNumber", 
            APIEndpoint.TRACKING_INFO, 
            params={"orderId": order_id}
        )
    
    async def track_package(self, tracking_number: str, carrier: str) -> Dict[str, Any]:
        """跟踪包裹"""
        return await self._make_rate_limited_request(
            "GET",
            "/logistic/trackPackage",
            APIEndpoint.TRACKING_INFO,
            params={"trackingNumber": tracking_number, "carrier": carrier}
        )
    
    # 其他接口
    async def get_categories(self) -> Dict[str, Any]:
        """获取商品分类"""
        return await self._make_rate_limited_request(
            "GET", 
            "/product/getCategory", 
            APIEndpoint.CATEGORIES
        )
    
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
        return await self._make_rate_limited_request(
            "GET", 
            "/support/getCountry", 
            APIEndpoint.COUNTRIES
        )
    
    async def validate_address(self, address: CJShippingAddress) -> Dict[str, Any]:
        """验证收货地址"""
        return await self._make_rate_limited_request(
            "POST", 
            "/support/validateAddress", 
            APIEndpoint.ADDRESS_VALIDATE, 
            data=address.dict()
        )


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