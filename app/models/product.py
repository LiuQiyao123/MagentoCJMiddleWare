"""
产品映射数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, Index
from sqlalchemy.sql import func

from app.config.database import Base


class SyncStatus(str, Enum):
    """同步状态枚举"""
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


class ProductMapping(Base):
    """产品映射表"""
    __tablename__ = "product_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    magento_product_id = Column(String(255), unique=True, nullable=False, index=True)
    magento_sku = Column(String(255), unique=True, nullable=False, index=True)
    cj_product_id = Column(String(255), nullable=False)
    cj_variant_id = Column(String(255), nullable=True)
    sync_status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING, index=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 添加索引
    __table_args__ = (
        Index('idx_sync_status', 'sync_status'),
        Index('idx_last_sync', 'last_sync_at'),
    )
    
    def __repr__(self):
        return f"<ProductMapping(magento_sku='{self.magento_sku}', cj_product_id='{self.cj_product_id}')>" 