#!/bin/bash

# Magento-CJ中台服务 WSL部署脚本
# 作者: AI Assistant
# 版本: 1.0.0

set -e  # 遇到错误立即退出

echo "🚀 开始部署 Magento-CJ 中台服务到 WSL..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查WSL环境
check_wsl_environment() {
    log_info "检查WSL环境..."
    
    # 检查是否为WSL
    if ! grep -q Microsoft /proc/version 2>/dev/null; then
        log_warning "未检测到WSL环境，但继续执行..."
    fi
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查Docker服务状态
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi
    
    log_success "WSL环境检查完成"
}

# 创建环境配置文件
create_env_file() {
    log_info "创建环境配置文件..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# 应用基础配置
APP_NAME=Magento-CJ-Middleware
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=3000

# 安全配置
SECRET_KEY=your-secret-key-change-this-in-production
JWT_SECRET=your-jwt-secret-change-this-in-production
JWT_EXPIRES_IN=24h

# CORS配置
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
ALLOWED_HOSTS=["localhost","127.0.0.1"]

# 数据库配置
DB_HOST=mysql
DB_PORT=3306
DB_NAME=magento_cj_middleware
DB_USER=magento_user
DB_PASSWORD=magento123456
DB_CHARSET=utf8mb4
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=100

# 队列配置
QUEUE_REDIS_HOST=redis
QUEUE_REDIS_PORT=6379
QUEUE_REDIS_DB=1
QUEUE_REDIS_PASSWORD=

# Magento配置 (请根据实际情况修改)
MAGENTO_BASE_URL=https://your-magento-store.com
MAGENTO_API_TOKEN=your-magento-api-token
MAGENTO_API_USER=your-magento-api-user
MAGENTO_API_PASSWORD=your-magento-api-password
MAGENTO_TIMEOUT=30
MAGENTO_MAX_RETRIES=3

# CJ Dropshipping配置 (请根据实际情况修改)
CJ_API_BASE_URL=https://developers.cjdropshipping.com/api2.0/v1
CJ_API_EMAIL=your-cj-email@example.com
CJ_API_PASSWORD=your-cj-api-password
CJ_TIMEOUT=30
CJ_MAX_RETRIES=3

# 同步配置
SYNC_INTERVAL_MINUTES=30
BATCH_SIZE=100
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY=5000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_MAX_SIZE=10
LOG_BACKUP_COUNT=5

# 监控配置
ENABLE_METRICS=true
METRICS_PORT=9090

# Celery配置
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
EOF
        log_success "环境配置文件 .env 已创建"
        log_warning "请根据实际情况修改 .env 文件中的配置参数"
    else
        log_info "环境配置文件 .env 已存在"
    fi
}

# 创建日志目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p logs
    mkdir -p app/static
    mkdir -p app/templates
    
    log_success "目录创建完成"
}

# 构建和启动服务
deploy_services() {
    log_info "开始构建和启动服务..."
    
    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose down --remove-orphans
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker-compose build --no-cache
    
    # 启动服务
    log_info "启动服务..."
    docker-compose up -d
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    # 等待MySQL就绪
    log_info "等待MySQL服务就绪..."
    timeout=60
    counter=0
    while ! docker-compose exec -T mysql mysqladmin ping -h"localhost" --silent; do
        sleep 1
        counter=$((counter + 1))
        if [ $counter -ge $timeout ]; then
            log_error "MySQL服务启动超时"
            exit 1
        fi
    done
    log_success "MySQL服务已就绪"
    
    # 等待Redis就绪
    log_info "等待Redis服务就绪..."
    timeout=30
    counter=0
    while ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
        sleep 1
        counter=$((counter + 1))
        if [ $counter -ge $timeout ]; then
            log_error "Redis服务启动超时"
            exit 1
        fi
    done
    log_success "Redis服务已就绪"
    
    # 等待应用服务就绪
    log_info "等待应用服务就绪..."
    timeout=120
    counter=0
    while ! curl -f http://localhost:3000/health > /dev/null 2>&1; do
        sleep 2
        counter=$((counter + 2))
        if [ $counter -ge $timeout ]; then
            log_error "应用服务启动超时"
            exit 1
        fi
    done
    log_success "应用服务已就绪"
}

# 运行数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."
    
    # 等待数据库完全就绪
    sleep 5
    
    # 运行Alembic迁移
    docker-compose exec app alembic upgrade head
    
    log_success "数据库迁移完成"
}

# 显示服务状态
show_status() {
    log_info "显示服务状态..."
    
    echo ""
    echo "📊 服务状态:"
    docker-compose ps
    
    echo ""
    echo "🌐 访问地址:"
    echo "   - 应用主页: http://localhost:3000"
    echo "   - API文档: http://localhost:3000/docs"
    echo "   - 健康检查: http://localhost:3000/health"
    echo "   - 监控指标: http://localhost:3000/metrics"
    
    echo ""
    echo "📝 日志查看:"
    echo "   - 应用日志: docker-compose logs -f app"
    echo "   - MySQL日志: docker-compose logs -f mysql"
    echo "   - Redis日志: docker-compose logs -f redis"
    
    echo ""
    echo "🔧 常用命令:"
    echo "   - 停止服务: docker-compose down"
    echo "   - 重启服务: docker-compose restart"
    echo "   - 查看状态: docker-compose ps"
    echo "   - 进入容器: docker-compose exec app bash"
}

# 主函数
main() {
    echo "=========================================="
    echo "  Magento-CJ 中台服务 WSL 部署脚本"
    echo "=========================================="
    echo ""
    
    check_wsl_environment
    create_env_file
    create_directories
    deploy_services
    wait_for_services
    run_migrations
    show_status
    
    echo ""
    log_success "🎉 部署完成！"
    echo ""
    log_warning "重要提醒："
    echo "1. 请根据实际情况修改 .env 文件中的配置参数"
    echo "2. 生产环境请修改默认密码和密钥"
    echo "3. 建议配置防火墙规则"
    echo "4. 定期备份数据库数据"
}

# 执行主函数
main "$@" 