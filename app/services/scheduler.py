"""
调度器管理模块
提供定时任务调度和管理功能
"""

import asyncio
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta

import structlog

from app.config.settings import get_settings
from app.services.queue import queue_manager

logger = structlog.get_logger(__name__)
settings = get_settings()


class SchedulerManager:
    """调度器管理器"""
    
    def __init__(self):
        self._initialized = False
        self._running = False
        self._tasks = {}
        self._scheduler_task = None
    
    async def initialize(self) -> None:
        """初始化调度器"""
        if self._initialized:
            return
        
        try:
            await queue_manager.initialize()
            self._register_default_tasks()
            self._initialized = True
            logger.info("Scheduler manager initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize scheduler manager", extra={"error": str(e)})
            raise
    
    def _register_default_tasks(self) -> None:
        """注册默认的定时任务"""
        self.register_task("sync_orders_hourly", self._sync_orders_task, interval=timedelta(hours=1))
        self.register_task("sync_products_daily", self._sync_products_task, interval=timedelta(days=1))
        self.register_task("cleanup_daily", self._cleanup_task, interval=timedelta(days=1))
        self.register_task("health_check", self._health_check_task, interval=timedelta(minutes=5))
    
    def register_task(
        self, task_name: str, task_func: Callable, interval: timedelta, start_time: Optional[datetime] = None
    ) -> None:
        """注册定时任务"""
        if task_name in self._tasks:
            logger.warning("Task already registered, overwriting", extra={"task": task_name})
        
        self._tasks[task_name] = {
            'func': task_func,
            'interval': interval,
            'next_run': start_time or datetime.now(),
            'last_run': None,
            'enabled': True
        }
        
        logger.info("Task registered", extra={"task": task_name, "interval_seconds": interval.total_seconds()})
    
    def unregister_task(self, task_name: str) -> bool:
        """取消注册定时任务"""
        if task_name in self._tasks:
            del self._tasks[task_name]
            logger.info("Task unregistered", extra={"task": task_name})
            return True
        return False
    
    def enable_task(self, task_name: str) -> bool:
        """启用定时任务"""
        if task_name in self._tasks:
            self._tasks[task_name]['enabled'] = True
            logger.info("Task enabled", extra={"task": task_name})
            return True
        return False
    
    def disable_task(self, task_name: str) -> bool:
        """禁用定时任务"""
        if task_name in self._tasks:
            self._tasks[task_name]['enabled'] = False
            logger.info("Task disabled", extra={"task": task_name})
            return True
        return False
    
    async def start(self) -> None:
        """启动调度器"""
        if not self._initialized:
            await self.initialize()
        
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")
    
    async def stop(self) -> None:
        """停止调度器"""
        if not self._running:
            return
        
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Scheduler stopped")
    
    async def _scheduler_loop(self) -> None:
        """调度器主循环"""
        while self._running:
            try:
                now = datetime.now()
                
                for task_name, task_info in self._tasks.items():
                    if not task_info['enabled']:
                        continue
                    
                    if now >= task_info['next_run']:
                        asyncio.create_task(self._execute_task(task_name, task_info))
                        task_info['next_run'] = now + task_info['interval']
                        task_info['last_run'] = now
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in scheduler loop", extra={"error": str(e)})
                await asyncio.sleep(5)
    
    async def _execute_task(self, task_name: str, task_info: Dict[str, Any]) -> None:
        """执行定时任务"""
        try:
            logger.info("Executing scheduled task", extra={"task": task_name})
            
            if asyncio.iscoroutinefunction(task_info['func']):
                await task_info['func']()
            else:
                task_info['func']()
            
            logger.info("Scheduled task completed successfully", extra={"task": task_name})
            
        except Exception as e:
            logger.error("Error executing scheduled task", extra={"task": task_name, "error": str(e)})
    
    async def _sync_orders_task(self) -> None:
        """同步订单任务"""
        try:
            await queue_manager.enqueue_task('order_sync', {
                'task_type': 'sync_pending_orders',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error("Error in sync orders task", extra={"error": str(e)})
    
    async def _sync_products_task(self) -> None:
        """同步商品任务"""
        try:
            await queue_manager.enqueue_task('product_sync', {
                'task_type': 'sync_all_products',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error("Error in sync products task", extra={"error": str(e)})
    
    async def _cleanup_task(self) -> None:
        """清理任务"""
        try:
            await queue_manager.enqueue_task('maintenance', {
                'task_type': 'cleanup_old_data',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error("Error in cleanup task", extra={"error": str(e)})
    
    async def _health_check_task(self) -> None:
        """健康检查任务"""
        try:
            await queue_manager.enqueue_task('maintenance', {
                'task_type': 'health_check',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error("Error in health check task", extra={"error": str(e)})
    
    def get_task_status(self, task_name: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_name not in self._tasks:
            return None
        task_info = self._tasks[task_name]
        return {
            'name': task_name,
            'enabled': task_info['enabled'],
            'interval': str(task_info['interval']),
            'next_run': task_info['next_run'].isoformat() if task_info['next_run'] else None,
            'last_run': task_info['last_run'].isoformat() if task_info['last_run'] else None,
        }
    
    def get_all_tasks_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        return {task_name: self.get_task_status(task_name) for task_name in self._tasks.keys()}
    
    def is_running(self) -> bool:
        """检查调度器是否正在运行"""
        return self._running


# 全局调度器管理器实例
scheduler_manager = SchedulerManager()
