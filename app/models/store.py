"""
加盟店数据模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.sql import func

from app.config.database import Base


class Store(Base):
    """加盟店表：保存每个店铺的 Magento 与供应商凭证"""
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    # Magento 凭证与店铺信息
    magento_base_url = Column(String(255), nullable=False)
    magento_access_token = Column(String(255), nullable=False)
    magento_store_code = Column(String(50), nullable=True)

    # 供应商类型，例如 cj / aliexpress 等
    supplier_type = Column(String(50), nullable=False, default="cj")
    supplier_credentials = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_supplier_type", "supplier_type"),
    )

    def __repr__(self):
        return f"<Store id={self.id} name={self.name} supplier={self.supplier_type}>" 