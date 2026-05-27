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
from app.config.redis import redis_manager
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
            
            # 初始化 Redis (如果尚未初始化)
            if not redis_manager._initialized:
                try:
                    await redis_manager.initialize()
                except Exception as e:
                    logger.warning(f"Redis initialization failed in CJClient: {e}")

            logger.info("CJ API client initialized successfully (Lazy Auth)")
            
        except Exception as e:
            error_details = {"error": str(e)}
            if isinstance(e, APIException):
                error_details["original_details"] = e.details
                
            logger.error("Failed to initialize CJ API client", extra=error_details)
            raise CJAPIError(
                error_code="CJ_INIT_ERROR",
                message="Failed to initialize CJ API client",
                details=error_details
            )
    
    async def close(self) -> None:
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
            
    async def _authenticate(self) -> None:
        """认证获取访问令牌 (仅在无有效Token时调用)"""
        try:
            # 构造认证请求
            auth_data = {
                "email": self.email,
                "password": self.password
            }
            
            logger.info("Requesting new Access Token from CJ API")
            
            # 发送认证请求
            response = await self._client.post(
                f"{self.base_url}/authentication/getAccessToken",
                json=auth_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error("CJ Auth Failed", extra={"status": response.status_code, "body": response.text})
                raise CJAPIError(
                    error_code="CJ_AUTH_ERROR",
                    message="Failed to authenticate with CJ API",
                    details={"status_code": response.status_code, "response": response.text}
                )
            
            result = response.json()
            
            if not result.get("result"):
                logger.error("CJ Auth Logic Failed", extra={"response": result})
                raise CJAPIError(
                    error_code="CJ_AUTH_ERROR",
                    message="Authentication failed",
                    details={"response": result}
                )
            
            data = result.get("data", {})
            self._access_token = data["accessToken"]
            refresh_token = data["refreshToken"]
            
            # 有效期: AccessToken 15天, RefreshToken 180天
            # 减去 300秒 (5分钟) 作为安全缓冲
            access_ttl = (15 * 24 * 3600) - 300
            refresh_ttl = (180 * 24 * 3600) - 300
            
            self._token_expires_at = datetime.now() + timedelta(seconds=access_ttl)
            
            # 保存到 Redis
            try:
                await redis_manager.set("cj_api:access_token", self._access_token, expire=access_ttl)
                await redis_manager.set("cj_api:refresh_token", refresh_token, expire=refresh_ttl)
                logger.info("Cached CJ tokens to Redis")
            except Exception as e:
                logger.warning(f"Failed to cache tokens to Redis: {e}")
            
            logger.info("CJ API authentication successful")
            
        except httpx.RequestError as e:
            logger.error("CJ API authentication network error", extra={"error": str(e)})
            raise CJAPIError(
                error_code="CJ_NETWORK_ERROR",
                message="Network error during authentication",
                details={"error": str(e)}
            )
        except Exception as e:
            logger.error("CJ API authentication error", extra={"error": str(e)})
            raise

    async def _refresh_token(self, refresh_token: str) -> None:
        """使用 Refresh Token 刷新 Access Token"""
        try:
            logger.info("Refreshing Access Token using Refresh Token")
            
            response = await self._client.post(
                f"{self.base_url}/authentication/refreshAccessToken",
                json={"refreshToken": refresh_token},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.warning("Refresh Token request failed", extra={"status": response.status_code})
                raise CJAPIError("Refresh request failed") # 触发重新登录
                
            result = response.json()
            if not result.get("result"):
                logger.warning("Refresh Token API returned false", extra={"response": result})
                raise CJAPIError("Refresh API returned false") # 触发重新登录
                
            data = result.get("data", {})
            self._access_token = data["accessToken"]
            new_refresh_token = data.get("refreshToken", refresh_token) # 有些接口可能不返回新的refresh token
            
            # 更新有效期
            access_ttl = (15 * 24 * 3600) - 300
            refresh_ttl = (180 * 24 * 3600) - 300 # 假设刷新也会重置 refresh token 有效期，或者保持原样
            
            self._token_expires_at = datetime.now() + timedelta(seconds=access_ttl)
            
            # 更新 Redis
            try:
                await redis_manager.set("cj_api:access_token", self._access_token, expire=access_ttl)
                await redis_manager.set("cj_api:refresh_token", new_refresh_token, expire=refresh_ttl)
                logger.info("Refreshed and cached CJ tokens")
            except Exception as e:
                logger.warning(f"Failed to cache refreshed tokens: {e}")
                
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise # 让上层捕获并执行 _authenticate

    async def _ensure_authenticated(self) -> None:
        """确保认证状态有效 (惰性认证核心逻辑)"""
        # 1. 内存检查
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return

        # 2. Redis Access Token 检查
        try:
            token = await redis_manager.get("cj_api:access_token")
            if token:
                client = await redis_manager.get_client()
                ttl = await client.ttl("cj_api:access_token")
                if ttl > 300: # 有效期 > 5分钟
                    self._access_token = token
                    self._token_expires_at = datetime.now() + timedelta(seconds=ttl)
                    logger.debug("Restored Access Token from Redis")
                    return
        except Exception as e:
            logger.warning(f"Redis Access Token check failed: {e}")

        # 3. Redis Refresh Token 检查 & 刷新
        try:
            refresh_token = await redis_manager.get("cj_api:refresh_token")
            if refresh_token:
                client = await redis_manager.get_client()
                ttl = await client.ttl("cj_api:refresh_token")
                if ttl > 300:
                    try:
                        await self._refresh_token(refresh_token)
                        return # 刷新成功，直接返回
                    except Exception as refresh_error:
                        logger.warning(f"Refresh failed, falling back to login: {refresh_error}")
        except Exception as e:
            logger.warning(f"Redis Refresh Token check failed: {e}")

        # 4. 最终手段：重新登录
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
            
            logger.error("CJ API network error", extra={"error": str(e), "endpoint": endpoint})
            raise CJAPIError(
                error_code="CJ_NETWORK_ERROR",
                message="Network error during CJ API request",
                details={"error": str(e), "endpoint": endpoint}
            )
        except CJAPIError:
            raise
        except Exception as e:
            logger.error("CJ API request error", extra={"error": str(e), "endpoint": endpoint})
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
            logger.error("Failed to get popular categories", extra={"error": str(e)})
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
            logger.error(f"Failed to get products for category {category_id}", extra={"error": str(e)})
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