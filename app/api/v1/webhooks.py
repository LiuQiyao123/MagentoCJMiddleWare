from fastapi import APIRouter, Header, HTTPException, Request, Depends
import structlog
from typing import Any, Dict, Optional

from app.config.settings import get_settings
from app.config.redis import get_redis_client

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def verify_signature(signature: str, payload: bytes, secret: str) -> bool:
    """简单的 HMAC-SHA256 签名验证，可按需替换"""
    import hmac
    import hashlib
    expected = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/magento/order")
async def magento_order_webhook(
    request: Request,
    x_magento_webhook_signature: Optional[str] = Header(None, alias="X-Magento-Webhook-Signature"),
    x_store_id: Optional[str] = Header("1", alias="X-Store-Id"),
):
    """接收 Magento 新订单 Webhook 并写入 Redis Stream"""
    settings = get_settings()
    raw_body = await request.body()

    # 验签（如果设置了密钥）
    if settings.MAGENTO_WEBHOOK_SECRET:
        if not x_magento_webhook_signature:
            raise HTTPException(status_code=400, detail="Missing signature header")
        if not await verify_signature(x_magento_webhook_signature, raw_body, settings.MAGENTO_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # 解析 JSON
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # 写入 Redis Stream
    try:
        async with get_redis_client() as redis:
            await redis.xadd(
                "stream:orders",
                {
                    "store_id": x_store_id,
                    "event": "order_created",
                    "payload": str(payload),  # 原样字符串化，消费端再解析
                },
                maxlen=10000,
                approximate=True,
            )
    except Exception as e:
        logger.error("Failed to write order event to Redis", error=str(e))
        raise HTTPException(status_code=500, detail="Internal queue error")

    logger.info("Received Magento order webhook", store_id=x_store_id)
    return {"success": True}
