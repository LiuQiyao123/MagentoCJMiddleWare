"""
Magento-CJ Dropshipping 中台服务主应用
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import get_settings
from app.config.database import DatabaseManager
from app.config.redis import RedisManager
from app.core.logging import setup_logging
from app.core.exceptions import APIException
from app.services.queue import QueueManager
from app.services.scheduler import SchedulerManager
from app.api.v1 import api_router
from app.api.health import health_router

# 设置日志
setup_logging()
logger = structlog.get_logger(__name__)

# 监控指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

settings = get_settings()

# 全局管理器实例
db_manager = DatabaseManager()
redis_manager = RedisManager()
queue_manager = QueueManager()
scheduler_manager = SchedulerManager()

# 模板和静态文件
templates = Jinja2Templates(directory="app/templates")


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Prometheus监控中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await call_next(request)
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()
            
            REQUEST_DURATION.observe(asyncio.get_event_loop().time() - start_time)
            
            return response
            
        except Exception as e:
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            REQUEST_DURATION.observe(asyncio.get_event_loop().time() - start_time)
            raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    logger.info("Starting application initialization...")
    
    try:
        # 1. 初始化数据库
        await db_manager.initialize()
        logger.info("Database initialized successfully")
        
        # 2. 初始化Redis
        await redis_manager.initialize()
        logger.info("Redis initialized successfully")
        
        # 3. 初始化任务队列
        await queue_manager.initialize()
        logger.info("Queue manager initialized successfully")
        
        # 4. 启动定时任务
        await scheduler_manager.start()
        logger.info("Scheduler started successfully")
        
        logger.info("Application initialization completed")
        
        yield
        
    except Exception as e:
        logger.error("Application initialization failed", extra={"error": str(e)})
        raise
    finally:
        # 清理资源
        logger.info("Starting application shutdown...")
        
        try:
            await scheduler_manager.stop()
            await queue_manager.cleanup()
            await redis_manager.cleanup()
            await db_manager.cleanup()
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error("Error during shutdown", extra={"error": str(e)})


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    app = FastAPI(
        title="Magento-CJ Middleware API",
        description="Magento 2 与 CJ Dropshipping 集成中台服务",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # 添加中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
    
    app.add_middleware(PrometheusMiddleware)
    
    # 请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        try:
            response = await call_next(request)
            
            process_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.3f}s",
                }
            )
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = asyncio.get_event_loop().time() - start_time
            
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time": f"{process_time:.3f}s",
                }
            )
            raise
    
    # 全局异常处理
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        logger.error(
            "API Exception",
            extra={
                "path": request.url.path,
                "error_code": exc.error_code,
                "error_message": exc.message,
                "details": exc.details,
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": exc.timestamp.isoformat(),
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            extra={
                "path": request.url.path,
                "error": str(exc),
                "exc_info": True,
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": None,
                "timestamp": None,
            }
        )
    
    # 挂载静态文件
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    # 注册路由
    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(api_router, prefix="/api/v1")
    
    # Web界面路由
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    
    # Prometheus指标端点
    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type="text/plain")
    
    return app


# 创建应用实例
app = create_app()


def run_server():
    """运行开发服务器"""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # 使用自定义日志配置
    )


if __name__ == "__main__":
    run_server() 