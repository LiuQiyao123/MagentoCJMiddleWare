"""
数据模型包
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

# 创建基础模型类
class Base(DeclarativeBase):
    pass

# 导入所有模型
from .product import Product
from .order import Order
from .sync_log import SyncLog

__all__ = ["Base", "Product", "Order", "SyncLog"] 