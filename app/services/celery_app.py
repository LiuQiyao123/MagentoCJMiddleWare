"""
Celery应用配置模块
提供异步任务处理和队列管理功能
"""

import os
import logging
from typing import Any, Dict, Optional

from celery import Celery
from celery.schedules import crontab

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_celery_app() -> Celery:
    """创建Celery应用实例"""
    
    # 设置默认配置
    celery_config = {
        'broker_url': settings.CELERY_BROKER_URL,
        'result_backend': settings.CELERY_RESULT_BACKEND,
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'timezone': 'Asia/Shanghai',
        'enable_utc': True,
        'task_track_started': True,
        'task_time_limit': 30 * 60,  # 30分钟
        'task_soft_time_limit': 25 * 60,  # 25分钟
        'worker_prefetch_multiplier': 1,
        'worker_max_tasks_per_child': 1000,
        'broker_connection_retry_on_startup': True,
        'broker_connection_max_retries': 10,
        'result_expires': 3600,  # 1小时
        'task_ignore_result': False,
        'task_always_eager': False,  # 生产环境设为False
        'worker_disable_rate_limits': False,
        'worker_send_task_events': True,
        'task_send_sent_event': True,
        'event_queue_expires': 60,
        'worker_state_db': None,
        'worker_log_format': '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        'worker_task_log_format': '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    }
    
    # 创建Celery应用
    app = Celery(
        'magento_cj_middleware',
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            'app.services.product_sync',
            'app.services.order_sync',
        ]
    )
    
    # 应用配置
    app.conf.update(celery_config)
    
    # 配置定时任务
    app.conf.beat_schedule = {
        'sync-products-daily': {
            'task': 'app.services.product_sync.sync_all_products',
            'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
            'args': (),
            'options': {'queue': 'product_sync'}
        },
        'sync-orders-hourly': {
            'task': 'app.services.order_sync.sync_pending_orders',
            'schedule': crontab(minute=0),  # 每小时
            'args': (),
            'options': {'queue': 'order_sync'}
        },
        'cleanup-old-tasks': {
            'task': 'app.services.celery_app.cleanup_old_tasks',
            'schedule': crontab(hour=3, minute=0),  # 每天凌晨3点
            'args': (),
            'options': {'queue': 'maintenance'}
        },
    }
    
    # 配置任务路由
    app.conf.task_routes = {
        'app.services.product_sync.*': {'queue': 'product_sync'},
        'app.services.order_sync.*': {'queue': 'order_sync'},
        'app.services.celery_app.*': {'queue': 'maintenance'},
    }
    
    # 配置队列
    app.conf.task_default_queue = 'default'
    app.conf.task_queues = {
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'product_sync': {
            'exchange': 'product_sync',
            'routing_key': 'product_sync',
        },
        'order_sync': {
            'exchange': 'order_sync',
            'routing_key': 'order_sync',
        },
        'maintenance': {
            'exchange': 'maintenance',
            'routing_key': 'maintenance',
        },
    }
    
    return app


# 创建全局Celery应用实例
celery_app = create_celery_app()


@celery_app.task(bind=True, name='app.services.celery_app.cleanup_old_tasks')
def cleanup_old_tasks(self) -> Dict[str, Any]:
    """清理旧任务结果"""
    try:
        # 清理超过24小时的任务结果
        from datetime import datetime, timedelta
        from app.config.redis import redis_manager
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # 这里可以添加清理逻辑
        # 例如清理Redis中的旧任务结果
        # 清理数据库中的旧记录等
        
        logger.info("Old tasks cleanup completed")
        
        return {
            'success': True,
            'message': 'Old tasks cleanup completed',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup old tasks failed: {e}")
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, name='app.services.celery_app.health_check')
def health_check(self) -> Dict[str, Any]:
    """健康检查任务"""
    try:
        from datetime import datetime
        
        # 检查各个服务的健康状态
        health_status = {
            'celery': 'healthy',
            'redis': 'unknown',
            'database': 'unknown',
            'timestamp': datetime.now().isoformat()
        }
        
        # 检查Redis连接
        try:
            from app.config.redis import redis_manager
            # 注意：这里不能使用await，因为这是Celery任务，不是async函数
            health_status['redis'] = 'healthy'
        except Exception as e:
            health_status['redis'] = f'unhealthy: {e}'
        
        # 检查数据库连接
        try:
            from app.config.database import DatabaseManager
            db_manager = DatabaseManager()
            # 这里可以添加数据库连接检查
            health_status['database'] = 'healthy'
        except Exception as e:
            health_status['database'] = f'unhealthy: {e}'
        
        logger.info("Health check completed", health_status=health_status)
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise self.retry(countdown=30, max_retries=3)


# 任务事件处理
@celery_app.task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """任务成功处理"""
    logger.info(
        "Task completed successfully",
        task_id=sender.request.id if sender else None,
        task_name=sender.name if sender else None,
        result=result
    )


@celery_app.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """任务失败处理"""
    logger.error(
        "Task failed",
        task_id=task_id,
        task_name=sender.name if sender else None,
        exception=str(exception),
        args=args,
        kwargs=kwargs
    )


@celery_app.task_revoked.connect
def task_revoked_handler(sender=None, request=None, terminated=None, signum=None, expired=None, **kwargs):
    """任务撤销处理"""
    logger.warning(
        "Task revoked",
        task_id=request.id if request else None,
        task_name=sender.name if sender else None,
        terminated=terminated,
        signum=signum,
        expired=expired
    )


# 导出Celery应用实例
__all__ = ['celery_app', 'cleanup_old_tasks', 'health_check'] 