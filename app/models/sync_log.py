"""
同步日志模型
"""
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    Text,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship
from app.config.database import Base


class SyncType(str, enum.Enum):
    """同步类型"""
    PRODUCT = "product"
    INVENTORY = "inventory"
    ORDER = "order"


class SyncStatus(str, enum.Enum):
    """同步状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SyncLog(Base):
    """同步日志模型"""
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # 关联外键
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False, index=True)

    sync_type = Column(Enum(SyncType), nullable=False)
    sync_status = Column(Enum(SyncStatus), nullable=False, default=SyncStatus.PENDING)
    
    source_id = Column(String(255), index=True)  # 例如 CJ 商品ID
    target_id = Column(String(255), index=True, nullable=True) # 例如 Magento Product ID
    
    message = Column(Text, nullable=True) # 日志信息或错误信息
    extra_data = Column(Text, nullable=True)  # 存储额外的JSON数据

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关系
    user = relationship("User")
    store = relationship("Store") 