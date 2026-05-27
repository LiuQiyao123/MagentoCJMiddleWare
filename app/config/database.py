"""
数据库配置和管理
"""
from typing import AsyncGenerator, Optional
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import QueuePool

from app.config.settings import get_settings
from app.models import Base

logger = structlog.get_logger(__name__)
settings = get_settings()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.async_engine = None
        self.sync_engine = None
        self.async_session_factory = None
        self.sync_session_factory = None
        
    async def initialize(self) -> None:
        """初始化数据库连接"""
        try:
            # 创建异步引擎
            self.async_engine = create_async_engine(
                settings.DATABASE_URL,
                poolclass=QueuePool,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.DEBUG,
            )
            
            # 创建同步引擎（用于Alembic迁移）
            self.sync_engine = create_engine(
                settings.database_url_sync,
                poolclass=QueuePool,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.DEBUG,
            )
            
            # 创建会话工厂
            self.async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            self.sync_session_factory = sessionmaker(
                self.sync_engine,
                expire_on_commit=False,
            )
            
            # 测试连接
            await self._test_connection()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error("Database initialization failed", extra={"error": str(e)})
            raise
    
    async def _test_connection(self) -> None:
        """测试数据库连接"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection test passed")
        except Exception as e:
            logger.error("Database connection test failed", extra={"error": str(e)})
            raise
    
    async def create_tables(self) -> None:
        """创建数据表"""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", extra={"error": str(e)})
            raise
    
    async def cleanup(self) -> None:
        """清理数据库连接"""
        try:
            if self.async_engine:
                await self.async_engine.dispose()
                logger.info("Async database engine disposed")
            
            if self.sync_engine:
                self.sync_engine.dispose()
                logger.info("Sync database engine disposed")
                
        except Exception as e:
            logger.error("Error during database cleanup", extra={"error": str(e)})
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取异步数据库会话"""
        if not self.async_session_factory:
            logger.warning("Database not initialized, attempting lazy initialization...")
            await self.initialize()
        
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error("Database session error", extra={"error": str(e)})
                raise
            finally:
                await session.close()
    
    def get_sync_session(self):
        """获取同步数据库会话"""
        if not self.sync_session_factory:
            raise RuntimeError("Database not initialized")
        
        return self.sync_session_factory()


# 全局数据库管理器实例
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：获取数据库会话"""
    async for session in db_manager.get_session():
        yield session 