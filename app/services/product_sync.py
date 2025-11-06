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
from app.config.settings import get_settings

import httpx

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
            # 优先初始化CJ客户端（必须成功）
            self.cj_client = await get_cj_client()
            logger.info("CJ client initialized successfully")
            
            # 尝试初始化Magento客户端（允许失败）
            try:
                self.magento_client = await get_magento_client()
                logger.info("Magento client initialized successfully")
            except Exception as e:
                logger.warning("Magento client initialization failed, will retry later", error=str(e))
                self.magento_client = None
                
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
                
                # 严格遵守CJ API频率限制：Free用户每秒最多1次请求
                await asyncio.sleep(1.5)  # 等待1.5秒确保不超限
            
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
            magento_product = self._build_magento_product(product_data, variant_data, None)
            
            # 检查产品是否已存在映射
            async with get_db() as session:
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
            async with get_db() as session:
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
        variants: List[Dict[str, Any]],
        inventory: List[Dict[str, Any]],
        category_id: Optional[int],
        retail_price: float,
        attribute_set_id: int
    ) -> Dict[str, Any]:
        """构建Magento产品数据"""
        
        # 将库存信息按变体ID映射，方便查找
        inventory_map = {item['vid']: item['stock'] for item in inventory}

        # 单变体或无变体 -> 创建简单商品
        if not variants or len(variants) <= 1:
            variant = variants[0] if variants else {}
            stock = inventory_map.get(variant.get('vid'), 0)

            simple_product_payload = {
                "sku": variant.get('variantSku') or cj_product["productSku"],
                "name": cj_product.get("productNameEn") or cj_product.get("productName"),
                "price": retail_price,
                "status": 1, # 启用
                "visibility": 4, # 目录, 搜索
                "type_id": "simple",
                "attribute_set_id": attribute_set_id,
                "weight": variant.get('variantWeight') or cj_product.get("packingWeight", 0),
                "extension_attributes": {
                    "stock_item": {
                        "qty": stock,
                        "is_in_stock": stock > 0
                    }
                },
                "custom_attributes": [
                    {"attribute_code": "description", "value": cj_product.get("description", "")}
                ]
            }
            if category_id:
                simple_product_payload["category_links"] = [{"position": 0, "category_id": str(category_id)}]
            
            return simple_product_payload

        # 多变体 -> 返回可配置商品及其所有子项的数据结构
        else:
            # 1. 构建父可配置商品
            configurable_product_payload = {
                "sku": cj_product["productSku"],
                "name": cj_product.get("productNameEn") or cj_product.get("productName"),
                "attribute_set_id": attribute_set_id,
                "type_id": "configurable",
                "status": 1,
                "visibility": 4,
                "custom_attributes": [
                    {"attribute_code": "description", "value": cj_product.get("description", "")}
                ],
                "image_url": cj_product.get("productImage") # 传递图片URL
            }
            if category_id:
                configurable_product_payload["category_links"] = [{"position": 0, "category_id": str(category_id)}]
            
            # 2. 构建所有子商品 (简单商品)
            child_products = []
            for variant in variants:
                stock = inventory_map.get(variant.get('vid'), 0)
                child_product = {
                    "sku": variant.get('variantSku'),
                    "name": cj_product.get("productNameEn") or cj_product.get("productName"),
                    "price": retail_price, # 假设所有变体使用相同的零售价
                    "status": 1,
                    "visibility": 1, # 单独不可见
                    "type_id": "simple",
                    "attribute_set_id": attribute_set_id,
                    "weight": variant.get('variantWeight', 0),
                    "extension_attributes": {
                        "stock_item": {
                            "qty": stock,
                            "is_in_stock": stock > 0
                        }
                    },
                    "image_url": variant.get("variantImage") or cj_product.get("productImage"), # 传递图片URL
                    # TODO: 需要处理 `custom_attributes` 来设置颜色、尺寸等
                }
                child_products.append(child_product)

            return {
                "type": "configurable",
                "parent": configurable_product_payload,
                "children": child_products
            }

    async def _upload_magento_image(self, sku: str, image_url: str):
        """下载图片并上传到Magento"""
        if not self.magento_client:
            return
            
        try:
            logger.info("开始上传Magento图片", sku=sku, image_url=image_url)
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=30.0)
                response.raise_for_status()
                image_data = response.content

            import base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            await self.magento_client.add_product_media(
                sku=sku,
                image_content=encoded_image,
                image_name=image_url.split("/")[-1].split("?")[0] or f"{sku}.jpg",
                image_types=["image", "small_image", "thumbnail"]
            )
            logger.info("Magento图片上传成功", sku=sku)

        except Exception as e:
            logger.error("Magento图片上传失败", sku=sku, image_url=image_url, error=str(e))


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
                async with get_db() as session:
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
                
                # 严格遵守CJ API频率限制：Free用户每秒最多1次请求
                await asyncio.sleep(1.5)  # 等待1.5秒确保不超限
            
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
    
    async def sync_single_product(
        self, 
        product_id: str, 
        product_url: Optional[str] = None, 
        category_id: Optional[int] = None,
        retail_price: float = 0.0,
        attribute_set_id: int = 4
    ) -> Dict[str, Any]:
        """
        同步单个CJ商品到Magento
        
        Args:
            product_id: CJ商品ID
            product_url: CJ商品链接（可选，用于日志记录）
            category_id: Magento分类ID
            retail_price: 零售价
            attribute_set_id: Magento属性集ID
            
        Returns:
            同步结果字典
        """
        import time
        import json
        import os
        start_time = time.time()
        
        try:
            logger.info("开始同步单个商品", product_id=product_id)
            
            # 确保CJ客户端已初始化（必须成功）
            if not self.cj_client:
                await self.initialize()
            
            # 1. 并行从CJ获取商品详情、变体和库存
            logger.info("正在从CJ获取商品详情、变体和库存", product_id=product_id)
            results = await asyncio.gather(
                self.cj_client.get_product_detail(product_id),
                self.cj_client.get_product_variants(product_id),
                self.cj_client.get_product_inventory(product_id),
                return_exceptions=True
            )
            
            # 检查API调用结果
            cj_product_details, cj_variants, cj_inventory = results
            for result in results:
                if isinstance(result, Exception):
                    raise ProductSyncError(
                        message="Failed to fetch complete product data from CJ",
                        error_code="CJ_DATA_FETCH_ERROR",
                        details={"error": str(result), "product_id": product_id}
                    )
            
            if not cj_product_details or not cj_product_details.get("data"):
                raise ValueError(f"商品不存在或数据格式不正确: {product_id}")

            # 缓存CJ商品数据
            await self._cache_cj_product_data(product_id, cj_product_details, product_url)
            
            # 2. 转换为Magento格式
            logger.info("正在转换商品数据格式", product_id=product_id)
            # CJ API返回的是完整响应，需要提取data部分
            cj_product_data = cj_product_details.get("data", {})
            variants_data = cj_variants.get("data", [])
            inventory_data = cj_inventory.get("data", [])

            magento_product_data = self._build_magento_product(
                cj_product_data, 
                variants_data, 
                inventory_data, 
                category_id,
                retail_price,
                attribute_set_id
            )
            
            # 缓存Magento格式数据
            await self._cache_magento_product_data(product_id, magento_product_data)
            
            # 3. 尝试创建Magento产品（允许失败）
            magento_result = None
            magento_error = None
            
            if self.magento_client:
                try:
                    logger.info("正在创建Magento产品", product_id=product_id)

                    image_url_to_upload = None

                    # 如果是可配置商品，执行不同的创建流程
                    if magento_product_data.get("type") == "configurable":
                        # 1. 创建父商品
                        parent_payload = magento_product_data["parent"]
                        image_url_to_upload = parent_payload.pop("image_url", None)
                        parent_product = await self.magento_client.create_product(parent_payload)
                        parent_sku = parent_product.get("sku")
                        
                        # 2. 创建子商品
                        child_skus = []
                        for child_payload in magento_product_data["children"]:
                            # 子商品图片通常不单独上传，除非有特殊需求
                            child_payload.pop("image_url", None) 
                            child_product = await self.magento_client.create_product(child_payload)
                            child_skus.append(child_product.get("sku"))
                        
                        # 3. 关联子商品
                        await self.magento_client.link_simple_to_configurable(parent_sku, child_skus)
                        
                        magento_result = parent_product

                    elif magento_product_data:
                        image_url_to_upload = magento_product_data.pop("image_url", None)
                        magento_result = await self.magento_client.create_product(magento_product_data)

                    else:
                        raise ValueError("magento_product_data为空，无法创建产品")

                    # 上传图片
                    if magento_result and image_url_to_upload:
                        sku = magento_result.get("sku")
                        await self._upload_magento_image(sku, image_url_to_upload)

                    logger.info("Magento产品创建成功", product_id=product_id, magento_id=magento_result.get("id"))
                except Exception as e:
                    magento_error = str(e)
                    logger.warning("Magento产品创建失败，数据已缓存", product_id=product_id, error=magento_error)
            else:
                magento_error = "Magento客户端未初始化"
                logger.warning("Magento客户端未初始化，数据已缓存", product_id=product_id)
            
            # 4. 计算同步耗时
            sync_duration = int((time.time() - start_time) * 1000)  # 转换为毫秒
            
            # 5. 记录同步日志
            await self._log_sync_result(
                product_id=product_id,
                success=magento_result is not None,
                magento_id=magento_result.get("id") if magento_result else None,
                error_message=magento_error,
                product_url=product_url,
                sync_duration=sync_duration
            )
            
            # 6. 返回结果（包含CJ数据和Magento结果）
            result = {
                "success": magento_result is not None,
                "product_id": product_id,
                "product_name": cj_product_details.get("data", {}).get("productName", "未知商品"),
                "cj_data": {
                    "details": cj_product_details,
                    "variants": cj_variants,
                    "inventory": cj_inventory,
                },
                "magento_data": magento_product_data,
                "magento_result": magento_result,
                "magento_error": magento_error,
                "sync_duration_ms": sync_duration,
                "magento_id": magento_result.get("id") if magento_result else None,
                "sku": magento_result.get("sku") if magento_result else None,
                "cached": True
            }
            
            logger.info("商品同步处理完成", 
                       product_id=product_id, 
                       success=magento_result is not None,
                       magento_id=magento_result.get("id") if magento_result else None,
                       duration_ms=sync_duration)
            
            return result
            
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

    async def _cache_cj_product_data(self, product_id: str, cj_data: Dict[str, Any], product_url: Optional[str] = None) -> None:
        """缓存CJ商品数据"""
        try:
            import os
            import json
            
            # 创建缓存目录
            cache_dir = "cache/products"
            os.makedirs(cache_dir, exist_ok=True)
            
            # 缓存数据
            cache_data = {
                "product_id": product_id,
                "product_url": product_url,
                "cj_data": cj_data,
                "cached_at": datetime.utcnow().isoformat(),
                "data_source": "cj_api"
            }
            
            cache_file = f"{cache_dir}/cj_{product_id}.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info("CJ商品数据已缓存", product_id=product_id, cache_file=cache_file)
            
        except Exception as e:
            logger.error("缓存CJ商品数据失败", product_id=product_id, error=str(e))

    async def _cache_magento_product_data(self, product_id: str, magento_data: Dict[str, Any]) -> None:
        """缓存Magento格式商品数据"""
        try:
            import os
            import json
            
            # 创建缓存目录
            cache_dir = "cache/products"
            os.makedirs(cache_dir, exist_ok=True)
            
            # 缓存数据
            cache_data = {
                "product_id": product_id,
                "magento_data": magento_data,
                "cached_at": datetime.utcnow().isoformat(),
                "data_source": "magento_format"
            }
            
            cache_file = f"{cache_dir}/magento_{product_id}.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info("Magento格式商品数据已缓存", product_id=product_id, cache_file=cache_file)
            
        except Exception as e:
            logger.error("缓存Magento格式商品数据失败", product_id=product_id, error=str(e))


# 全局产品同步服务实例
_product_sync_service: Optional[ProductSyncService] = None


async def get_product_sync_service() -> ProductSyncService:
    """获取产品同步服务实例"""
    global _product_sync_service
    
    if _product_sync_service is None:
        _product_sync_service = ProductSyncService()
        await _product_sync_service.initialize()
    
    return _product_sync_service 