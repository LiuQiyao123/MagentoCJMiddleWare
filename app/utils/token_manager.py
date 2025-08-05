"""
CJ API Token管理器
"""
import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.token import TokenStorage
# 延迟导入以避免循环导入
# from app.clients.cj_client import CJClient
from app.core.exceptions import APIException

logger = structlog.get_logger(__name__)


@dataclass
class TokenInfo:
    """Token信息"""
    access_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenInfo':
        """从字典创建"""
        return cls(**data)


class CJTokenManager:
    """CJ API Token管理器"""
    
    def __init__(self):
        self.cj_client: Optional[Any] = None  # 使用Any避免循环导入
        self._token_info: Optional[TokenInfo] = None
        self._last_check_time = 0
        self._check_interval = 300  # 5分钟检查一次
        
        # Token有效期设置
        self.access_token_validity_days = 15
        self.refresh_token_validity_days = 180
        
        # 提前更新时间（天）
        self.access_token_advance_days = 1  # 提前1天更新access token
        self.refresh_token_advance_days = 7  # 提前7天更新refresh token
        
        logger.info("CJ Token Manager initialized")
    
    async def initialize(self) -> None:
        """初始化Token管理器"""
        if not self.cj_client:
            # 延迟导入以避免循环导入
            from app.clients.cj_client import CJClient
            self.cj_client = CJClient()
            await self.cj_client.initialize()
        
        # 从数据库加载token
        await self._load_token_from_db()
        
        logger.info("CJ Token Manager initialized successfully")
    
    async def close(self) -> None:
        """关闭Token管理器"""
        if self.cj_client:
            await self.cj_client.close()
            self.cj_client = None
    
    async def get_valid_token(self) -> str:
        """获取有效的access token"""
        current_time = time.time()
        
        # 检查是否需要检查token状态
        if current_time - self._last_check_time < self._check_interval:
            if self._token_info and self._is_access_token_valid():
                return self._token_info.access_token
        
        # 更新检查时间
        self._last_check_time = current_time
        
        # 检查并更新token
        await self._ensure_valid_token()
        
        if not self._token_info:
            raise APIException(
                message="No valid token available",
                error_code="TOKEN_NOT_AVAILABLE"
            )
        
        return self._token_info.access_token
    
    async def _ensure_valid_token(self) -> None:
        """确保token有效"""
        # 如果没有token信息，从数据库加载
        if not self._token_info:
            await self._load_token_from_db()
        
        # 如果仍然没有token，获取新token
        if not self._token_info:
            await self._get_new_token()
            return
        
        # 检查access token是否需要更新
        if self._should_update_access_token():
            await self._update_access_token()
        
        # 检查refresh token是否需要更新
        if self._should_update_refresh_token():
            await self._update_refresh_token()
    
    def _is_access_token_valid(self) -> bool:
        """检查access token是否有效"""
        if not self._token_info:
            return False
        
        now = datetime.now(timezone.utc)
        return now < self._token_info.access_token_expires_at
    
    def _is_refresh_token_valid(self) -> bool:
        """检查refresh token是否有效"""
        if not self._token_info:
            return False
        
        now = datetime.now(timezone.utc)
        return now < self._token_info.refresh_token_expires_at
    
    def _should_update_access_token(self) -> bool:
        """检查是否需要更新access token"""
        if not self._token_info:
            return True
        
        now = datetime.now(timezone.utc)
        advance_time = self._token_info.access_token_expires_at - timedelta(days=self.access_token_advance_days)
        return now >= advance_time
    
    def _should_update_refresh_token(self) -> bool:
        """检查是否需要更新refresh token"""
        if not self._token_info:
            return True
        
        now = datetime.now(timezone.utc)
        advance_time = self._token_info.refresh_token_expires_at - timedelta(days=self.refresh_token_advance_days)
        return now >= advance_time
    
    async def _get_new_token(self) -> None:
        """获取新的token"""
        logger.info("Getting new CJ token...")
        
        try:
            # 使用CJ客户端获取新token
            access_token = await self.cj_client._get_access_token()
            
            # 创建token信息
            now = datetime.now(timezone.utc)
            self._token_info = TokenInfo(
                access_token=access_token,
                refresh_token=self.cj_client._refresh_token,
                access_token_expires_at=self.cj_client._token_expires_at,
                refresh_token_expires_at=now + timedelta(days=self.refresh_token_validity_days),
                created_at=now,
                updated_at=now
            )
            
            # 保存到数据库
            await self._save_token_to_db()
            
            logger.info("New token obtained successfully")
            
        except Exception as e:
            logger.error("Failed to get new token", error=str(e))
            raise APIException(
                message="Failed to get new token",
                error_code="TOKEN_ACQUISITION_FAILED",
                details={"error": str(e)}
            )
    
    async def _update_access_token(self) -> None:
        """更新access token"""
        logger.info("Updating access token...")
        
        try:
            if not self._is_refresh_token_valid():
                logger.warning("Refresh token expired, getting new token")
                await self._get_new_token()
                return
            
            # 使用refresh token更新access token
            access_token = await self.cj_client._refresh_access_token()
            
            # 更新token信息
            now = datetime.now(timezone.utc)
            self._token_info.access_token = access_token
            self._token_info.access_token_expires_at = self.cj_client._token_expires_at
            self._token_info.updated_at = now
            
            # 如果refresh token也更新了
            if self.cj_client._refresh_token != self._token_info.refresh_token:
                self._token_info.refresh_token = self.cj_client._refresh_token
                self._token_info.refresh_token_expires_at = now + timedelta(days=self.refresh_token_validity_days)
            
            # 保存到数据库
            await self._save_token_to_db()
            
            logger.info("Access token updated successfully")
            
        except Exception as e:
            logger.error("Failed to update access token", error=str(e))
            # 如果refresh失败，获取新token
            await self._get_new_token()
    
    async def _update_refresh_token(self) -> None:
        """更新refresh token"""
        logger.info("Updating refresh token...")
        
        try:
            # 获取新token（这会同时更新access token和refresh token）
            await self._get_new_token()
            
        except Exception as e:
            logger.error("Failed to update refresh token", error=str(e))
            raise APIException(
                message="Failed to update refresh token",
                error_code="REFRESH_TOKEN_UPDATE_FAILED",
                details={"error": str(e)}
            )
    
    async def _load_token_from_db(self) -> None:
        """从数据库加载token"""
        try:
            async for session in get_db():
                stmt = select(TokenStorage).where(TokenStorage.provider == "cj")
                result = await session.execute(stmt)
                token_record = result.scalar_one_or_none()
                
                if token_record:
                    # 解析token数据
                    token_data = json.loads(token_record.token_data)
                    self._token_info = TokenInfo.from_dict(token_data)
                    
                    logger.info("Token loaded from database")
                else:
                    logger.info("No token found in database")
                
                break
                
        except Exception as e:
            logger.error("Failed to load token from database", error=str(e))
            self._token_info = None
    
    async def _save_token_to_db(self) -> None:
        """保存token到数据库"""
        if not self._token_info:
            return
        
        try:
            async for session in get_db():
                # 检查是否已存在记录
                stmt = select(TokenStorage).where(TokenStorage.provider == "cj")
                result = await session.execute(stmt)
                token_record = result.scalar_one_or_none()
                
                if token_record:
                    # 更新现有记录
                    stmt = update(TokenStorage).where(
                        TokenStorage.provider == "cj"
                    ).values(
                        token_data=json.dumps(self._token_info.to_dict()),
                        updated_at=datetime.now(timezone.utc)
                    )
                    await session.execute(stmt)
                else:
                    # 创建新记录
                    token_record = TokenStorage(
                        provider="cj",
                        token_data=json.dumps(self._token_info.to_dict()),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    session.add(token_record)
                
                await session.commit()
                logger.info("Token saved to database")
                break
                
        except Exception as e:
            logger.error("Failed to save token to database", error=str(e))
    
    def get_token_status(self) -> Dict[str, Any]:
        """获取token状态"""
        if not self._token_info:
            return {
                "has_token": False,
                "access_token_valid": False,
                "refresh_token_valid": False
            }
        
        now = datetime.now(timezone.utc)
        
        return {
            "has_token": True,
            "access_token_valid": self._is_access_token_valid(),
            "refresh_token_valid": self._is_refresh_token_valid(),
            "access_token_expires_at": self._token_info.access_token_expires_at.isoformat(),
            "refresh_token_expires_at": self._token_info.refresh_token_expires_at.isoformat(),
            "created_at": self._token_info.created_at.isoformat(),
            "updated_at": self._token_info.updated_at.isoformat(),
            "access_token_preview": self._token_info.access_token[:10] + "...",
            "refresh_token_preview": self._token_info.refresh_token[:10] + "..."
        }


# 全局Token管理器实例
_token_manager: Optional[CJTokenManager] = None


async def get_token_manager() -> CJTokenManager:
    """获取全局Token管理器实例"""
    global _token_manager
    if _token_manager is None:
        _token_manager = CJTokenManager()
        await _token_manager.initialize()
    return _token_manager


async def close_token_manager() -> None:
    """关闭全局Token管理器"""
    global _token_manager
    if _token_manager:
        await _token_manager.close()
        _token_manager = None 