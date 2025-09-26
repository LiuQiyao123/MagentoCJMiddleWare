"""
API v1 路由初始化
"""
from fastapi import APIRouter

# 新增 categories
from app.api.v1 import products, orders, monitor, categories

api_router = APIRouter()

# 注册路由
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(monitor.router, tags=["monitor"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"]) 