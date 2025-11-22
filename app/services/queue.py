"""
队列管理模块
提供任务队列管理和监控功能
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from app.config.settings import get_settings
from app.config.redis import redis_manager

logger = logging.getLogger(__name__)
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
            logger.error(f"Failed to initialize queue manager: {e}")
            raise
    
    async def _create_queue(self, queue_name: str) -> None:
        """创建队列"""
        try:
            client = await redis_manager.get_client()
            # 创建队列键（用于监控队列长度）
            await client.set(f"queue:{queue_name}:created", "1")
            logger.debug(f"Queue {queue_name} created")
        except Exception as e:
            logger.error(f"Failed to create queue {queue_name}: {e}")
    
    async def enqueue_task(self, queue_name: str, task_data: Dict[str, Any]) -> bool:
        """将任务加入队列"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if queue_name not in self._queues:
                raise ValueError(f"Unknown queue: {queue_name}")
            
            client = await redis_manager.get_client()
            
            # 将任务数据序列化并加入队列
            import json
            task_json = json.dumps(task_data)
            
            # 使用Redis List作为队列
            await client.lpush(f"queue:{queue_name}:tasks", task_json)
            
            # 更新队列统计信息
            await self._update_queue_stats(queue_name, "enqueued")
            
            logger.info(f"Task enqueued to {queue_name}", task_data=task_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue task to {queue_name}: {e}")
            return False
    
    async def dequeue_task(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """从队列中取出任务"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if queue_name not in self._queues:
                raise ValueError(f"Unknown queue: {queue_name}")
            
            client = await redis_manager.get_client()
            
            # 从队列中取出任务
            task_json = await client.brpop(f"queue:{queue_name}:tasks", timeout=1)
            
            if task_json:
                import json
                task_data = json.loads(task_json[1])
                
                # 更新队列统计信息
                await self._update_queue_stats(queue_name, "dequeued")
                
                logger.debug(f"Task dequeued from {queue_name}", task_data=task_data)
                return task_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to dequeue task from {queue_name}: {e}")
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
            logger.error(f"Failed to get queue length for {queue_name}: {e}")
            return 0
    
    async def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """获取队列统计信息"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if queue_name not in self._queues:
                return {}
            
            client = await redis_manager.get_client()
            
            # 获取队列统计信息
            stats = await client.hgetall(f"queue:{queue_name}:stats")
            
            # 获取当前队列长度
            length = await self.get_queue_length(queue_name)
            
            return {
                "queue_name": queue_name,
                "length": length,
                "enqueued": int(stats.get("enqueued", 0)),
                "dequeued": int(stats.get("dequeued", 0)),
                "failed": int(stats.get("failed", 0)),
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats for {queue_name}: {e}")
            return {}
    
    async def _update_queue_stats(self, queue_name: str, stat_type: str) -> None:
        """更新队列统计信息"""
        try:
            client = await redis_manager.get_client()
            await client.hincrby(f"queue:{queue_name}:stats", stat_type, 1)
        except Exception as e:
            logger.error(f"Failed to update queue stats for {queue_name}: {e}")
    
    async def clear_queue(self, queue_name: str) -> bool:
        """清空队列"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if queue_name not in self._queues:
                return False
            
            client = await redis_manager.get_client()
            
            # 删除队列中的所有任务
            await client.delete(f"queue:{queue_name}:tasks")
            
            # 重置统计信息
            await client.delete(f"queue:{queue_name}:stats")
            
            logger.info(f"Queue {queue_name} cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear queue {queue_name}: {e}")
            return False
    
    async def get_all_queues_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有队列的统计信息"""
        try:
            stats = {}
            for queue_name in self._queues.values():
                stats[queue_name] = await self.get_queue_stats(queue_name)
            return stats
        except Exception as e:
            logger.error(f"Failed to get all queues stats: {e}")
            return {}
    
    async def cleanup(self) -> None:
        """清理队列管理器"""
        try:
            # 这里可以添加清理逻辑
            # 例如清理过期的队列数据等
            self._initialized = False
            logger.info("Queue manager cleaned up")
        except Exception as e:
            logger.error(f"Error during queue manager cleanup: {e}")


# 全局队列管理器实例
queue_manager = QueueManager() 