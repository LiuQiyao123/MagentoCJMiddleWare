"""
产品API路由
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.product_sync import get_product_sync_service, ProductSyncService
from app.core.exceptions import APIException
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


class ProductSyncRequest(BaseModel):
    """产品同步请求模型"""
    category_id: Optional[str] = Field(None, description="CJ分类ID")
    keyword: Optional[str] = Field(None, description="搜索关键词")
    limit: int = Field(100, ge=1, le=1000, description="同步产品数量限制")


class InventorySyncRequest(BaseModel):
    """库存同步请求模型"""
    product_ids: Optional[list] = Field(None, description="指定产品ID列表，为空则同步所有产品")


class ProductSyncResponse(BaseModel):
    """产品同步响应模型"""
    success: bool = Field(description="是否成功")
    message: str = Field(description="响应消息")
    data: Dict[str, Any] = Field(description="同步结果数据")


@router.post("/sync/from-cj", response_model=ProductSyncResponse)
async def sync_products_from_cj(
    request: ProductSyncRequest,
    background_tasks: BackgroundTasks,
    product_sync_service: ProductSyncService = Depends(get_product_sync_service)
):
    """
    从CJ同步产品到Magento
    
    - **category_id**: CJ分类ID（可选）
    - **keyword**: 搜索关键词（可选）
    - **limit**: 同步产品数量限制（1-1000）
    """
    try:
        logger.info(
            "Starting product sync from CJ",
            category_id=request.category_id,
            keyword=request.keyword,
            limit=request.limit
        )
        
        # 如果数量较大，使用后台任务
        if request.limit > 50:
            background_tasks.add_task(
                _sync_products_background,
                product_sync_service,
                request.category_id,
                request.keyword,
                request.limit
            )
            
            return ProductSyncResponse(
                success=True,
                message="Product sync started in background",
                data={"status": "background_task_started", "limit": request.limit}
            )
        else:
            # 直接同步
            result = await product_sync_service.sync_products_from_cj(
                category_id=request.category_id,
                keyword=request.keyword,
                limit=request.limit
            )
            
            return ProductSyncResponse(
                success=True,
                message="Product sync completed successfully",
                data=result
            )
            
    except APIException as e:
        logger.error("Product sync API error", error=str(e))
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error("Unexpected error in product sync", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.post("/sync/inventory", response_model=ProductSyncResponse)
async def sync_inventory_from_cj(
    request: InventorySyncRequest,
    background_tasks: BackgroundTasks,
    product_sync_service: ProductSyncService = Depends(get_product_sync_service)
):
    """
    从CJ同步库存到Magento
    
    - **product_ids**: 指定产品ID列表，为空则同步所有产品
    """
    try:
        logger.info("Starting inventory sync from CJ", product_ids=request.product_ids)
        
        # 使用后台任务处理库存同步
        background_tasks.add_task(
            _sync_inventory_background,
            product_sync_service,
            request.product_ids
        )
        
        return ProductSyncResponse(
            success=True,
            message="Inventory sync started in background",
            data={"status": "background_task_started"}
        )
        
    except APIException as e:
        logger.error("Inventory sync API error", error=str(e))
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error("Unexpected error in inventory sync", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/sync/status")
async def get_sync_status():
    """
    获取同步状态
    """
    try:
        # 这里可以实现获取同步状态的逻辑
        # 例如从Redis或数据库获取正在进行的同步任务状态
        return {
            "success": True,
            "message": "Sync status retrieved successfully",
            "data": {
                "active_tasks": 0,
                "last_sync": None,
                "status": "idle"
            }
        }
    except Exception as e:
        logger.error("Error getting sync status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


async def _sync_products_background(
    product_sync_service: ProductSyncService,
    category_id: Optional[str],
    keyword: Optional[str],
    limit: int
):
    """后台产品同步任务"""
    try:
        logger.info("Background product sync started")
        
        result = await product_sync_service.sync_products_from_cj(
            category_id=category_id,
            keyword=keyword,
            limit=limit
        )
        
        logger.info("Background product sync completed", result=result)
        
    except Exception as e:
        logger.error("Background product sync failed", error=str(e))


async def _sync_inventory_background(
    product_sync_service: ProductSyncService,
    product_ids: Optional[list]
):
    """后台库存同步任务"""
    try:
        logger.info("Background inventory sync started")
        
        # 如果指定了产品ID，需要先获取对应的ProductMapping
        product_mappings = None
        if product_ids:
            # 这里需要实现根据产品ID获取ProductMapping的逻辑
            pass
        
        result = await product_sync_service.sync_inventory_from_cj(product_mappings)
        
        logger.info("Background inventory sync completed", result=result)
        
    except Exception as e:
        logger.error("Background inventory sync failed", error=str(e)) 