"""
店铺（租户）模型
"""
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Enum,
    ForeignKey,
    func,
    Text
)
from sqlalchemy.orm import relationship
from app.config.database import Base


class StorePlatform(enum.Enum):
    """店铺平台枚举"""
    MAGENTO = "magento"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"


class Store(Base):
    """店铺（租户）模型"""
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    platform = Column(Enum(StorePlatform), nullable=False)
    
    api_url = Column(String(255), nullable=False)
    
    # 存储加密后的API凭证
    encrypted_consumer_key = Column(Text)
    encrypted_consumer_secret = Column(Text)
    encrypted_access_token = Column(Text)
    encrypted_access_token_secret = Column(Text)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    user = relationship("User", back_populates="stores") 