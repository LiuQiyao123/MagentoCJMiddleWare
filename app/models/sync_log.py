"""同步日志模型"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, Enum as SAEnum
from . import Base


class SyncType(str, enum.Enum):
    """同步类型"""
    PRODUCT = "product"
    ORDER = "order"


class SyncStatus(str, enum.Enum):
    """同步状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncLog(Base):
    """同步操作日志"""
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_type = Column(SAEnum(SyncType), nullable=False, comment="同步类型")
    status = Column(SAEnum(SyncStatus), nullable=False, default=SyncStatus.PENDING, comment="状态")
    message = Column(String(500), nullable=True, comment="摘要信息")
    details = Column(JSON, nullable=True, comment="详细数据")
    
    # 商品同步专用
    product_id = Column(String(100), nullable=True, comment="CJ 商品ID")
    product_url = Column(String(1000), nullable=True, comment="商品链接")
    success = Column(Boolean, nullable=True, comment="是否成功")
    magento_id = Column(Integer, nullable=True, comment="Magento 商品ID")
    error_message = Column(String(2000), nullable=True, comment="错误信息")

    # 订单同步专用
    order_id = Column(String(100), nullable=True, comment="订单ID")

    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
