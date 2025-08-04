#!/usr/bin/env python3
"""
启动脚本 - 用于启动不同的服务组件
"""
import os
import sys
import argparse
import subprocess
import signal
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_api_server():
    """启动API服务器"""
    print("Starting API server...")
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # 启动uvicorn服务器
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--log-level", "info"
    ]
    
    try:
        subprocess.run(cmd, env=env, cwd=project_root)
    except KeyboardInterrupt:
        print("\nAPI server stopped.")


def start_celery_worker():
    """启动Celery Worker"""
    print("Starting Celery worker...")
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # 启动celery worker
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "app.tasks.sync_tasks:celery_app",
        "worker",
        "--loglevel=info",
        "--concurrency=4",
        "--pool=prefork"
    ]
    
    try:
        subprocess.run(cmd, env=env, cwd=project_root)
    except KeyboardInterrupt:
        print("\nCelery worker stopped.")


def start_celery_beat():
    """启动Celery Beat定时任务"""
    print("Starting Celery beat scheduler...")
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # 启动celery beat
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "app.tasks.sync_tasks:celery_app",
        "beat",
        "--loglevel=info",
        "--schedule=/tmp/celerybeat-schedule"
    ]
    
    try:
        subprocess.run(cmd, env=env, cwd=project_root)
    except KeyboardInterrupt:
        print("\nCelery beat stopped.")


def start_flower():
    """启动Flower监控界面"""
    print("Starting Flower monitoring...")
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # 启动flower
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "app.tasks.sync_tasks:celery_app",
        "flower",
        "--port=5555",
        "--broker_api=http://guest:guest@localhost:15672/api/"
    ]
    
    try:
        subprocess.run(cmd, env=env, cwd=project_root)
    except KeyboardInterrupt:
        print("\nFlower stopped.")


def init_database():
    """初始化数据库"""
    print("Initializing database...")
    
    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # 运行数据库初始化脚本
    cmd = [sys.executable, "-c", """
import asyncio
from app.config.database import DatabaseManager

async def init_db():
    db_manager = DatabaseManager()
    await db_manager.initialize()
    await db_manager.create_tables()
    print("Database initialized successfully!")
    await db_manager.cleanup()

asyncio.run(init_db())
"""]
    
    try:
        subprocess.run(cmd, env=env, cwd=project_root)
    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)


def check_dependencies():
    """检查依赖服务"""
    print("Checking dependencies...")
    
    # 检查MySQL
    try:
        import mysql.connector
        print("✓ MySQL connector available")
    except ImportError:
        print("✗ MySQL connector not available")
        return False
    
    # 检查Redis
    try:
        import redis
        print("✓ Redis client available")
    except ImportError:
        print("✗ Redis client not available")
        return False
    
    # 检查其他依赖
    required_packages = [
        "fastapi", "uvicorn", "celery", "sqlalchemy", 
        "httpx", "structlog", "pydantic"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} available")
        except ImportError:
            print(f"✗ {package} not available")
            return False
    
    print("All dependencies are available!")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Magento-CJ Middleware Service Manager")
    parser.add_argument(
        "command",
        choices=["api", "worker", "beat", "flower", "init-db", "check-deps", "all"],
        help="Command to run"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies before starting"
    )
    
    args = parser.parse_args()
    
    # 检查依赖
    if args.check_deps or args.command == "check-deps":
        if not check_dependencies():
            print("Please install missing dependencies.")
            sys.exit(1)
        if args.command == "check-deps":
            return
    
    # 执行命令
    if args.command == "api":
        start_api_server()
    elif args.command == "worker":
        start_celery_worker()
    elif args.command == "beat":
        start_celery_beat()
    elif args.command == "flower":
        start_flower()
    elif args.command == "init-db":
        init_database()
    elif args.command == "all":
        print("Starting all services...")
        print("Note: This will start services in sequence. For production, use a process manager.")
        
        # 在生产环境中，建议使用supervisor或systemd来管理多个进程
        processes = []
        
        try:
            # 启动API服务器
            api_process = subprocess.Popen([
                sys.executable, __file__, "api"
            ])
            processes.append(("API Server", api_process))
            
            # 启动Celery Worker
            worker_process = subprocess.Popen([
                sys.executable, __file__, "worker"
            ])
            processes.append(("Celery Worker", worker_process))
            
            # 启动Celery Beat
            beat_process = subprocess.Popen([
                sys.executable, __file__, "beat"
            ])
            processes.append(("Celery Beat", beat_process))
            
            print("All services started. Press Ctrl+C to stop.")
            
            # 等待所有进程
            for name, process in processes:
                process.wait()
                
        except KeyboardInterrupt:
            print("\nStopping all services...")
            for name, process in processes:
                print(f"Stopping {name}...")
                process.terminate()
                process.wait()
            print("All services stopped.")


if __name__ == "__main__":
    main() 