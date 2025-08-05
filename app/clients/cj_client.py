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
from app.utils.request_manager import get_request_manager

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
        
        # 尝试从文件加载缓存的token
        self._load_cached_token()
        
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
            
            # 加载缓存的token
            self._load_cached_token()
            
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
    
    def _get_token_cache_file(self) -> str:
        """获取token缓存文件路径"""
        import os
        # 使用项目根目录下的cache文件夹
        project_root = os.getcwd()  # 使用当前工作目录作为项目根目录
        cache_dir = os.path.join(project_root, "cache")
        
        try:
            os.makedirs(cache_dir, exist_ok=True)
            logger.info("Cache directory created/verified", cache_dir=cache_dir)
        except Exception as e:
            logger.warning("Failed to create cache directory", error=str(e), cache_dir=cache_dir)
            # 如果创建失败，使用临时目录
            import tempfile
            cache_dir = tempfile.gettempdir()
            logger.info("Using temp directory for cache", temp_dir=cache_dir)
            
        return os.path.join(cache_dir, "cj_token.json")
    
    def _load_cached_token(self) -> None:
        """从文件加载缓存的token"""
        try:
            import json
            import os
            from datetime import timezone
            
            cache_file = self._get_token_cache_file()
            logger.info("Attempting to load cached token", cache_file=cache_file)
            
            if not os.path.exists(cache_file):
                logger.info("Cache file does not exist", cache_file=cache_file)
                return
            
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            logger.info("Loaded cache data", has_email=data.get("email") == self.email, 
                       has_expires=bool(data.get("expires_at")))
            
            # 检查token是否属于当前用户且仍然有效
            if data.get("email") == self.email and data.get("expires_at"):
                try:
                    expiry_dt = datetime.fromisoformat(data["expires_at"])
                    current_time = datetime.now(timezone.utc)
                    
                    logger.info("Token expiry check", 
                               expiry_time=expiry_dt.isoformat(),
                               current_time=current_time.isoformat(),
                               is_valid=current_time < expiry_dt)
                    
                    if current_time < expiry_dt:
                        self._access_token = data.get("access_token")
                        self._refresh_token = data.get("refresh_token")
                        self._token_expires_at = expiry_dt
                        logger.info("Successfully loaded cached CJ token", 
                                  expires_at=data["expires_at"],
                                  token_preview=self._access_token[:10] + "..." if self._access_token else None)
                    else:
                        logger.info("Cached CJ token has expired", 
                                  expiry_time=expiry_dt.isoformat(),
                                  current_time=current_time.isoformat())
                except Exception as e:
                    logger.warning("Failed to parse cached token expiry", error=str(e), expiry=data.get("expires_at"))
            else:
                logger.info("No valid cached token found", 
                           email_match=data.get("email") == self.email,
                           has_expires=bool(data.get("expires_at")))
                    
        except Exception as e:
            logger.warning("Failed to load cached token", error=str(e))
    
    def _save_cached_token(self) -> None:
        """保存token到缓存文件"""
        try:
            import json
            import os
            
            if not self._access_token or not self._token_expires_at:
                logger.warning("Cannot save token to cache - missing token or expiry")
                return
            
            cache_file = self._get_token_cache_file()
            data = {
                "access_token": self._access_token,
                "refresh_token": self._refresh_token,
                "expires_at": self._token_expires_at.isoformat(),
                "email": self.email  # 用于验证token是否属于当前用户
            }
            
            # 确保目录存在
            cache_dir = os.path.dirname(cache_file)
            os.makedirs(cache_dir, exist_ok=True)
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Successfully saved CJ token to cache", 
                       cache_file=cache_file,
                       expires_at=data["expires_at"],
                       token_preview=self._access_token[:10] + "..." if self._access_token else None)
            
        except Exception as e:
            logger.warning("Failed to save token to cache", error=str(e), cache_file=cache_file)
            

    
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
            
            # 检查token是否存在
            if not self._access_token:
                raise CJAPIError(
                    message="No access token available after authentication",
                    error_code="CJ_AUTH_ERROR",
                    details={"endpoint": endpoint}
                )
            
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
                message=f"Network error during CJ API request: {str(e)}",
                error_code="CJ_NETWORK_ERROR",
                details={"error": str(e), "endpoint": endpoint}
            )
        except httpx.HTTPStatusError as e:
            logger.error("CJ API HTTP error", status_code=e.response.status_code, response_text=e.response.text, endpoint=endpoint)
            raise CJAPIError(
                message=f"HTTP error during CJ API request: {e.response.status_code}",
                error_code="CJ_HTTP_ERROR",
                details={"status_code": e.response.status_code, "response": e.response.text, "endpoint": endpoint}
            )
        except CJAPIError:
            raise
        except Exception as e:
            logger.error("CJ API unexpected error", error=str(e), endpoint=endpoint)
            raise CJAPIError(
                message=f"Unexpected error during CJ API request: {str(e)}",
                error_code="CJ_UNEXPECTED_ERROR",
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
        # 确保已认证
        await self._ensure_authenticated()
        
        async def _make_api_request():
            # 检查token是否存在
            if not self._access_token:
                raise CJAPIError(
                    message="No access token available after authentication",
                    error_code="CJ_AUTH_ERROR",
                    details={"endpoint": endpoint}
                )
            
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
            if response.status_code == 401:
                # Token过期，等待一段时间后重新获取token
                logger.warning("CJ API token expired, waiting before refresh...")
                await asyncio.sleep(5)  # 等待5秒避免频率限制
                self._access_token = None
                self._token_expires_at = None
                await self._ensure_authenticated()
                # 重新发送请求
                return await _make_api_request()
            
            if response.status_code == 429:
                raise CJAPIError(
                    message="API调用频率超限：Free等级限制为1次/秒",
                    error_code="CJ_RATE_LIMIT_ERROR",
                    details={"status_code": response.status_code, "response": response.text}
                )
            elif response.status_code not in [200, 201]:
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
        
        try:
            # 使用请求管理器
            request_manager = get_request_manager()
            return await request_manager.make_request(
                _make_api_request,
                endpoint="general"
            )
            
        except Exception as e:
            raise
    
    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        
        async def _make_get_token_request():
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
                
                if response.status_code == 429:
                    raise CJAPIError(
                        message="getAccessToken接口频率限制：每5分钟只能调用1次",
                        error_code="CJ_RATE_LIMIT_ERROR",
                        details={"status_code": response.status_code, "response": response.text}
                    )
                elif response.status_code != 200:
                    raise CJAPIError(
                        message=f"Failed to get access token: {response.status_code}",
                        error_code="CJ_AUTH_ERROR",
                        details={"status_code": response.status_code, "response": response.text}
                    )
                
                result = response.json()
                logger.info("CJ API parsed response", result=result)
                
                return result
        
        try:
            # 使用请求管理器
            request_manager = get_request_manager()
            result = await request_manager.make_request(
                _make_get_token_request,
                endpoint="get_access_token"
            )
            
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
            
            # 保存到缓存
            self._save_cached_token()
            
            return access_token
                
        except httpx.RequestError as e:
            logger.error("Network error during getAccessToken", error=str(e))
            raise CJAPIError(
                message=f"Network error during getAccessToken: {str(e)}",
                error_code="CJ_NETWORK_ERROR",
                details={"error": str(e), "endpoint": "/authentication/getAccessToken"}
            )
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error during getAccessToken", status_code=e.response.status_code, response_text=e.response.text)
            raise CJAPIError(
                message=f"HTTP error during getAccessToken: {e.response.status_code}",
                error_code="CJ_HTTP_ERROR",
                details={"status_code": e.response.status_code, "response": e.response.text, "endpoint": "/authentication/getAccessToken"}
            )
        except Exception as e:
            logger.error("Unexpected error during getAccessToken", error=str(e))
            raise CJAPIError(
                message=f"Unexpected error during getAccessToken: {str(e)}",
                error_code="CJ_UNEXPECTED_ERROR",
                details={"error": str(e), "endpoint": "/authentication/getAccessToken"}
            )
    
    async def _refresh_access_token(self) -> str:
        """使用refresh token刷新access token"""
        if not self._refresh_token:
            raise CJAPIError(
                message="No refresh token available",
                error_code="CJ_AUTH_ERROR"
            )
        
        async def _make_refresh_token_request():
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
                
                if response.status_code != 200:
                    raise CJAPIError(
                        message=f"Failed to refresh access token: {response.status_code}",
                        error_code="CJ_AUTH_ERROR",
                        details={"status_code": response.status_code, "response": response.text}
                    )
                
                result = response.json()
                return result
        
        try:
            # 使用请求管理器
            request_manager = get_request_manager()
            result = await request_manager.make_request(
                _make_refresh_token_request,
                endpoint="refresh_token"
            )
            
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
            
            if not access_token:
                raise CJAPIError(
                    message="No access token in refresh response",
                    error_code="CJ_AUTH_ERROR",
                    details={"response": result}
                )
            
            # 更新token信息
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
                    from datetime import timezone
                    self._token_expires_at = datetime.now(timezone.utc) + timedelta(days=15)
            else:
                from datetime import timezone
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(days=15)
            
            logger.info("Successfully refreshed CJ access token", 
                      expires_at=self._token_expires_at.isoformat())
            
            # 保存到缓存
            self._save_cached_token()
            
            return access_token
                
        except httpx.RequestError as e:
            logger.error("Network error during refreshAccessToken", error=str(e))
            raise CJAPIError(
                message=f"Network error during refreshAccessToken: {str(e)}",
                error_code="CJ_NETWORK_ERROR",
                details={"error": str(e), "endpoint": "/authentication/refreshAccessToken"}
            )
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error during refreshAccessToken", status_code=e.response.status_code, response_text=e.response.text)
            raise CJAPIError(
                message=f"HTTP error during refreshAccessToken: {e.response.status_code}",
                error_code="CJ_HTTP_ERROR",
                details={"status_code": e.response.status_code, "response": e.response.text, "endpoint": "/authentication/refreshAccessToken"}
            )
        except Exception as e:
            logger.error("Unexpected error during refreshAccessToken", error=str(e))
            raise CJAPIError(
                message=f"Unexpected error during refreshAccessToken: {str(e)}",
                error_code="CJ_UNEXPECTED_ERROR",
                details={"error": str(e), "endpoint": "/authentication/refreshAccessToken"}
            )
    
    async def _ensure_authenticated(self) -> None:
        """确保已认证"""
        from datetime import timezone
        
        # 如果已有有效token，直接返回
        if self._access_token and self._token_expires_at and datetime.now(timezone.utc) < self._token_expires_at:
            logger.debug("Using existing valid token")
            return
        
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
        try:
            await self._get_access_token()
        except Exception as e:
            logger.error("Failed to get access token", error=str(e))
            # 不要在这里设置token为None，让错误继续传播
            raise
    
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
        await self._ensure_authenticated()
        
        async with self._client as client:
            response = await client.get(
                f"{self.base_url}/product/query",
                params={"pid": product_id},
                headers={
                    "CJ-Access-Token": self._access_token,  # 使用CJ API文档指定的header格式
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise CJAPIError(
                    message=f"获取产品详情失败: {response.status_code}",
                    error_code="CJ_PRODUCT_DETAIL_ERROR",
                    details={"status_code": response.status_code, "response": response.text}
                )
            
            result = response.json()
            if not result.get("result"):
                raise CJAPIError(
                    message="产品详情API返回错误",
                    error_code="CJ_PRODUCT_DETAIL_ERROR",
                    details={"response": result}
                )
            
            return result.get("data", {})
    
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