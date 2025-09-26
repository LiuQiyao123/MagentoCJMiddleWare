"""
应用配置管理
"""
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""
    # 应用信息
    APP_NAME: str = "CJ Magento Middleware"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_KEY: str  # 新增: 用于保护API的静态密钥

    # 加密密钥
    SECRET_KEY: str

    # 数据库配置
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str = Field(default="magento_cj_middleware", description="数据库名称")
    DB_USER: str = Field(default="root", description="数据库用户")
    DB_PASSWORD: str = Field(description="数据库密码")
    DB_CHARSET: str = Field(default="utf8mb4", description="数据库字符集")
    DB_POOL_SIZE: int = Field(default=10, description="数据库连接池大小")
    DB_MAX_OVERFLOW: int = Field(default=20, description="数据库连接池最大溢出")
    
    # Redis配置
    REDIS_HOST: str = Field(default="localhost", description="Redis主机")
    REDIS_PORT: int = Field(default=6379, description="Redis端口")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    REDIS_DB: int = Field(default=0, description="Redis数据库")
    REDIS_MAX_CONNECTIONS: int = Field(default=100, description="Redis最大连接数")
    
    # 队列配置
    QUEUE_REDIS_HOST: str = Field(default="localhost", description="队列Redis主机")
    QUEUE_REDIS_PORT: int = Field(default=6379, description="队列Redis端口")
    QUEUE_REDIS_DB: int = Field(default=1, description="队列Redis数据库")
    QUEUE_REDIS_PASSWORD: Optional[str] = Field(default=None, description="队列Redis密码")
    
    # Magento配置
    MAGENTO_BASE_URL: str = Field(description="Magento基础URL")
    MAGENTO_CONSUMER_KEY: str = Field(description="Magento Consumer Key")
    MAGENTO_CONSUMER_SECRET: str = Field(description="Magento Consumer Secret")
    MAGENTO_ACCESS_TOKEN: str = Field(description="Magento Access Token")
    MAGENTO_ACCESS_TOKEN_SECRET: str = Field(description="Magento Access Token Secret")
    MAGENTO_TIMEOUT: int = Field(default=30, description="Magento API超时时间")
    MAGENTO_MAX_RETRIES: int = Field(default=3, description="Magento API最大重试次数")
    MAGENTO_ADMIN_USERNAME: Optional[str] = Field(default=None, description="用于自动刷新Token的管理员用户名")
    MAGENTO_ADMIN_PASSWORD: Optional[str] = Field(default=None, description="用于自动刷新Token的管理员密码")
    MAGENTO_STORE_CODE: str = Field(default="default", description="REST调用使用的Store View代码")
    MAGENTO_WEBSITE_IDS: List[int] = Field(default=[1], description="创建商品时分配的Website ID 列表，以逗号分隔")
    MAGENTO_ADMIN_PATH: str = Field(default="admin", description="Magento 后台路径，如 admin_wim6xs1")
    
    # CJ Dropshipping配置
    CJ_API_BASE_URL: str = Field(
        default="https://developers.cjdropshipping.com/api2.0/v1",
        description="CJ API基础URL"
    )
    CJ_API_EMAIL: str = Field(description="CJ API邮箱")
    CJ_API_KEY: str = Field(description="CJ API Key")
    CJ_TIMEOUT: int = Field(default=30, description="CJ API超时时间")
    CJ_MAX_RETRIES: int = Field(default=3, description="CJ API最大重试次数")
    
    # 同步配置
    SYNC_INTERVAL_MINUTES: int = Field(default=30, description="同步间隔（分钟）")
    BATCH_SIZE: int = Field(default=100, description="批处理大小")
    MAX_RETRY_ATTEMPTS: int = Field(default=3, description="最大重试次数")
    RETRY_DELAY: int = Field(default=5000, description="重试延迟（毫秒）")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="logs/app.log", description="日志文件路径")
    LOG_MAX_SIZE: int = Field(default=10, description="日志文件最大大小（MB）")
    LOG_BACKUP_COUNT: int = Field(default=5, description="日志备份数量")
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, description="启用监控指标")
    METRICS_PORT: int = Field(default=9090, description="监控端口")
    
    # SSL配置
    VERIFY_SSL: bool = Field(default=True, description="是否验证SSL证书")
    SSL_CERT_PATH: Optional[str] = Field(default=None, description="SSL证书路径")
    
    # Celery配置
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery Broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", description="Celery Result Backend URL")
    
    # CORS和安全配置
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"], description="允许的源")
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"], description="允许的主机")
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )
    
    @property
    def database_url_sync(self) -> str:
        """获取同步数据库连接URL"""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )
    
    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def queue_redis_url(self) -> str:
        """获取队列Redis连接URL"""
        auth = f":{self.QUEUE_REDIS_PASSWORD}@" if self.QUEUE_REDIS_PASSWORD else ""
        return f"redis://{auth}{self.QUEUE_REDIS_HOST}:{self.QUEUE_REDIS_PORT}/{self.QUEUE_REDIS_DB}"
    
    def create_log_directory(self) -> None:
        """创建日志目录"""
        log_dir = os.path.dirname(self.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings() 