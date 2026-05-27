"""
异步任务管理器
管理后台任务的进度、状态、错误日志
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

import structlog
from app.config.redis import redis_manager

logger = structlog.get_logger(__name__)

TASK_PREFIX = "async_task:"


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskManager:
    """异步任务管理器，基于Redis存储任务状态"""

    async def create_task(self, task_type: str, data: Dict[str, Any]) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())[:8]
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "status": TaskStatus.PENDING,
            "progress": 0,
            "message": "任务已创建",
            "data": json.dumps(data, ensure_ascii=False),
            "result": "",
            "errors": json.dumps([], ensure_ascii=False),
            "logs": json.dumps([], ensure_ascii=False),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        client = await redis_manager.get_client()
        key = f"{TASK_PREFIX}{task_id}"
        await client.hset(key, mapping=task)
        await client.expire(key, 3600)  # 1小时后自动过期
        return task_id

    async def update_progress(self, task_id: str, progress: int, message: str = "", log: str = ""):
        """更新任务进度"""
        client = await redis_manager.get_client()
        key = f"{TASK_PREFIX}{task_id}"
        await client.hset(key, "progress", progress)
        await client.hset(key, "message", message)
        await client.hset(key, "status", TaskStatus.RUNNING)
        await client.hset(key, "updated_at", datetime.utcnow().isoformat())
        if log:
            await self._add_log(client, key, log)

    async def mark_success(self, task_id: str, result: Any = None):
        """标记任务成功"""
        client = await redis_manager.get_client()
        key = f"{TASK_PREFIX}{task_id}"
        await client.hset(key, "status", TaskStatus.SUCCESS)
        await client.hset(key, "progress", 100)
        await client.hset(key, "message", "任务完成")
        await client.hset(key, "result", json.dumps(result, ensure_ascii=False) if result else "")
        await client.hset(key, "updated_at", datetime.utcnow().isoformat())

    async def mark_failed(self, task_id: str, error: str):
        """标记任务失败"""
        client = await redis_manager.get_client()
        key = f"{TASK_PREFIX}{task_id}"
        await client.hset(key, "status", TaskStatus.FAILED)
        await client.hset(key, "message", f"失败: {error}")
        errors = json.loads((await client.hget(key, "errors")) or "[]")
        errors.append({"time": datetime.utcnow().isoformat(), "error": error})
        await client.hset(key, "errors", json.dumps(errors, ensure_ascii=False))
        await client.hset(key, "updated_at", datetime.utcnow().isoformat())

    async def update_data(self, task_id: str, data: Dict[str, Any]):
        """更新任务的自定义数据（存储中间结果，如 created_skus）"""
        client = await redis_manager.get_client()
        key = f"{TASK_PREFIX}{task_id}"
        await client.hset(key, "task_data", json.dumps(data, ensure_ascii=False))
    
    async def add_error(self, task_id: str, error: str):
        """添加错误记录"""
        client = await redis_manager.get_client()
        key = f"{TASK_PREFIX}{task_id}"
        errors = json.loads((await client.hget(key, "errors")) or "[]")
        errors.append({"time": datetime.utcnow().isoformat(), "error": error})
        await client.hset(key, "errors", json.dumps(errors, ensure_ascii=False))
        await client.hset(key, "updated_at", datetime.utcnow().isoformat())

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        client = await redis_manager.get_client()
        key = f"{TASK_PREFIX}{task_id}"
        data = await client.hgetall(key)
        if not data:
            return None
        return {
            k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
            for k, v in data.items()
        }

    async def list_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近任务列表"""
        client = await redis_manager.get_client()
        keys = await client.keys(f"{TASK_PREFIX}*")
        keys.sort(reverse=True)
        tasks = []
        for key in keys[:limit]:
            data = await client.hgetall(key)
            task = {
                k.decode() if isinstance(k, bytes) else k:
                    v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()
            }
            tasks.append(task)
        return tasks

    async def _add_log(self, client, key: str, log_text: str):
        """添加日志"""
        logs = json.loads((await client.hget(key, "logs")) or "[]")
        logs.append({"time": datetime.utcnow().isoformat(), "log": log_text})
        await client.hset(key, "logs", json.dumps(logs, ensure_ascii=False))


# 全局实例
task_manager = TaskManager()
