"""
Redis配置管理模块
提供Redis连接池管理和基本操作功能
"""

import asyncio
import logging
from typing import Optional, Any, Dict
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisManager:
    """Redis连接管理器"""
    
    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化Redis连接池"""
        if self._initialized:
            return
        
        try:
            # 创建连接池
            self._pool = ConnectionPool.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                decode_responses=True,
            )
            
            # 创建Redis客户端
            self._client = Redis(connection_pool=self._pool)
            
            # 测试连接
            await self._client.ping()
            
            self._initialized = True
            logger.info("Redis connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def get_client(self) -> Redis:
        """获取Redis客户端实例"""
        if not self._initialized:
            await self.initialize()
        return self._client
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置键值对"""
        try:
            client = await self.get_client()
            result = await client.set(key, value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """获取键值"""
        try:
            client = await self.get_client()
            return await client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """删除键"""
        try:
            client = await self.get_client()
            result = await client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            client = await self.get_client()
            result = await client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间"""
        try:
            client = await self.get_client()
            result = await client.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """设置哈希表字段"""
        try:
            client = await self.get_client()
            result = await client.hset(name, key, value)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis HSET error for hash {name}, key {key}: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希表字段值"""
        try:
            client = await self.get_client()
            return await client.hget(name, key)
        except Exception as e:
            logger.error(f"Redis HGET error for hash {name}, key {key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """获取哈希表所有字段"""
        try:
            client = await self.get_client()
            return await client.hgetall(name)
        except Exception as e:
            logger.error(f"Redis HGETALL error for hash {name}: {e}")
            return {}
    
    async def cleanup(self) -> None:
        """清理Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None
        
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        
        self._initialized = False
        logger.info("Redis connections cleaned up")


# 全局Redis管理器实例
redis_manager = RedisManager()


@asynccontextmanager
async def get_redis_client():
    """Redis客户端上下文管理器"""
    client = await redis_manager.get_client()
    try:
        yield client
    except Exception as e:
        logger.error(f"Redis operation error: {e}")
        raise 