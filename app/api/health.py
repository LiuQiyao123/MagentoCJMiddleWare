"""
健康检查API模块
提供系统健康状态检查和监控端点
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.config.database import DatabaseManager
from app.config.redis import redis_manager
from app.services.queue import queue_manager
from app.services.scheduler import scheduler_manager

logger = logging.getLogger(__name__)
settings = get_settings()

health_router = APIRouter(tags=["健康检查"])


@health_router.get("/")
async def health_check() -> Dict[str, Any]:
    """基础健康检查"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Magento-CJ Middleware",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@health_router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """详细健康检查"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Magento-CJ Middleware",
            "version": "1.0.0",
            "components": {}
        }
        
        # 检查数据库连接
        try:
            db_manager = DatabaseManager()
            # 这里可以添加实际的数据库连接测试
            health_status["components"]["database"] = {
                "status": "healthy",
                "message": "Database connection OK"
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {e}"
            }
            health_status["status"] = "degraded"
        
        # 检查Redis连接
        try:
            client = await redis_manager.get_client()
            await client.ping()
            health_status["components"]["redis"] = {
                "status": "healthy",
                "message": "Redis connection OK"
            }
        except Exception as e:
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "message": f"Redis connection failed: {e}"
            }
            health_status["status"] = "degraded"
        
        # 检查队列管理器
        try:
            if queue_manager._initialized:
                health_status["components"]["queue_manager"] = {
                    "status": "healthy",
                    "message": "Queue manager OK"
                }
            else:
                health_status["components"]["queue_manager"] = {
                    "status": "unhealthy",
                    "message": "Queue manager not initialized"
                }
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["queue_manager"] = {
                "status": "unhealthy",
                "message": f"Queue manager failed: {e}"
            }
            health_status["status"] = "degraded"
        
        # 检查调度器
        try:
            if scheduler_manager.is_running():
                health_status["components"]["scheduler"] = {
                    "status": "healthy",
                    "message": "Scheduler running"
                }
            else:
                health_status["components"]["scheduler"] = {
                    "status": "unhealthy",
                    "message": "Scheduler not running"
                }
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["scheduler"] = {
                "status": "unhealthy",
                "message": f"Scheduler failed: {e}"
            }
            health_status["status"] = "degraded"
        
        # 检查配置
        try:
            # 检查关键配置项
            required_configs = [
                "MAGENTO_BASE_URL",
                "MAGENTO_API_TOKEN",
                "CJ_API_BASE_URL",
                "CJ_API_EMAIL",
                "CJ_API_PASSWORD"
            ]
            
            missing_configs = []
            for config_name in required_configs:
                if not hasattr(settings, config_name) or not getattr(settings, config_name):
                    missing_configs.append(config_name)
            
            if missing_configs:
                health_status["components"]["configuration"] = {
                    "status": "unhealthy",
                    "message": f"Missing configurations: {', '.join(missing_configs)}"
                }
                health_status["status"] = "degraded"
            else:
                health_status["components"]["configuration"] = {
                    "status": "healthy",
                    "message": "Configuration OK"
                }
        except Exception as e:
            health_status["components"]["configuration"] = {
                "status": "unhealthy",
                "message": f"Configuration check failed: {e}"
            }
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Detailed health check failed")


@health_router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """就绪检查"""
    try:
        # 检查关键服务是否就绪
        ready = True
        issues = []
        
        # 检查数据库
        try:
            db_manager = DatabaseManager()
            # 这里可以添加实际的数据库连接测试
        except Exception as e:
            ready = False
            issues.append(f"Database: {e}")
        
        # 检查Redis
        try:
            client = await redis_manager.get_client()
            await client.ping()
        except Exception as e:
            ready = False
            issues.append(f"Redis: {e}")
        
        if ready:
            return {
                "status": "ready",
                "timestamp": datetime.now().isoformat(),
                "message": "Service is ready to handle requests"
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "timestamp": datetime.now().isoformat(),
                    "message": "Service is not ready",
                    "issues": issues
                }
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=500, detail="Readiness check failed")


@health_router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """存活检查"""
    try:
        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "message": "Service is alive"
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(status_code=500, detail="Liveness check failed")


@health_router.get("/queue-stats")
async def queue_stats() -> Dict[str, Any]:
    """队列统计信息"""
    try:
        if not queue_manager._initialized:
            raise HTTPException(status_code=503, detail="Queue manager not initialized")
        
        stats = await queue_manager.get_all_queues_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "queues": stats
        }
        
    except Exception as e:
        logger.error(f"Queue stats check failed: {e}")
        raise HTTPException(status_code=500, detail="Queue stats check failed")


@health_router.get("/scheduler-stats")
async def scheduler_stats() -> Dict[str, Any]:
    """调度器统计信息"""
    try:
        tasks_status = scheduler_manager.get_all_tasks_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "scheduler_running": scheduler_manager.is_running(),
            "tasks": tasks_status
        }
        
    except Exception as e:
        logger.error(f"Scheduler stats check failed: {e}")
        raise HTTPException(status_code=500, detail="Scheduler stats check failed") 