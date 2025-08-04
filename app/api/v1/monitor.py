"""
监控API端点
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
import structlog

from app.utils.rate_limiter import get_rate_limiter
from app.utils.token_manager import get_token_manager

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/monitor", tags=["监控"])


@router.get("/rate-limiter/status")
async def get_rate_limiter_status() -> Dict[str, Any]:
    """获取频率限制器状态"""
    try:
        limiter = get_rate_limiter()
        status = limiter.get_status()
        
        logger.info("Rate limiter status retrieved", status=status)
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error("Failed to get rate limiter status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get rate limiter status",
                "message": str(e)
            }
        )


@router.get("/token/status")
async def get_token_status() -> Dict[str, Any]:
    """获取Token状态"""
    try:
        token_manager = await get_token_manager()
        status = token_manager.get_token_status()
        
        logger.info("Token status retrieved", status=status)
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error("Failed to get token status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get token status",
                "message": str(e)
            }
        )


@router.post("/token/refresh")
async def refresh_token() -> Dict[str, Any]:
    """手动刷新Token"""
    try:
        token_manager = await get_token_manager()
        
        # 强制刷新token
        await token_manager._ensure_valid_token()
        
        status = token_manager.get_token_status()
        
        logger.info("Token refreshed manually", status=status)
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "data": status
        }
        
    except Exception as e:
        logger.error("Failed to refresh token", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to refresh token",
                "message": str(e)
            }
        )


@router.get("/system/status")
async def get_system_status() -> Dict[str, Any]:
    """获取系统整体状态"""
    try:
        # 获取频率限制器状态
        limiter = get_rate_limiter()
        rate_limiter_status = limiter.get_status()
        
        # 获取Token状态
        token_manager = await get_token_manager()
        token_status = token_manager.get_token_status()
        
        # 计算系统健康度
        system_health = "healthy"
        warnings = []
        
        # 检查频率限制
        total_calls = rate_limiter_status.get("total_calls_today", 0)
        daily_limit = rate_limiter_status.get("daily_limit", 1000)
        if total_calls > daily_limit * 0.8:
            system_health = "warning"
            warnings.append(f"API调用次数接近限制: {total_calls}/{daily_limit}")
        
        # 检查Token状态
        if not token_status.get("access_token_valid", False):
            system_health = "error"
            warnings.append("Access Token无效")
        
        if not token_status.get("refresh_token_valid", False):
            system_health = "warning"
            warnings.append("Refresh Token即将过期")
        
        status = {
            "system_health": system_health,
            "warnings": warnings,
            "rate_limiter": rate_limiter_status,
            "token": token_status,
            "timestamp": "2024-01-01T00:00:00Z"  # 这里应该使用实际时间
        }
        
        logger.info("System status retrieved", status=status)
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to get system status",
                "message": str(e)
            }
        ) 