"""
队列管理模块
提供任务队列管理和监控功能
"""

import asyncio
from typing import Any, Dict, Optional

import structlog

from app.config.settings import get_settings
from app.config.redis import redis_manager

logger = structlog.get_logger(__name__)
settings = get_settings()


class QueueManager:
    """队列管理器"""
    
    def __init__(self):
        self._initialized = False
        self._queues = {
            'default': 'default',
            'product_sync': 'product_sync',
            'order_sync': 'order_sync',
            'maintenance': 'maintenance',
        }
    
    async def initialize(self) -> None:
        """初始化队列管理器"""
        if self._initialized:
            return
        
        try:
            # 初始化Redis连接
            await redis_manager.initialize()
            
            # 创建队列（在Redis中创建队列键）
            for queue_name in self._queues.values():
                await self._create_queue(queue_name)
            
            self._initialized = True
            logger.info("Queue manager initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize queue manager", extra={"error": str(e)})
            raise
    
    async def _create_queue(self, queue_name: str) -> None:
        """创建队列"""
        try:
            client = await redis_manager.get_client()
            await client.set(f"queue:{queue_name}:created", "1")
            logger.debug("Queue created", extra={"queue": queue_name})
        except Exception as e:
            logger.error("Failed to create queue", extra={"queue": queue_name, "error": str(e)})
    
    async def enqueue_task(self, queue_name: str, task_data: Dict[str, Any]) -> bool:
        """将任务加入队列"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if queue_name not in self._queues:
                raise ValueError(f"Unknown queue: {queue_name}")
            
            client = await redis_manager.get_client()
            
            import json
            task_json = json.dumps(task_data)
            
            await client.lpush(f"queue:{queue_name}:tasks", task_json)
            await self._update_queue_stats(queue_name, "enqueued")
            
            logger.info("Task enqueued", extra={"queue": queue_name})
            return True
            
        except Exception as e:
            logger.error("Failed to enqueue task", extra={"queue": queue_name, "error": str(e)})
            return False
    
    async def dequeue_task(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """从队列中取出任务"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if queue_name not in self._queues:
                raise ValueError(f"Unknown queue: {queue_name}")
            
            client = await redis_manager.get_client()
            
            task_json = await client.brpop(f"queue:{queue_name}:tasks", timeout=1)
            
            if task_json:
                import json
                task_data = json.loads(task_json[1])
                await self._update_queue_stats(queue_name, "dequeued")
                logger.debug("Task dequeued", extra={"queue": queue_name})
                return task_data
            
            return None
            
        except Exception as e:
            logger.error("Failed to dequeue task", extra={"queue": queue_name, "error": str(e)})
            return None
    
    async def get_queue_length(self, queue_name: str) -> int:
        """获取队列长度"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if queue_name not in self._queues:
                return 0
            
            client = await redis_manager.get_client()
            length = await client.llen(f"queue:{queue_name}:tasks")
            return length
            
        except Exception as e:
            logger.error("Failed to get queue length", extra={"queue": queue_name, "error": str(e)})
            return 0
    
    async def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """获取队列统计信息"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if queue_name not in self._queues:
                return {}
            
            client = await redis_manager.get_client()
            stats = await client.hgetall(f"queue:{queue_name}:stats")
            length = await self.get_queue_length(queue_name)
            
            return {
                "queue_name": queue_name,
                "length": length,
                "enqueued": int(stats.get("enqueued", 0)),
                "dequeued": int(stats.get("dequeued", 0)),
                "failed": int(stats.get("failed", 0)),
            }
            
        except Exception as e:
            logger.error("Failed to get queue stats", extra={"queue": queue_name, "error": str(e)})
            return {}
    
    async def _update_queue_stats(self, queue_name: str, stat_type: str) -> None:
        """更新队列统计信息"""
        try:
            client = await redis_manager.get_client()
            await client.hincrby(f"queue:{queue_name}:stats", stat_type, 1)
        except Exception as e:
            logger.error("Failed to update queue stats", extra={"queue": queue_name, "error": str(e)})
    
    async def clear_queue(self, queue_name: str) -> bool:
        """清空队列"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if queue_name not in self._queues:
                return False
            
            client = await redis_manager.get_client()
            await client.delete(f"queue:{queue_name}:tasks")
            await client.delete(f"queue:{queue_name}:stats")
            
            logger.info("Queue cleared", extra={"queue": queue_name})
            return True
            
        except Exception as e:
            logger.error("Failed to clear queue", extra={"queue": queue_name, "error": str(e)})
            return False
    
    async def get_all_queues_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有队列的统计信息"""
        try:
            stats = {}
            for queue_name in self._queues.values():
                stats[queue_name] = await self.get_queue_stats(queue_name)
            return stats
        except Exception as e:
            logger.error("Failed to get all queues stats", extra={"error": str(e)})
            return {}
    
    async def cleanup(self) -> None:
        """清理队列管理器"""
        try:
            self._initialized = False
            logger.info("Queue manager cleaned up")
        except Exception as e:
            logger.error("Error during queue manager cleanup", extra={"error": str(e)})


# 全局队列管理器实例
queue_manager = QueueManager()
