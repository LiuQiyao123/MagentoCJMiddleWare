"""
订单数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from decimal import Decimal

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, Index, Numeric, JSON
from sqlalchemy.sql import func

from app.models import Base


class SyncStatus(str, Enum):
    """同步状态枚举"""
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    PROCESSING = "processing"


class Order(Base):
    """订单表"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    magento_order_id = Column(String(255), nullable=True, index=True)
    cj_order_id = Column(String(255), nullable=True, index=True)
    order_number = Column(String(255), unique=True, nullable=False, index=True)
    customer_email = Column(String(255), nullable=True, index=True)
    customer_name = Column(String(255), nullable=True)
    order_status = Column(String(50), nullable=True)
    payment_status = Column(String(50), nullable=True)
    shipping_status = Column(String(50), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(10), nullable=True)
    shipping_address = Column(JSON, nullable=True)
    billing_address = Column(JSON, nullable=True)
    items = Column(JSON, nullable=True)
    shipping_method = Column(String(255), nullable=True)
    payment_method = Column(String(255), nullable=True)
    sync_status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING, index=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Order(order_number='{self.order_number}', customer_email='{self.customer_email}')>" 