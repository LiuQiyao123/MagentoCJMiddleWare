"""
Token存储模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.sql import func

from app.config.database import Base


class TokenStorage(Base):
    """Token存储表"""
    __tablename__ = "token_storage"
    
    # 主键
    id = Column(String(36), primary_key=True, index=True)
    
    # 提供商（如：cj, magento等）
    provider = Column(String(50), nullable=False, index=True)
    
    # Token数据（JSON格式）
    token_data = Column(Text, nullable=False)
    
    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 更新时间
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_provider_created', 'provider', 'created_at'),
        Index('idx_provider_updated', 'provider', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<TokenStorage(provider='{self.provider}', created_at='{self.created_at}')>" 