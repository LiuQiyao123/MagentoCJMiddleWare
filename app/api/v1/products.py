"""
产品API路由
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.product_sync import get_product_sync_service, ProductSyncService
from app.clients.cj_client import get_cj_client, CJClient
from app.utils.url_parser import extract_product_id_from_url, validate_cj_url
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


class ProductSyncSingleRequest(BaseModel):
    """单商品同步请求模型"""
    product_url: str = Field(..., description="CJ商品链接")
    category_id: Optional[int] = Field(None, description="Magento分类ID，可选")
    retail_price: float = Field(..., gt=0, description="在Magento中设置的零售价格")
    attribute_set_id: int = Field(..., description="在Magento中为Dropshipping商品配置的属性集ID")


class InventorySyncRequest(BaseModel):
    """库存同步请求模型"""
    product_ids: Optional[list] = Field(None, description="产品ID列表")


@router.post("/sync/single")
async def sync_single_product(
    request: ProductSyncSingleRequest,
    product_sync_service: ProductSyncService = Depends(get_product_sync_service)
):
    """同步单个CJ商品到Magento"""
    try:
        # 验证URL格式
        if not validate_cj_url(request.product_url):
            return {
                "success": False,
                "error": "无效的CJ商品链接",
                "error_code": "1001"
            }
        
        # 提取商品ID
        try:
            product_id = extract_product_id_from_url(request.product_url)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "1002"
            }
        
        # 同步商品
        result = await product_sync_service.sync_single_product(
            product_id=product_id,
            product_url=request.product_url,
            category_id=request.category_id,
            retail_price=request.retail_price,
            attribute_set_id=request.attribute_set_id
        )
        
        return {
            "success": result.get("success", True),
            "product_id": result.get("product_id"),
            "product_name": result.get("product_name"),
            "magento_product_id": result.get("magento_id"),
            "sku": result.get("sku"),
            "magento_url": result.get("magento_url"),
            "cj_data": result.get("cj_data"),
            "magento_data": result.get("magento_data"),
            "magento_result": result.get("magento_result"),
            "magento_error": result.get("magento_error"),
            "sync_duration_ms": result.get("sync_duration_ms"),
            "cached": result.get("cached", False)
        }
        
    except Exception as e:
        logger.error("单个商品同步失败", error=str(e), product_url=request.product_url)
        return {
            "success": False,
            "error": str(e),
            "error_code": "5001"
        }


@router.post("/sync/inventory")
async def sync_inventory(
    request: InventorySyncRequest,
    product_sync_service: ProductSyncService = Depends(get_product_sync_service)
):
    """同步库存信息"""
    try:
        result = await product_sync_service.sync_inventory(request.product_ids)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error("库存同步失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/status")
async def get_sync_status(
    task_id: Optional[str] = Query(None, description="任务ID")
):
    """获取同步状态"""
    try:
        # 这里应该实现获取同步状态的逻辑
        return {"status": "completed", "progress": 100}
    except Exception as e:
        logger.error("获取同步状态失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) 