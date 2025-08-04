#!/bin/bash

# Magento-CJ 中间件启动脚本

echo "🚀 启动 Magento-CJ 中间件..."

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "❌ 错误: .env 文件不存在"
    echo "请先复制 .env.example 为 .env 并配置您的API密钥"
    exit 1
fi

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ 错误: Docker 未运行"
    echo "请先启动 Docker"
    exit 1
fi

# 构建并启动服务
echo "📦 构建 Docker 镜像..."
docker-compose build

echo "🔄 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 测试API连接
echo "🧪 测试API连接..."

# 测试中间件健康状态
echo "测试中间件健康状态..."
curl -s http://localhost:3000/health || echo "❌ 中间件未响应"

# 测试Magento连接
echo "测试Magento连接..."
curl -s http://localhost:3000/api/v1/health/magento || echo "❌ Magento连接失败"

# 测试CJ连接
echo "测试CJ连接..."
curl -s http://localhost:3000/api/v1/health/cj || echo "❌ CJ连接失败"

echo ""
echo "✅ 启动完成！"
echo "📊 监控面板: http://localhost:5555 (Celery监控)"
echo "📚 API文档: http://localhost:3000/docs"
echo "🔧 管理界面: http://localhost:3000/admin"

echo ""
echo "📝 常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps" 