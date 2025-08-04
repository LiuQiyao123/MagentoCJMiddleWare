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
                message="Failed to initialize product sync service",
                error_code="SYNC_INIT_ERROR",
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
                message="Failed to sync products from CJ",
                error_code="CJ_SYNC_ERROR",
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
                message="Failed to sync inventory from CJ",
                error_code="INVENTORY_SYNC_ERROR",
                details={"error": str(e)}
            )
    
    async def sync_product_to_cj(self, magento_product_id: str) -> Dict[str, Any]:
        """将Magento产品同步到CJ（通常用于订单处理）"""
        # 这个方法主要用于订单处理时确保产品信息同步
        # 实际实现取决于具体的业务需求
        pass
    
    async def sync_single_product(self, product_id: str, product_url: Optional[str] = None) -> Dict[str, Any]:
        """
        同步单个CJ商品到Magento
        
        Args:
            product_id: CJ商品ID
            product_url: CJ商品链接（可选，用于日志记录）
            
        Returns:
            同步结果字典
        """
        import time
        start_time = time.time()
        
        try:
            logger.info("开始同步单个商品", product_id=product_id)
            
            # 1. 从CJ获取商品详情
            cj_product = await self.cj_client.get_product_detail(product_id)
            if not cj_product:
                raise ValueError(f"商品不存在: {product_id}")
            
            # 2. 转换为Magento格式
            magento_product_data = self._build_magento_product(cj_product)
            
            # 3. 创建Magento产品
            magento_result = await self.magento_client.create_product(magento_product_data)
            
            # 4. 计算同步耗时
            sync_duration = int((time.time() - start_time) * 1000)  # 转换为毫秒
            
            # 5. 记录同步日志
            await self._log_sync_result(
                product_id=product_id,
                success=True,
                magento_id=magento_result.get("id"),
                error_message=None,
                product_url=product_url,
                sync_duration=sync_duration
            )
            
            logger.info("单个商品同步成功", 
                       product_id=product_id, 
                       magento_id=magento_result.get("id"),
                       duration_ms=sync_duration)
            
            return {
                "product_name": cj_product.get("name"),
                "magento_id": magento_result.get("id"),
                "sku": magento_product_data.get("sku"),
                "magento_url": f"{self.settings.MAGENTO_BASE_URL}/admin/catalog/product/edit/id/{magento_result.get('id')}"
            }
            
        except Exception as e:
            error_message = str(e)
            sync_duration = int((time.time() - start_time) * 1000)
            
            logger.error("单个商品同步失败", 
                        product_id=product_id, 
                        error=error_message,
                        duration_ms=sync_duration)
            
            # 记录错误日志
            await self._log_sync_result(
                product_id=product_id,
                success=False,
                magento_id=None,
                error_message=error_message,
                product_url=product_url,
                sync_duration=sync_duration
            )
            
            raise e

    async def _log_sync_result(self, product_id: str, success: bool, 
                              magento_id: Optional[str], error_message: Optional[str],
                              product_url: Optional[str] = None, sync_duration: Optional[int] = None):
        """
        记录同步结果到数据库
        
        Args:
            product_id: CJ商品ID
            success: 是否成功
            magento_id: Magento产品ID
            error_message: 错误信息
            product_url: CJ商品链接
            sync_duration: 同步耗时(毫秒)
        """
        try:
            from app.models.sync_log import SyncLog
            from app.config.database import get_db
            
            # 获取数据库会话
            async with get_db() as db:
                # 创建日志记录
                sync_log = SyncLog(
                    product_id=product_id,
                    product_url=product_url,
                    success=success,
                    magento_id=magento_id,
                    error_message=error_message,
                    sync_duration=sync_duration
                )
                
                # 如果有错误，设置错误代码
                if not success and error_message:
                    if "商品不存在" in error_message:
                        sync_log.error_code = "2001"
                    elif "URL解析失败" in error_message:
                        sync_log.error_code = "1002"
                    elif "无效的CJ商品链接" in error_message:
                        sync_log.error_code = "1001"
                    else:
                        sync_log.error_code = "5001"
                
                # 保存到数据库
                db.add(sync_log)
                await db.commit()
                
                logger.info("同步日志已记录", 
                           log_id=sync_log.id,
                           product_id=product_id,
                           success=success)
                
        except Exception as e:
            logger.error("记录同步日志失败", error=str(e))
    
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