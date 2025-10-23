import asyncio
import json
import structlog
from typing import Dict, Any

from app.config.redis import get_redis_client
from app.gateways.factory import get_supplier_gateway
from app.models.order import OrderMapping, OrderStatus
from app.config.database import get_db
from sqlalchemy import insert
from datetime import datetime

logger = structlog.get_logger(__name__)

STREAM_KEY = "stream:orders"
GROUP = "order_workers"
CONSUMER = "worker-1"


async def ensure_group():
    async with get_redis_client() as redis:
        try:
            await redis.xgroup_create(name=STREAM_KEY, groupname=GROUP, id="0-0", mkstream=True)
        except Exception:
            # group may already exist
            pass


async def process_message(message_id: str, data: Dict[str, str]):
    store_id = data.get("store_id", "1")
    payload_str = data.get("payload", "{}")
    try:
        payload: Dict[str, Any] = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error("Invalid payload JSON", message_id=message_id)
        return

    # TODO: 根据 store_id 获取 Store 及其 supplier_type
    supplier_type = "cj"  # 临时使用 cj
    gateway = await get_supplier_gateway(supplier_type)

    try:
        cj_resp = await gateway.create_order(payload)  # 假设 payload 已是 supplier 所需格式
        cj_order_id = cj_resp.get("data", {}).get("orderId")

        if cj_order_id:
            # 写入 OrderMapping
            async with get_db() as session:
                stmt = insert(OrderMapping).values(
                    magento_order_id=str(payload.get("entity_id")),
                    magento_order_increment_id=payload.get("increment_id"),
                    cj_order_id=str(cj_order_id),
                    order_status=OrderStatus.PENDING,
                    created_at=datetime.utcnow(),
                    last_sync_at=datetime.utcnow(),
                )
                await session.execute(stmt)
                await session.commit()
            logger.info("CJ order created", cj_order_id=cj_order_id)
        else:
            logger.error("CJ create order failed", response=cj_resp)
    except Exception as e:
        logger.error("Error creating CJ order", error=str(e))
        raise


async def worker_loop():
    await ensure_group()
    async with get_redis_client() as redis:
        while True:
            resp = await redis.xreadgroup(GROUP, CONSUMER, streams={STREAM_KEY: ">"}, count=10, block=5000)
            if not resp:
                continue
            for _, messages in resp:
                for message_id, data in messages:
                    try:
                        await process_message(message_id, data)
                        await redis.xack(STREAM_KEY, GROUP, message_id)
                    except Exception:
                        # 失败消息不 ack，可配置死信或重试
                        pass
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(worker_loop())
