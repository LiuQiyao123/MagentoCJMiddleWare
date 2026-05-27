"""
自定义异常处理模块
定义API异常类和错误处理机制
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class APIException(Exception):
    """API异常基类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = timestamp or datetime.now()
        
        # 记录异常日志
        logger.error(
            "API Exception raised",
            extra={
                "error_code": error_code,
                "error_message": message,  # Renamed from message to avoid KeyError
                "status_code": status_code,
                "details": details
            }
        )


class ValidationError(APIException):
    """数据验证错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class AuthenticationError(APIException):
    """认证错误"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class AuthorizationError(APIException):
    """授权错误"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )


class NotFoundError(APIException):
    """资源未找到错误"""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details=details
        )


class ConflictError(APIException):
    """资源冲突错误"""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
            details=details
        )


class RateLimitError(APIException):
    """速率限制错误"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )


class ExternalServiceError(APIException):
    """外部服务错误"""
    
    def __init__(self, message: str, service: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service, **(details or {})}
        )


class DatabaseError(APIException):
    """数据库错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details
        )


class ConfigurationError(APIException):
    """配置错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details
        )


# 预定义的错误代码
ERROR_CODES = {
    "VALIDATION_ERROR": "数据验证失败",
    "AUTHENTICATION_ERROR": "认证失败",
    "AUTHORIZATION_ERROR": "权限不足",
    "NOT_FOUND": "资源未找到",
    "CONFLICT": "资源冲突",
    "RATE_LIMIT_EXCEEDED": "请求频率超限",
    "EXTERNAL_SERVICE_ERROR": "外部服务错误",
    "DATABASE_ERROR": "数据库错误",
    "CONFIGURATION_ERROR": "配置错误",
    "INTERNAL_ERROR": "内部服务器错误",
}


def get_error_message(error_code: str) -> str:
    """获取错误代码对应的中文描述"""
    return ERROR_CODES.get(error_code, "未知错误")


def create_error_response(
    error_code: str,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> Dict[str, Any]:
    """创建标准错误响应"""
    return {
        "success": False,
        "error_code": error_code,
        "message": message or get_error_message(error_code),
        "details": details or {},
        "timestamp": datetime.now().isoformat(),
        "status_code": status_code
    } 