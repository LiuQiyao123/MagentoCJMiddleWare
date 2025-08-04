@echo off
chcp 65001 >nul
echo 🚀 启动 Magento-CJ 中间件...

REM 检查.env文件是否存在
if not exist .env (
    echo ❌ 错误: .env 文件不存在
    echo 请先复制 .env.example 为 .env 并配置您的API密钥
    pause
    exit /b 1
)

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Docker 未运行
    echo 请先启动 Docker Desktop
    pause
    exit /b 1
)

REM 构建并启动服务
echo 📦 构建 Docker 镜像...
docker-compose build

echo 🔄 启动服务...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 🔍 检查服务状态...
docker-compose ps

REM 测试API连接
echo 🧪 测试API连接...

REM 测试中间件健康状态
echo 测试中间件健康状态...
curl -s http://localhost:3000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ 中间件未响应
) else (
    echo ✅ 中间件运行正常
)

REM 测试Magento连接
echo 测试Magento连接...
curl -s http://localhost:3000/api/v1/health/magento >nul 2>&1
if errorlevel 1 (
    echo ❌ Magento连接失败
) else (
    echo ✅ Magento连接正常
)

REM 测试CJ连接
echo 测试CJ连接...
curl -s http://localhost:3000/api/v1/health/cj >nul 2>&1
if errorlevel 1 (
    echo ❌ CJ连接失败
) else (
    echo ✅ CJ连接正常
)

echo.
echo ✅ 启动完成！
echo 📊 监控面板: http://localhost:5555 (Celery监控)
echo 📚 API文档: http://localhost:3000/docs
echo 🔧 管理界面: http://localhost:3000/admin

echo.
echo 📝 常用命令:
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo   查看状态: docker-compose ps

pause 