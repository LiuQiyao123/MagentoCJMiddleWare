#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.database import db_manager
from app.models import order, product


async def init_db():
    """初始化数据库表"""
    try:
        # 初始化数据库管理器
        await db_manager.initialize()
        print("✅ 数据库连接初始化完成")
        
        # 创建订单相关表
        async with db_manager.async_engine.begin() as conn:
            await conn.run_sync(order.Base.metadata.create_all)
            print("✅ 订单表创建完成")
            
            # 创建产品相关表
            await conn.run_sync(product.Base.metadata.create_all)
            print("✅ 产品表创建完成")
            
        print("🎉 数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_db()) 