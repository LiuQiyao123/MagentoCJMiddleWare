"""
产品数据模型
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


class Product(Base):
    """产品表"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    magento_id = Column(String(255), nullable=True, index=True)
    cj_product_id = Column(String(255), nullable=True, index=True)
    sku = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    cost_price = Column(Numeric(10, 2), nullable=True)
    stock_quantity = Column(Integer, nullable=True)
    status = Column(String(50), nullable=True)
    category = Column(String(255), nullable=True)
    brand = Column(String(255), nullable=True)
    weight = Column(Numeric(8, 3), nullable=True)
    dimensions = Column(JSON, nullable=True)
    images = Column(JSON, nullable=True)
    attributes = Column(JSON, nullable=True)
    sync_status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING, index=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(sku='{self.sku}', name='{self.name}')>" 