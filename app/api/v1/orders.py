"""
订单API路由
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.order_sync import get_order_sync_service, OrderSyncService
from app.core.exceptions import APIException
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


class OrderSyncRequest(BaseModel):
    """订单同步请求模型"""
    hours_back: int = Field(24, ge=1, le=168, description="回溯小时数（1-168小时）")


class OrderSyncResponse(BaseModel):
    """订单同步响应模型"""
    success: bool = Field(description="是否成功")
    message: str = Field(description="响应消息")
    data: Dict[str, Any] = Field(description="同步结果数据")


@router.post("/sync/to-cj", response_model=OrderSyncResponse)
async def sync_orders_to_cj(
    request: OrderSyncRequest,
    background_tasks: BackgroundTasks,
    order_sync_service: OrderSyncService = Depends(get_order_sync_service)
):
    """
    同步Magento订单到CJ
    """
    try:
        logger.info("Starting order sync to CJ", extra={"hours_back": request.hours_back})
        
        # 使用后台任务处理订单同步
        background_tasks.add_task(
            _sync_orders_background,
            order_sync_service,
            request.hours_back
        )
        
        return OrderSyncResponse(
            success=True,
            message="Order sync started in background",
            data={"status": "background_task_started", "hours_back": request.hours_back}
        )
        
    except APIException as e:
        logger.error("Order sync API error", extra={"error": str(e)})
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error("Unexpected error in order sync", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


async def _sync_orders_background(
    order_sync_service: OrderSyncService,
    hours_back: int
):
    """后台订单同步任务"""
    try:
        logger.info("Background order sync started", extra={"hours_back": hours_back})
        
        result = await order_sync_service.sync_new_orders(hours_back=hours_back)
        
        logger.info("Background order sync completed", extra={"result": result})
        
    except Exception as e:
        logger.error("Background order sync failed", extra={"error": str(e)}) 