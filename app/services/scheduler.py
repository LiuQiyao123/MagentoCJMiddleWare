"""
调度器管理模块
提供定时任务调度和管理功能
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta

from app.config.settings import get_settings
from app.services.queue import queue_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class SchedulerManager:
    """调度器管理器"""
    
    def __init__(self):
        self._initialized = False
        self._running = False
        self._tasks = {}
        self._scheduler_task = None
        self._running_tasks = set()  # 用于跟踪正在运行的任务
    
    async def initialize(self) -> None:
        """初始化调度器"""
        if self._initialized:
            return
        
        try:
            # 初始化队列管理器
            await queue_manager.initialize()
            
            # 注册默认任务
            self._register_default_tasks()
            
            self._initialized = True
            logger.info("Scheduler manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler manager: {e}")
            raise
    
    def _register_default_tasks(self) -> None:
        """注册默认的定时任务"""
        # 每小时同步订单
        self.register_task(
            "sync_orders_hourly",
            self._sync_orders_task,
            interval=timedelta(hours=1)
        )
        
        # 每天同步商品
        self.register_task(
            "sync_products_daily",
            self._sync_products_task,
            interval=timedelta(days=1)
        )
        
        # 每天清理旧数据
        self.register_task(
            "cleanup_daily",
            self._cleanup_task,
            interval=timedelta(days=1)
        )
        
        # 健康检查（每5分钟）
        self.register_task(
            "health_check",
            self._health_check_task,
            interval=timedelta(minutes=5)
        )
    
    def register_task(
        self,
        task_name: str,
        task_func: Callable,
        interval: timedelta,
        start_time: Optional[datetime] = None
    ) -> None:
        """注册定时任务"""
        if task_name in self._tasks:
            logger.warning(f"Task {task_name} already registered, overwriting")
        
        self._tasks[task_name] = {
            'func': task_func,
            'interval': interval,
            'next_run': start_time or datetime.now(),
            'last_run': None,
            'enabled': True
        }
        
        logger.info(f"Task {task_name} registered with interval {interval}")
    
    def unregister_task(self, task_name: str) -> bool:
        """取消注册定时任务"""
        if task_name in self._tasks:
            del self._tasks[task_name]
            logger.info(f"Task {task_name} unregistered")
            return True
        return False
    
    def enable_task(self, task_name: str) -> bool:
        """启用定时任务"""
        if task_name in self._tasks:
            self._tasks[task_name]['enabled'] = True
            logger.info(f"Task {task_name} enabled")
            return True
        return False
    
    def disable_task(self, task_name: str) -> bool:
        """禁用定时任务"""
        if task_name in self._tasks:
            self._tasks[task_name]['enabled'] = False
            logger.info(f"Task {task_name} disabled")
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
                
                # 检查需要执行的任务
                for task_name, task_info in self._tasks.items():
                    if not task_info['enabled']:
                        continue
                    
                    if now >= task_info['next_run']:
                        # 检查任务是否已在运行
                        if task_name in self._running_tasks:
                            logger.warning(f"Task {task_name} is still running, skipping this scheduled run.")
                            continue

                        # 执行任务
                        asyncio.create_task(self._execute_task(task_name, task_info))
                        
                        # 更新下次执行时间，防止漂移
                        task_info['next_run'] = task_info['next_run'] + task_info['interval']
                        task_info['last_run'] = now
                
                # 等待1秒后再次检查
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(5)  # 出错后等待5秒再继续
    
    async def _execute_task(self, task_name: str, task_info: Dict[str, Any]) -> None:
        """执行定时任务"""
        try:
            logger.info(f"Executing scheduled task: {task_name}")
            self._running_tasks.add(task_name)
            
            # 执行任务函数
            if asyncio.iscoroutinefunction(task_info['func']):
                await task_info['func']()
            else:
                task_info['func']()
            
            logger.info(f"Scheduled task {task_name} completed successfully")
            
        except Exception as e:
            logger.error(f"Error executing scheduled task {task_name}: {e}")
        finally:
            self._running_tasks.remove(task_name)
    
    async def _sync_orders_task(self) -> None:
        """同步订单任务"""
        try:
            # 将同步订单任务加入队列
            await queue_manager.enqueue_task('order_sync', {
                'task_type': 'sync_pending_orders',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error in sync orders task: {e}")
    
    async def _sync_products_task(self) -> None:
        """同步商品任务"""
        try:
            # 将同步商品任务加入队列
            await queue_manager.enqueue_task('product_sync', {
                'task_type': 'sync_all_products',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error in sync products task: {e}")
    
    async def _cleanup_task(self) -> None:
        """清理任务"""
        try:
            # 将清理任务加入队列
            await queue_manager.enqueue_task('maintenance', {
                'task_type': 'cleanup_old_data',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
    
    async def _health_check_task(self) -> None:
        """健康检查任务"""
        try:
            # 将健康检查任务加入队列
            await queue_manager.enqueue_task('maintenance', {
                'task_type': 'health_check',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error in health check task: {e}")
    
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
        return {
            task_name: self.get_task_status(task_name)
            for task_name in self._tasks.keys()
        }
    
    def is_running(self) -> bool:
        """检查调度器是否正在运行"""
        return self._running


# 全局调度器管理器实例
scheduler_manager = SchedulerManager() 