#!/bin/bash

# 项目部署脚本
set -e

echo "🚀 开始部署Magento-CJ中间件..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker服务"
    echo "运行: sudo service docker start"
    exit 1
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo "❌ 未找到.env文件，请先配置环境变量"
    echo "请复制.env.example为.env并填入正确的配置"
    exit 1
fi

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p logs
mkdir -p docker/mysql/init.sql

# 构建Docker镜像
echo "🔨 构建Docker镜像..."
docker-compose build

# 启动数据库和Redis
echo "🗄️ 启动数据库服务..."
docker-compose up -d mysql redis

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 30

# 运行数据库迁移
echo "🔄 运行数据库迁移..."
docker-compose run --rm middleware python -c "
from app.config.database import engine
from app.models import order, product
import asyncio

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(order.Base.metadata.create_all)
        await conn.run_sync(product.Base.metadata.create_all)
    print('数据库表创建完成')

asyncio.run(init_db())
"

# 启动所有服务
echo "🚀 启动所有服务..."
docker-compose up -d

# 检查服务状态
echo "📊 检查服务状态..."
sleep 10
docker-compose ps

echo "✅ 部署完成！"
echo "🌐 访问地址:"
echo "   - 主服务: http://localhost:3000"
echo "   - API文档: http://localhost:3000/docs"
echo "   - Celery监控: http://localhost:5555"
echo ""
echo "📝 常用命令:"
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart" 