from fastapi import APIRouter, HTTPException
import structlog

from app.clients.magento_client import get_magento_client, MagentoAPIError

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/", summary="获取Magento分类树")
async def list_categories():
    """获取 Magento 分类完整树，直接透传 Magento API 响应。"""
    try:
        client = await get_magento_client()
        categories = await client.get_categories()
        return categories
    except MagentoAPIError as e:
        logger.error("Failed to fetch categories", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
