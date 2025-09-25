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
        logger.info("Starting order sync to CJ", hours_back=request.hours_back)
        
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
        logger.error("Order sync API error", error=str(e))
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        logger.error("Unexpected error in order sync", error=str(e))
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
        logger.info("Background order sync started", hours_back=hours_back)
        
        result = await order_sync_service.sync_new_orders(hours_back=hours_back)
        
        logger.info("Background order sync completed", result=result)
        
    except Exception as e:
        logger.error("Background order sync failed", error=str(e))


@router.get("/tracking/{order_id}")
async def get_order_tracking(
    order_id: str,
    order_sync_service: OrderSyncService = Depends(get_order_sync_service)
):
    """获取订单跟踪信息"""
    try:
        # 确保服务已初始化
        if not order_sync_service.cj_client:
            await order_sync_service.initialize()
        
        # 从CJ获取订单详情
        cj_order = await order_sync_service.cj_client.get_order_detail(order_id)
        
        # 获取跟踪信息
        tracking_info = await order_sync_service.cj_client.get_tracking_info(order_id)
        
        return {
            "success": True,
            "order_id": order_id,
            "cj_order": cj_order,
            "tracking_info": tracking_info,
            "cached": True
        }
        
    except Exception as e:
        logger.error("获取订单跟踪信息失败", error=str(e), order_id=order_id)
        return {
            "success": False,
            "error": str(e),
            "error_code": "5001"
        } 