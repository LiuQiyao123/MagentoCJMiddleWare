"""
产品同步服务
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.cj_client import get_cj_client, CJClient
from app.clients.magento_client import get_magento_client, MagentoClient
from app.config.database import get_db
from app.models.product import ProductMapping, SyncStatus
from app.models.sync_log import SyncLog, SyncType, SyncStatus as LogSyncStatus
from app.core.exceptions import APIException

logger = structlog.get_logger(__name__)


class ProductSyncError(APIException):
    """产品同步异常"""
    pass


class ProductSyncService:
    """产品同步服务"""
    
    def __init__(self):
        self.cj_client: Optional[CJClient] = None
        self.magento_client: Optional[MagentoClient] = None
        
    async def initialize(self) -> None:
        """初始化服务"""
        try:
            self.cj_client = await get_cj_client()
            self.magento_client = await get_magento_client()
            logger.info("Product sync service initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize product sync service", error=str(e))
            raise ProductSyncError(
                error_code="SYNC_INIT_ERROR",
                message="Failed to initialize product sync service",
                details={"error": str(e)}
            )
    
    async def sync_products_from_cj(
        self,
        category_id: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """从CJ同步产品到Magento"""
        if not self.cj_client or not self.magento_client:
            await self.initialize()
            
        sync_result = {
            "total_processed": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # 搜索CJ产品
            page = 1
            page_size = 20
            processed_count = 0
            
            while processed_count < limit:
                logger.info(f"Fetching CJ products page {page}")
                
                cj_response = await self.cj_client.search_products(
                    keyword=keyword,
                    category_id=category_id,
                    page=page,
                    page_size=page_size
                )
                
                products = cj_response.get("data", {}).get("list", [])
                
                if not products:
                    break
                
                # 处理每个产品
                for product in products:
                    if processed_count >= limit:
                        break
                        
                    try:
                        await self._sync_single_product_from_cj(product)
                        sync_result["created"] += 1
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(
                            "Failed to sync product from CJ",
                            product_id=product.get("pid"),
                            error=str(e)
                        )
                        sync_result["failed"] += 1
                        sync_result["errors"].append({
                            "product_id": product.get("pid"),
                            "error": str(e)
                        })
                
                sync_result["total_processed"] = processed_count
                
                # 如果产品数量少于页面大小，说明已经是最后一页
                if len(products) < page_size:
                    break
                    
                page += 1
                
                # 添加延迟避免API限制
                await asyncio.sleep(0.5)
            
            logger.info("CJ product sync completed", result=sync_result)
            return sync_result
            
        except Exception as e:
            logger.error("CJ product sync failed", error=str(e))
            raise ProductSyncError(
                error_code="CJ_SYNC_ERROR",
                message="Failed to sync products from CJ",
                details={"error": str(e)}
            )
    
    async def _sync_single_product_from_cj(self, cj_product: Dict[str, Any]) -> None:
        """同步单个CJ产品到Magento"""
        product_id = cj_product["pid"]
        
        try:
            # 获取产品详情和变体
            product_detail = await self.cj_client.get_product_detail(product_id)
            variants = await self.cj_client.get_product_variants(product_id)
            
            product_data = product_detail.get("data", {})
            variant_data = variants.get("data", {}).get("list", [])
            
            # 构造Magento产品数据
            magento_product = self._build_magento_product(product_data, variant_data)
            
            # 检查产品是否已存在映射
            async for session in get_db():
                stmt = select(ProductMapping).where(
                    ProductMapping.cj_product_id == product_id
                )
                result = await session.execute(stmt)
                existing_mapping = result.scalar_one_or_none()
                
                if existing_mapping:
                    # 更新现有产品
                    await self.magento_client.update_product(
                        existing_mapping.magento_product_id,
                        magento_product
                    )
                    
                    # 更新映射状态
                    await session.execute(
                        update(ProductMapping)
                        .where(ProductMapping.id == existing_mapping.id)
                        .values(
                            sync_status=SyncStatus.SYNCED,
                            last_sync_at=datetime.utcnow()
                        )
                    )
                else:
                    # 创建新产品
                    magento_response = await self.magento_client.create_product(magento_product)
                    magento_product_id = magento_response.get("id")
                    
                    # 创建产品映射
                    mapping = ProductMapping(
                        magento_product_id=str(magento_product_id),
                        magento_sku=magento_product["sku"],
                        cj_product_id=product_id,
                        cj_variant_id=variant_data[0]["vid"] if variant_data else None,
                        sync_status=SyncStatus.SYNCED,
                        last_sync_at=datetime.utcnow()
                    )
                    
                    session.add(mapping)
                
                await session.commit()
                
                # 记录同步日志
                await self._log_sync_operation(
                    session,
                    SyncType.PRODUCT_SYNC,
                    LogSyncStatus.SUCCESS,
                    f"Synced product {product_id} from CJ to Magento"
                )
                
        except Exception as e:
            # 记录失败日志
            async for session in get_db():
                await self._log_sync_operation(
                    session,
                    SyncType.PRODUCT_SYNC,
                    LogSyncStatus.FAILED,
                    f"Failed to sync product {product_id}: {str(e)}"
                )
                await session.commit()
            raise
    
    def _build_magento_product(
        self,
        cj_product: Dict[str, Any],
        variants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """构建Magento产品数据"""
        
        # 基础产品信息
        magento_product = {
            "sku": f"CJ_{cj_product['pid']}",
            "name": cj_product.get("productName", ""),
            "price": cj_product.get("sellPrice", 0),
            "status": 1,  # 启用
            "visibility": 4,  # 目录和搜索可见
            "type_id": "simple",
            "attribute_set_id": 4,  # 默认属性集
            "weight": cj_product.get("productWeight", 0),
            "extension_attributes": {},
            "custom_attributes": [
                {
                    "attribute_code": "description",
                    "value": cj_product.get("description", "")
                },
                {
                    "attribute_code": "short_description", 
                    "value": cj_product.get("productName", "")
                },
                {
                    "attribute_code": "meta_title",
                    "value": cj_product.get("productName", "")
                },
                {
                    "attribute_code": "cj_product_id",
                    "value": cj_product["pid"]
                }
            ]
        }
        
        # 添加产品图片
        if cj_product.get("productImage"):
            magento_product["media_gallery_entries"] = [
                {
                    "media_type": "image",
                    "label": "Product Image",
                    "position": 1,
                    "disabled": False,
                    "types": ["image", "small_image", "thumbnail"],
                    "file": cj_product["productImage"]
                }
            ]
        
        # 处理变体（如果有多个变体，创建为可配置产品）
        if len(variants) > 1:
            magento_product["type_id"] = "configurable"
            # 这里需要根据实际需求处理可配置产品的变体
            
        return magento_product
    
    async def sync_inventory_from_cj(self, product_mappings: Optional[List[ProductMapping]] = None) -> Dict[str, Any]:
        """从CJ同步库存到Magento"""
        if not self.cj_client or not self.magento_client:
            await self.initialize()
            
        sync_result = {
            "total_processed": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # 如果没有指定产品映射，获取所有已同步的产品
            if not product_mappings:
                async for session in get_db():
                    stmt = select(ProductMapping).where(
                        ProductMapping.sync_status == SyncStatus.SYNCED
                    )
                    result = await session.execute(stmt)
                    product_mappings = result.scalars().all()
            
            # 同步每个产品的库存
            for mapping in product_mappings:
                try:
                    # 获取CJ库存信息
                    inventory_response = await self.cj_client.get_product_inventory(
                        mapping.cj_product_id,
                        mapping.cj_variant_id
                    )
                    
                    inventory_data = inventory_response.get("data", {})
                    stock_qty = inventory_data.get("stock", 0)
                    
                    # 更新Magento库存
                    await self.magento_client.update_stock(
                        mapping.magento_sku,
                        stock_qty,
                        stock_qty > 0  # 如果库存大于0则设为有货
                    )
                    
                    sync_result["updated"] += 1
                    
                except Exception as e:
                    logger.error(
                        "Failed to sync inventory for product",
                        product_id=mapping.cj_product_id,
                        error=str(e)
                    )
                    sync_result["failed"] += 1
                    sync_result["errors"].append({
                        "product_id": mapping.cj_product_id,
                        "error": str(e)
                    })
                
                sync_result["total_processed"] += 1
                
                # 添加延迟避免API限制
                await asyncio.sleep(0.2)
            
            logger.info("Inventory sync completed", result=sync_result)
            return sync_result
            
        except Exception as e:
            logger.error("Inventory sync failed", error=str(e))
            raise ProductSyncError(
                error_code="INVENTORY_SYNC_ERROR",
                message="Failed to sync inventory from CJ",
                details={"error": str(e)}
            )
    
    async def sync_product_to_cj(self, magento_product_id: str) -> Dict[str, Any]:
        """将Magento产品同步到CJ（通常用于订单处理）"""
        # 这个方法主要用于订单处理时确保产品信息同步
        # 实际实现取决于具体的业务需求
        pass
    
    async def _log_sync_operation(
        self,
        session: AsyncSession,
        sync_type: SyncType,
        status: LogSyncStatus,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录同步操作日志"""
        log_entry = SyncLog(
            sync_type=sync_type,
            status=status,
            message=message,
            details=details or {},
            created_at=datetime.utcnow()
        )
        
        session.add(log_entry)


# 全局产品同步服务实例
_product_sync_service: Optional[ProductSyncService] = None


async def get_product_sync_service() -> ProductSyncService:
    """获取产品同步服务实例"""
    global _product_sync_service
    
    if _product_sync_service is None:
        _product_sync_service = ProductSyncService()
        await _product_sync_service.initialize()
    
    return _product_sync_service 