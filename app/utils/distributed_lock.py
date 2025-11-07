import asyncio
import time
import uuid
from typing import Optional

import structlog
from redis.asyncio import Redis as AsyncRedis

from app.config.redis import get_redis_client

logger = structlog.get_logger(__name__)

class AsyncDistributedLock:
    """
    An asynchronous distributed lock using Redis.

    This lock is designed to be used with `async with`.
    It is not re-entrant.
    """

    def __init__(
        self,
        lock_key: str,
        timeout: int = 10,  # Lock timeout in seconds
        blocking_timeout: int = 5,  # How long to wait to acquire the lock
    ):
        """
        Initialize the distributed lock.

        :param lock_key: The key for the lock in Redis.
        :param timeout: The lock's expiry time in seconds.
        :param blocking_timeout: Max time in seconds to wait to acquire the lock.
        """
        self.redis_client: AsyncRedis = get_redis_client()
        self.lock_key = f"lock:{lock_key}"
        self.timeout = timeout
        self.blocking_timeout = blocking_timeout
        self.lock_value = str(uuid.uuid4())
        self._acquired = False

    async def __aenter__(self):
        """Acquire the lock."""
        start_time = time.monotonic()
        while time.monotonic() - start_time < self.blocking_timeout:
            if await self.redis_client.set(
                self.lock_key, self.lock_value, ex=self.timeout, nx=True
            ):
                self._acquired = True
                logger.debug("Distributed lock acquired", lock_key=self.lock_key)
                return self
            await asyncio.sleep(0.1)  # Wait a bit before retrying

        raise TimeoutError(f"Could not acquire lock for {self.lock_key} within {self.blocking_timeout}s")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release the lock."""
        if self._acquired:
            # Use a Lua script to ensure we only delete the lock if we own it.
            # This prevents a process that was slow from deleting a lock
            # that has been acquired by another process.
            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            try:
                await self.redis_client.eval(script, 1, self.lock_key, self.lock_value)
                logger.debug("Distributed lock released", lock_key=self.lock_key)
            except Exception:
                logger.exception("Failed to release distributed lock", lock_key=self.lock_key)
            finally:
                self._acquired = False
