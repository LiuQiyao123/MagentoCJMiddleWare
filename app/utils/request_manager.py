"""
CJ API请求管理器
统一管理API调用频率、错误处理和重试逻辑
"""
import asyncio
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

import structlog
from app.core.exceptions import APIException

logger = structlog.get_logger(__name__)


class CJErrorCode(Enum):
    """CJ错误码枚举"""
    SUCCESS = 200
    SYSTEM_BUSY = 1600000
    NO_PERMISSION = 1600001
    MUST_CARRY_TOKEN = 1600002
    REFRESH_TOKEN_INVALID = 1600003
    CALL_EXCEEDED_LIMIT = 1600200
    EXCEEDED_DEFAULT_LIMIT = 1600201


class CJRequestManager:
    """CJ API请求管理器"""
    
    def __init__(self):
        # Free等级限制：1次/秒
        self.max_requests_per_second = 1
        self.request_timestamps = []
        
        # 特殊接口限制
        self.get_access_token_interval = 300  # 5分钟
        self.refresh_token_interval = 60      # 1分钟
        self.last_get_token_time = 0
        self.last_refresh_token_time = 0
        
        # 重试配置
        self.max_retries = 3
        self.retry_delays = [1, 2, 5]  # 重试延迟（秒）
    
    def _cleanup_old_timestamps(self):
        """清理过期的请求时间戳"""
        current_time = time.time()
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 1.0
        ]
    
    async def _wait_for_rate_limit(self, endpoint: str = "general"):
        """等待频率限制"""
        self._cleanup_old_timestamps()
        
        # 通用频率限制检查（1次/秒）
        if len(self.request_timestamps) >= self.max_requests_per_second:
            wait_time = 1.0 - (time.time() - self.request_timestamps[0])
            if wait_time > 0:
                logger.info(f"Rate limit hit for {endpoint}, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        # 特殊接口检查
        current_time = time.time()
        
        if endpoint == "get_access_token":
            if current_time - self.last_get_token_time < self.get_access_token_interval:
                wait_time = self.get_access_token_interval - (current_time - self.last_get_token_time)
                logger.info(f"getAccessToken limit hit, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        elif endpoint == "refresh_token":
            if current_time - self.last_refresh_token_time < self.refresh_token_interval:
                wait_time = self.refresh_token_interval - (current_time - self.last_refresh_token_time)
                logger.info(f"refreshToken limit hit, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
    
    def _record_request_time(self, endpoint: str = "general"):
        """记录请求时间"""
        current_time = time.time()
        
        # 记录通用请求时间
        self.request_timestamps.append(current_time)
        
        # 记录特殊接口时间
        if endpoint == "get_access_token":
            self.last_get_token_time = current_time
        elif endpoint == "refresh_token":
            self.last_refresh_token_time = current_time
    
    def _parse_cj_error(self, response_data: Dict[str, Any]) -> Optional[str]:
        """解析CJ错误码"""
        if not response_data:
            return "Empty response"
        
        code = response_data.get("code")
        if code is None:
            return "No error code in response"
        
        if code == CJErrorCode.SUCCESS.value:
            return None
        
        # 根据错误码返回具体错误信息
        error_messages = {
            CJErrorCode.SYSTEM_BUSY.value: "系统繁忙，请稍后重试",
            CJErrorCode.NO_PERMISSION.value: "Token无效，需要重新认证",
            CJErrorCode.MUST_CARRY_TOKEN.value: "缺少Token，需要认证",
            CJErrorCode.REFRESH_TOKEN_INVALID.value: "Refresh Token失效，需要重新获取Token",
            CJErrorCode.CALL_EXCEEDED_LIMIT.value: "调用频率超限，请降低请求频率",
            CJErrorCode.EXCEEDED_DEFAULT_LIMIT.value: "超过默认限额，请检查用户等级",
        }
        
        return error_messages.get(code, f"未知错误码: {code}")
    
    async def make_request(
        self,
        request_func: Callable,
        endpoint: str = "general",
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """执行API请求"""
        
        for attempt in range(self.max_retries + 1):
            try:
                # 等待频率限制
                await self._wait_for_rate_limit(endpoint)
                
                # 执行请求
                logger.info(f"Making request to {endpoint}, attempt {attempt + 1}")
                response = await request_func(*args, **kwargs)
                
                # 检查CJ错误码
                if isinstance(response, dict):
                    cj_error = self._parse_cj_error(response)
                    if cj_error:
                        logger.error(f"CJ API error: {cj_error}", 
                                   endpoint=endpoint, 
                                   response=response)
                        raise APIException(
                            message=cj_error,
                            error_code="CJ_API_ERROR",
                            details={"response": response, "endpoint": endpoint}
                        )
                
                # 记录请求时间（只在成功时记录）
                self._record_request_time(endpoint)
                
                logger.info(f"Request successful for {endpoint}")
                return response
                
            except APIException as e:
                # 如果是CJ API错误，检查是否需要重试
                if e.error_code == "CJ_API_ERROR":
                    error_details = e.details.get("response", {})
                    code = error_details.get("code")
                    
                    # 系统繁忙可以重试
                    if code == CJErrorCode.SYSTEM_BUSY.value and attempt < self.max_retries:
                        delay = self.retry_delays[attempt]
                        logger.warning(f"System busy, retrying in {delay}s", 
                                     attempt=attempt + 1, endpoint=endpoint)
                        await asyncio.sleep(delay)
                        continue
                    
                    # 其他错误不重试
                    raise
                
                # 频率限制错误 - 不重试，直接抛出
                elif e.error_code == "CJ_RATE_LIMIT_ERROR":
                    logger.error(f"Rate limit error: {e.message}", endpoint=endpoint)
                    raise
                
                # 网络错误可以重试
                elif "network" in e.error_code.lower() and attempt < self.max_retries:
                    delay = self.retry_delays[attempt]
                    logger.warning(f"Network error, retrying in {delay}s", 
                                 attempt=attempt + 1, endpoint=endpoint)
                    await asyncio.sleep(delay)
                    continue
                
                else:
                    raise
            
            except Exception as e:
                if attempt < self.max_retries:
                    delay = self.retry_delays[attempt]
                    logger.warning(f"Unexpected error, retrying in {delay}s", 
                                 error=str(e), attempt=attempt + 1, endpoint=endpoint)
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Request failed after {self.max_retries + 1} attempts", 
                               error=str(e), endpoint=endpoint)
                    raise APIException(
                        message=f"Request failed: {str(e)}",
                        error_code="REQUEST_FAILED",
                        details={"error": str(e), "endpoint": endpoint}
                    )
        
        # 不应该到达这里
        raise APIException(
            message="Request failed after all retries",
            error_code="REQUEST_FAILED",
            details={"endpoint": endpoint}
        )


# 全局请求管理器实例
_request_manager: Optional[CJRequestManager] = None


def get_request_manager() -> CJRequestManager:
    """获取请求管理器实例"""
    global _request_manager
    if _request_manager is None:
        _request_manager = CJRequestManager()
    return _request_manager 