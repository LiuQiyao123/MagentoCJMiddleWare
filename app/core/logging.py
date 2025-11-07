"""
日志配置模块
设置结构化日志记录和日志格式
"""

import logging
import logging.config
import sys
from typing import Dict, Any

import structlog
from structlog.stdlib import LoggerFactory

from app.config.settings import get_settings

settings = get_settings()


def setup_logging() -> None:
    """设置日志配置"""
    
    # 配置structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 配置标准库日志
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "structlog.stdlib.ProcessorFormatter",
                "processor": structlog.processors.JSONRenderer(),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "formatter": "json" if settings.DEBUG else "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/app.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": "logs/error.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console", "file", "error_file"],
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "propagate": False,
            },
            "app": {
                "handlers": ["console", "file", "error_file"],
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
            "redis": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
            "httpx": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
            "requests": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }
    
    # 应用日志配置
    logging.config.dictConfig(logging_config)
    
    # 设置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # 创建日志目录
    import os
    os.makedirs("logs", exist_ok=True)
    
    # 记录启动日志
    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging system initialized",
        debug_mode=settings.DEBUG,
        log_level="DEBUG" if settings.DEBUG else "INFO"
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)


def log_request(request_data: Dict[str, Any]) -> None:
    """记录请求日志"""
    logger = get_logger("request")
    logger.info("HTTP Request", **request_data)


def log_response(response_data: Dict[str, Any]) -> None:
    """记录响应日志"""
    logger = get_logger("response")
    logger.info("HTTP Response", **response_data)


def log_error(error_data: Dict[str, Any]) -> None:
    """记录错误日志"""
    logger = get_logger("error")
    logger.error("Application Error", **error_data)


def log_performance(performance_data: Dict[str, Any]) -> None:
    """记录性能日志"""
    logger = get_logger("performance")
    logger.info("Performance Metric", **performance_data) 