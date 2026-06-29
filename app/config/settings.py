"""
应用配置管理
"""
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # 应用基础配置
    APP_NAME: str = Field(default="Magento-CJ-Middleware", description="应用名称")
    APP_VERSION: str = Field(default="1.2.0", description="应用版本")
    DEBUG: bool = Field(default=False, description="调试模式")
    HOST: str = Field(default="0.0.0.0", description="服务器地址")
    PORT: int = Field(default=3000, description="服务器端口")
    
    # 安全配置
    SECRET_KEY: str = Field(description="应用密钥")
    JWT_SECRET: str = Field(description="JWT密钥")
    JWT_EXPIRES_IN: str = Field(default="24h", description="JWT过期时间")
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost", "http://127.0.0.1"],
        description="允许的跨域源"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="允许的主机"
    )
    
    # 数据库配置
    DB_HOST: str = Field(default="localhost", description="数据库主机")
    DB_PORT: int = Field(default=3306, description="数据库端口")
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
    MAGENTO_API_TOKEN: str = Field(description="Magento API Token")
    MAGENTO_API_USER: str = Field(description="Magento API用户")
    MAGENTO_API_PASSWORD: str = Field(description="Magento API密码")
    MAGENTO_TIMEOUT: int = Field(default=30, description="Magento API超时时间")
    
    # Magento 数据库配置（用于属性管理器直连 EAV 表）
    MAGENTO_DB_HOST: str = Field(default="host.docker.internal", description="Magento数据库主机")
    MAGENTO_DB_PORT: int = Field(default=33061, description="Magento数据库端口")
    MAGENTO_DB_NAME: str = Field(default="magento", description="Magento数据库名称")
    MAGENTO_DB_USER: str = Field(default="magento", description="Magento数据库用户")
    MAGENTO_DB_PASSWORD: str = Field(default="magento", description="Magento数据库密码")
    MAGENTO_MAX_RETRIES: int = Field(default=3, description="Magento API最大重试次数")
    
    # 兼容旧配置
    MAGENTO_CONSUMER_KEY: Optional[str] = Field(default=None, description="Magento Consumer Key (兼容)")
    MAGENTO_CONSUMER_SECRET: Optional[str] = Field(default=None, description="Magento Consumer Secret (兼容)")
    MAGENTO_ACCESS_TOKEN: Optional[str] = Field(default=None, description="Magento Access Token (兼容)")
    MAGENTO_ACCESS_TOKEN_SECRET: Optional[str] = Field(default=None, description="Magento Access Token Secret (兼容)")
    
    # CJ Dropshipping配置
    CJ_API_BASE_URL: str = Field(
        default="https://developers.cjdropshipping.com/api2.0/v1",
        description="CJ API基础URL"
    )
    CJ_API_EMAIL: str = Field(description="CJ API邮箱")
    CJ_API_PASSWORD: str = Field(description="CJ API密码（API Key）")
    CJ_TIMEOUT: int = Field(default=30, description="CJ API超时时间")
    CJ_MAX_RETRIES: int = Field(default=3, description="CJ API最大重试次数")
    
    # 兼容旧配置
    CJ_API_KEY: Optional[str] = Field(default=None, description="CJ API Key (兼容)")
    CJ_API_SECRET: Optional[str] = Field(default=None, description="CJ API Secret (兼容)")
    
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
    
    # Celery配置
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery Broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", description="Celery Result Backend URL")
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """解析CORS配置"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """解析允许的主机"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @property
    def DATABASE_URL(self) -> str:
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