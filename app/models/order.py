"""
订单映射数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, JSON, Index, Float
from sqlalchemy.sql import func

from app.config.database import Base


class OrderStatus(str, Enum):
    """订单状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class OrderMapping(Base):
    """订单映射表"""
    __tablename__ = "order_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    magento_order_id = Column(String(50), nullable=False, unique=True, index=True)
    magento_order_increment_id = Column(String(50), nullable=False, index=True)
    cj_order_id = Column(String(50), nullable=False, index=True)
    order_status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True)
    
    # 订单金额信息
    total_amount = Column(Float, nullable=True)
    currency = Column(String(3), nullable=True, default="USD")
    
    # 物流信息
    tracking_number = Column(String(100), nullable=True, index=True)
    shipping_method = Column(String(100), nullable=True)
    
    # 同步信息
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_sync_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # 额外信息
    notes = Column(Text, nullable=True)
    order_metadata = Column(JSON, nullable=True)
    
    # 添加索引
    __table_args__ = (
        Index('idx_magento_order_id', 'magento_order_id'),
        Index('idx_cj_order_id', 'cj_order_id'),
        Index('idx_order_status', 'order_status'),
        Index('idx_tracking_number', 'tracking_number'),
        Index('idx_last_sync_at', 'last_sync_at'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<OrderMapping(magento_order='{self.magento_order_increment_id}', cj_order='{self.cj_order_id}', status='{self.order_status}')>" 