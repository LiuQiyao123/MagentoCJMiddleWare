"""
CJ API频率限制器
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class APIEndpoint(Enum):
    """API接口类型枚举"""
    PRODUCT_SEARCH = "product_search"
    PRODUCT_DETAIL = "product_detail"
    PRODUCT_INVENTORY = "product_inventory"
    ORDER_CREATE = "order_create"
    ORDER_DETAIL = "order_detail"
    ORDER_LIST = "order_list"
    ORDER_CANCEL = "order_cancel"
    SHIPPING_METHODS = "shipping_methods"
    SHIPPING_COST = "shipping_cost"
    TRACKING_INFO = "tracking_info"
    CATEGORIES = "categories"
    COUNTRIES = "countries"
    ADDRESS_VALIDATE = "address_validate"


class CJRateLimiter:
    """CJ API频率限制器"""
    
    def __init__(self):
        # 每日限制
        self.daily_limit = 1000
        
        # 最小调用间隔（秒）
        self.min_interval = 2.0
        
        # 按接口类型记录最后调用时间
        self.last_call_time: Dict[APIEndpoint, float] = {}
        
        # 按接口类型记录每日调用次数
        self.daily_call_count: Dict[APIEndpoint, int] = {}
        
        # 每日重置时间
        self.daily_reset_time: Optional[datetime] = None
        
        # 动态间隔调整
        self.current_interval = self.min_interval
        self.max_interval = 10.0  # 最大间隔10秒
        
        # 错误计数
        self.error_count = 0
        self.max_errors = 5  # 连续错误5次后增加间隔
        
        logger.info("CJ Rate Limiter initialized", 
                   daily_limit=self.daily_limit,
                   min_interval=self.min_interval)
    
    def _get_daily_reset_time(self) -> datetime:
        """获取每日重置时间（UTC时间）"""
        now = datetime.utcnow()
        # 设置为下一个UTC日期的00:00:00
        next_day = now + timedelta(days=1)
        return next_day.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _should_reset_daily_count(self) -> bool:
        """检查是否需要重置每日计数"""
        if not self.daily_reset_time:
            self.daily_reset_time = self._get_daily_reset_time()
            return True
        
        now = datetime.utcnow()
        if now >= self.daily_reset_time:
            self.daily_reset_time = self._get_daily_reset_time()
            return True
        
        return False
    
    def _reset_daily_count(self) -> None:
        """重置每日调用计数"""
        self.daily_call_count.clear()
        logger.info("Daily call count reset")
    
    def _get_total_daily_calls(self) -> int:
        """获取当日总调用次数"""
        return sum(self.daily_call_count.values())
    
    def _increment_call_count(self, endpoint: APIEndpoint) -> None:
        """增加接口调用计数"""
        if endpoint not in self.daily_call_count:
            self.daily_call_count[endpoint] = 0
        self.daily_call_count[endpoint] += 1
    
    def _update_last_call_time(self, endpoint: APIEndpoint) -> None:
        """更新最后调用时间"""
        self.last_call_time[endpoint] = time.time()
    
    def _calculate_wait_time(self, endpoint: APIEndpoint) -> float:
        """计算需要等待的时间"""
        current_time = time.time()
        last_call = self.last_call_time.get(endpoint, 0)
        
        # 基础间隔
        wait_time = max(0, last_call + self.current_interval - current_time)
        
        # 如果接近每日限制，增加间隔
        total_calls = self._get_total_daily_calls()
        if total_calls > self.daily_limit * 0.8:  # 超过80%时增加间隔
            wait_time += 2.0
        
        return wait_time
    
    def _adjust_interval(self, success: bool) -> None:
        """动态调整调用间隔"""
        if success:
            # 成功调用，逐渐减少间隔
            self.error_count = 0
            self.current_interval = max(self.min_interval, self.current_interval * 0.9)
        else:
            # 失败调用，增加间隔
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.current_interval = min(self.max_interval, self.current_interval * 1.5)
                self.error_count = 0
        
        logger.debug("Interval adjusted", 
                    current_interval=self.current_interval,
                    error_count=self.error_count)
    
    async def acquire(self, endpoint: APIEndpoint) -> None:
        """获取调用许可"""
        # 检查是否需要重置每日计数
        if self._should_reset_daily_count():
            self._reset_daily_count()
        
        # 检查是否超过每日限制
        total_calls = self._get_total_daily_calls()
        if total_calls >= self.daily_limit:
            # 计算到下一个重置时间的等待时间
            now = datetime.utcnow()
            wait_seconds = (self.daily_reset_time - now).total_seconds()
            
            logger.warning("Daily limit exceeded", 
                          total_calls=total_calls,
                          daily_limit=self.daily_limit,
                          wait_seconds=wait_seconds)
            
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
                self._reset_daily_count()
        
        # 计算需要等待的时间
        wait_time = self._calculate_wait_time(endpoint)
        if wait_time > 0:
            logger.debug("Rate limiting", 
                        endpoint=endpoint.value,
                        wait_time=wait_time)
            await asyncio.sleep(wait_time)
        
        # 更新调用时间和计数
        self._update_last_call_time(endpoint)
        self._increment_call_count(endpoint)
        
        logger.debug("API call permitted", 
                    endpoint=endpoint.value,
                    total_calls=self._get_total_daily_calls())
    
    def report_success(self, endpoint: APIEndpoint) -> None:
        """报告调用成功"""
        self._adjust_interval(True)
        logger.debug("API call success", endpoint=endpoint.value)
    
    def report_error(self, endpoint: APIEndpoint, error: str) -> None:
        """报告调用失败"""
        self._adjust_interval(False)
        logger.warning("API call failed", 
                      endpoint=endpoint.value,
                      error=error)
    
    def get_status(self) -> Dict[str, Any]:
        """获取限制器状态"""
        return {
            "daily_limit": self.daily_limit,
            "total_calls_today": self._get_total_daily_calls(),
            "calls_remaining": max(0, self.daily_limit - self._get_total_daily_calls()),
            "current_interval": self.current_interval,
            "daily_reset_time": self.daily_reset_time.isoformat() if self.daily_reset_time else None,
            "endpoint_calls": self.daily_call_count.copy(),
            "error_count": self.error_count
        }


# 全局频率限制器实例
_rate_limiter: Optional[CJRateLimiter] = None


def get_rate_limiter() -> CJRateLimiter:
    """获取全局频率限制器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = CJRateLimiter()
    return _rate_limiter


async def rate_limited_call(endpoint: APIEndpoint, func, *args, **kwargs):
    """带频率限制的API调用装饰器"""
    limiter = get_rate_limiter()
    
    try:
        # 获取调用许可
        await limiter.acquire(endpoint)
        
        # 执行API调用
        result = await func(*args, **kwargs)
        
        # 报告成功
        limiter.report_success(endpoint)
        
        return result
        
    except Exception as e:
        # 报告失败
        limiter.report_error(endpoint, str(e))
        raise 