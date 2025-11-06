"""
订单同步服务
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.cj_client import get_cj_client, CJClient, CJShippingAddress
from app.clients.magento_client import get_magento_client, MagentoClient
from app.config.database import get_db
from app.models.order import OrderMapping, OrderStatus
from app.models.product import ProductMapping, SyncStatus
from app.models.sync_log import SyncLog, SyncType, SyncStatus as LogSyncStatus
from app.core.exceptions import APIException
from app.config.settings import get_settings
from app.utils.country_codes import is_valid_country_code

logger = structlog.get_logger(__name__)
settings = get_settings()


class OrderSyncError(APIException):
    """订单同步异常"""
    pass


class OrderSyncService:
    """订单同步服务"""
    
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
                
            logger.info("Order sync service initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize order sync service", error=str(e))
            raise OrderSyncError(
                error_code="ORDER_SYNC_INIT_ERROR",
                message="Failed to initialize order sync service",
                details={"error": str(e)}
            )
    
    async def sync_new_orders(self, hours_back: int = 24) -> Dict[str, Any]:
        """同步新订单到CJ"""
        if not self.cj_client or not self.magento_client:
            await self.initialize()
            
        sync_result = {
            "total_processed": 0,
            "created": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # 计算时间范围
            since_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # 获取Magento新订单
            search_criteria = {
                "filterGroups[0][filters][0][field]": "created_at",
                "filterGroups[0][filters][0][value]": since_time.strftime("%Y-%m-%d %H:%M:%S"),
                "filterGroups[0][filters][0][conditionType]": "gt",
                "filterGroups[1][filters][0][field]": "status",
                "filterGroups[1][filters][0][value]": "processing",
                "filterGroups[1][filters][0][conditionType]": "eq"
            }
            
            orders_response = await self.magento_client.get_orders(
                page=1,
                page_size=50,
                search_criteria=search_criteria
            )
            
            orders = orders_response.get("items", [])
            
            for order in orders:
                try:
                    # 检查订单是否已经同步
                    async for session in get_db():
                        stmt = select(OrderMapping).where(
                            OrderMapping.magento_order_id == str(order["entity_id"])
                        )
                        result = await session.execute(stmt)
                        existing_mapping = result.scalar_one_or_none()
                        
                        if existing_mapping:
                            logger.info(f"Order {order['increment_id']} already synced, skipping")
                            continue
                        
                        # 同步订单到CJ
                        await self._sync_single_order_to_cj(order)
                        sync_result["created"] += 1
                        
                except Exception as e:
                    logger.error(
                        "Failed to sync order to CJ",
                        order_id=order.get("increment_id"),
                        error=str(e)
                    )
                    sync_result["failed"] += 1
                    sync_result["errors"].append({
                        "order_id": order.get("increment_id"),
                        "error": str(e)
                    })
                
                sync_result["total_processed"] += 1
                
                # 添加延迟避免API限制
                await asyncio.sleep(1)
            
            logger.info("Order sync completed", result=sync_result)
            return sync_result
            
        except Exception as e:
            logger.error("Order sync failed", error=str(e))
            raise OrderSyncError(
                error_code="ORDER_SYNC_ERROR",
                message="Failed to sync orders to CJ",
                details={"error": str(e)}
            )
    
    async def _sync_single_order_to_cj(self, magento_order: Dict[str, Any]) -> None:
        """同步单个订单到CJ"""
        order_id = magento_order["entity_id"]
        order_increment_id = magento_order["increment_id"]
        
        try:
            # 构建CJ订单数据
            cj_order_data, unmapped_skus = await self._build_cj_order(magento_order)

            # 如果存在未映射的SKU，则将订单标记为需要人工审核
            if unmapped_skus:
                await self._mark_order_for_manual_review(
                    order_id, order_increment_id, unmapped_skus
                )
                raise OrderSyncError(
                    error_code="UNMAPPED_SKUS_FOUND",
                    message=f"Order {order_increment_id} has unmapped SKUs.",
                    details={"unmapped_skus": unmapped_skus},
                )

            # 创建CJ订单
            cj_response = await self.cj_client.create_order(cj_order_data)
            cj_order_id = cj_response.get("data", {}).get("orderId")
            
            if not cj_order_id:
                raise OrderSyncError(
                    error_code="CJ_ORDER_CREATE_ERROR",
                    message="Failed to create CJ order",
                    details={"cj_response": cj_response}
                )
            
            # 创建订单映射
            async for session in get_db():
                mapping = OrderMapping(
                    magento_order_id=str(order_id),
                    magento_order_increment_id=order_increment_id,
                    cj_order_id=str(cj_order_id),
                    order_status=OrderStatus.PENDING,
                    created_at=datetime.utcnow(),
                    last_sync_at=datetime.utcnow()
                )
                
                session.add(mapping)
                await session.commit()
                
                # 记录同步日志
                await self._log_sync_operation(
                    session,
                    SyncType.ORDER_SYNC,
                    LogSyncStatus.SUCCESS,
                    f"Synced order {order_increment_id} to CJ (CJ Order ID: {cj_order_id})"
                )
                
                logger.info(
                    "Order synced to CJ successfully",
                    magento_order_id=order_increment_id,
                    cj_order_id=cj_order_id
                )
                
        except Exception as e:
            # 记录失败日志
            async for session in get_db():
                await self._log_sync_operation(
                    session,
                    SyncType.ORDER_SYNC,
                    LogSyncStatus.FAILED,
                    f"Failed to sync order {order_increment_id}: {str(e)}"
                )
                await session.commit()
            raise
    
    async def _build_cj_order(self, magento_order: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """构建CJ订单数据"""
        order_items = []
        unmapped_skus = []
        
        # 处理订单项
        for item in magento_order.get("items", []):
            if item.get("product_type") == "simple":
                # 查找产品映射
                async for session in get_db():
                    stmt = select(ProductMapping).where(
                        ProductMapping.magento_sku == item["sku"]
                    )
                    result = await session.execute(stmt)
                    product_mapping = result.scalar_one_or_none()
                    
                    if product_mapping:
                        order_items.append({
                            "vid": product_mapping.cj_variant_id,
                            "quantity": int(item["qty_ordered"]),
                            # "shippingMethod": "CJ_STANDARD"  # 默认物流方式 - 将被替换
                        })
                    else:
                        logger.warning(
                            "Product mapping not found for SKU",
                            sku=item["sku"],
                            order_id=magento_order["increment_id"]
                        )
                        unmapped_skus.append(item["sku"])
        
        if not order_items:
            raise OrderSyncError(
                error_code="NO_MAPPED_PRODUCTS",
                message="No mapped products found in order",
                details={"order_id": magento_order["increment_id"]}
            )
        
        # 构建收货地址
        shipping_address = magento_order.get("extension_attributes", {}).get("shipping_assignments", [{}])[0].get("shipping", {}).get("address", {})
        
        if not shipping_address:
            shipping_address = magento_order.get("billing_address", {})

        # 动态获取物流方式
        chosen_shipping_method = await self._get_optimal_shipping_method(
            order_items, shipping_address
        )

        # 为所有订单项设置选定的物流方式
        for item in order_items:
            item["shippingMethod"] = chosen_shipping_method
        
        cj_order = {
            "orderNumber": magento_order["increment_id"],
            "shippingAddress": {
                "firstName": shipping_address.get("firstname", ""),
                "lastName": shipping_address.get("lastname", ""),
                "company": shipping_address.get("company", ""),
                "address1": shipping_address.get("street", [""])[0] if shipping_address.get("street") else "",
                "address2": shipping_address.get("street", ["", ""])[1] if len(shipping_address.get("street", [])) > 1 else "",
                "city": shipping_address.get("city", ""),
                "state": shipping_address.get("region", ""),
                "zip": shipping_address.get("postcode", ""),
                "country": shipping_address.get("country_id", ""),
                "phone": shipping_address.get("telephone", ""),
                "email": magento_order.get("customer_email", "")
            },
            "products": order_items,
            "remark": f"Magento Order: {magento_order['increment_id']}"
        }
        
        return cj_order, unmapped_skus

    async def _mark_order_for_manual_review(
        self, magento_order_id: str, magento_order_increment_id: str, unmapped_skus: List[str]
    ):
        """将订单标记为需要人工审核"""
        async for session in get_db():
            try:
                # 检查是否已存在记录
                stmt = select(OrderMapping).where(
                    OrderMapping.magento_order_id == str(magento_order_id)
                )
                result = await session.execute(stmt)
                existing_mapping = result.scalar_one_or_none()

                if existing_mapping:
                    logger.info("Order mapping already exists for manual review.", order_id=magento_order_increment_id)
                    return

                # 创建新的订单映射记录
                note = f"Failed to sync due to unmapped SKUs: {', '.join(unmapped_skus)}"
                mapping = OrderMapping(
                    magento_order_id=str(magento_order_id),
                    magento_order_increment_id=magento_order_increment_id,
                    cj_order_id=None,  # 没有CJ订单ID
                    order_status=OrderStatus.MANUAL_REVIEW_REQUIRED,
                    notes=note,
                    created_at=datetime.utcnow(),
                    last_sync_at=datetime.utcnow(),
                )

                session.add(mapping)
                await session.commit()
                logger.warning(
                    "Order marked for manual review due to unmapped SKUs.",
                    order_id=magento_order_increment_id,
                    unmapped_skus=unmapped_skus,
                )
            except Exception as e:
                logger.error("Failed to mark order for manual review", order_id=magento_order_increment_id, error=str(e))
                await session.rollback()
            finally:
                await session.close()


    async def _get_optimal_shipping_method(
        self, order_items: List[Dict[str, Any]], shipping_address: Dict[str, Any]
    ) -> str:
        """获取最优物流方式"""
        country_code = shipping_address.get("country_id", "")
        if not is_valid_country_code(country_code):
            raise OrderSyncError(
                error_code="INVALID_COUNTRY_CODE",
                message=f"The destination country code '{country_code}' is not supported by CJ.",
                details={"country_code": country_code},
            )

        # 准备CJ运费计算API所需参数
        products_for_shipping = [
            {"vid": item["vid"], "quantity": item["quantity"]} for item in order_items
        ]
        province = shipping_address.get("region", "")

        # 调用CJ API获取可用物流选项
        shipping_options_response = await self.cj_client.get_shipping_cost(
            products=products_for_shipping,
            country_code=country_code,
            province=province,
        )

        # 步骤 1: 验证API调用是否成功
        if not shipping_options_response.get("result"):
            raise OrderSyncError(
                error_code="CJ_SHIPPING_API_ERROR",
                message="CJ shipping cost API call failed.",
                details={"cj_response": shipping_options_response},
            )

        # 步骤 2: 验证数据内容
        shipping_options = shipping_options_response.get("data")
        if not shipping_options or not isinstance(shipping_options, list):
            raise OrderSyncError(
                error_code="NO_SHIPPING_METHODS_FOUND",
                message="No available shipping methods were returned by CJ for this order.",
                details={
                    "country_code": country_code,
                    "province": province,
                },
            )

        # 根据策略选择物流方式
        if settings.LOGISTICS_STRATEGY == "cheapest":
            chosen_method = min(shipping_options, key=lambda x: x.get("logisticsPrice", float('inf')))
        elif settings.LOGISTICS_STRATEGY == "fastest":
            # 注意：logisticsAging可能是 "5-10" 这样的字符串，需要解析
            def get_min_days(aging_str):
                try:
                    return int(aging_str.split('-')[0])
                except (ValueError, IndexError):
                    return float('inf')
            chosen_method = min(shipping_options, key=lambda x: get_min_days(x.get("logisticsAging", "")))
        else: # 默认使用cheapest
            chosen_method = min(shipping_options, key=lambda x: x.get("logisticsPrice", float('inf')))

        chosen_method_name = chosen_method.get("logisticsName")
        if not chosen_method_name:
            raise OrderSyncError(
                error_code="SHIPPING_METHOD_NAME_MISSING",
                message="Could not determine shipping method name from optimal choice.",
                details={"chosen_method_data": chosen_method}
            )
            
        logger.info(
            "Optimal shipping method selected",
            strategy=settings.LOGISTICS_STRATEGY,
            method_name=chosen_method_name,
            price=chosen_method.get("logisticsPrice"),
            aging=chosen_method.get("logisticsAging"),
        )
        return chosen_method_name
    
    async def update_order_status(self, hours_back: int = 72) -> Dict[str, Any]:
        """更新订单状态"""
        if not self.cj_client or not self.magento_client:
            await self.initialize()
            
        sync_result = {
            "total_processed": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # 获取需要更新状态的订单
            since_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            async for session in get_db():
                stmt = select(OrderMapping).where(
                    OrderMapping.last_sync_at >= since_time,
                    OrderMapping.order_status.in_([OrderStatus.PENDING, OrderStatus.PROCESSING])
                )
                result = await session.execute(stmt)
                order_mappings = result.scalars().all()
                
                for mapping in order_mappings:
                    try:
                        # 获取CJ订单状态
                        cj_order_detail = await self.cj_client.get_order_detail(mapping.cj_order_id)
                        
                        status_data = cj_order_detail.get("data", [{}])[0]
                        new_status = self._map_cj_status_to_local(status_data.get("orderStatus"))
                        
                        if new_status != mapping.order_status:
                            # 更新订单状态
                            await session.execute(
                                update(OrderMapping)
                                .where(OrderMapping.id == mapping.id)
                                .values(
                                    order_status=new_status,
                                    last_sync_at=datetime.utcnow()
                                )
                            )
                            
                            # 如果有跟踪信息，同步到Magento
                            if status_data.get("trackingNumber"):
                                await self._update_magento_tracking(
                                    mapping.magento_order_id,
                                    status_data.get("trackingNumber"),
                                    status_data.get("shippingMethodName", "CJ_STANDARD")
                                )
                            
                            sync_result["updated"] += 1
                            
                            logger.info(
                                "Order status updated",
                                magento_order_id=mapping.magento_order_increment_id,
                                old_status=mapping.order_status,
                                new_status=new_status
                            )
                        
                    except Exception as e:
                        logger.error(
                            "Failed to update order status",
                            order_id=mapping.magento_order_increment_id,
                            error=str(e)
                        )
                        sync_result["failed"] += 1
                        sync_result["errors"].append({
                            "order_id": mapping.magento_order_increment_id,
                            "error": str(e)
                        })
                    
                    sync_result["total_processed"] += 1
                    
                    # 添加延迟避免API限制
                    await asyncio.sleep(0.5)
                
                await session.commit()
            
            logger.info("Order status update completed", result=sync_result)
            return sync_result
            
        except Exception as e:
            logger.error("Order status update failed", error=str(e))
            raise OrderSyncError(
                error_code="ORDER_STATUS_UPDATE_ERROR",
                message="Failed to update order status",
                details={"error": str(e)}
            )
    
    def _map_cj_status_to_local(self, cj_status: str) -> OrderStatus:
        """映射CJ状态到本地状态"""
        status_mapping = {
            "pending": OrderStatus.PENDING,
            "processing": OrderStatus.PROCESSING,
            "shipped": OrderStatus.SHIPPED,
            "delivered": OrderStatus.DELIVERED,
            "cancelled": OrderStatus.CANCELLED,
            "failed": OrderStatus.FAILED
        }
        
        return status_mapping.get(cj_status.lower(), OrderStatus.PENDING)
    
    async def _update_magento_tracking(
        self,
        magento_order_id: str,
        tracking_number: str,
        shipping_method: str
    ) -> None:
        """更新Magento订单跟踪信息"""
        try:
            order_id_int = int(magento_order_id)

            # 1. 获取可发货的订单项
            items_for_shipment = await self.magento_client.get_order_items_for_shipment(order_id_int)
            if not items_for_shipment:
                logger.warning("No items to ship for order, skipping shipment creation.", order_id=magento_order_id)
                return

            # 2. 创建Shipment
            shipment_id = await self.magento_client.create_shipment(
                order_id=order_id_int,
                items=items_for_shipment
            )

            if not shipment_id:
                raise OrderSyncError(
                    error_code="MAGENTO_SHIPMENT_CREATION_FAILED",
                    message="Failed to create shipment in Magento, received empty shipment ID.",
                    details={"magento_order_id": magento_order_id}
                )

            logger.info("Shipment created in Magento", order_id=magento_order_id, shipment_id=shipment_id)

            # 3. 为Shipment添加跟踪信息
            await self.magento_client.add_tracking_info_to_shipment(
                shipment_id=shipment_id,
                tracking_number=tracking_number,
                carrier_code="custom", # 使用 'custom' 作为通用 carrier code
                title=f"CJ Dropshipping - {shipping_method}"
            )
            
            logger.info(
                "Tracking info added to Magento shipment",
                order_id=magento_order_id,
                tracking_number=tracking_number
            )
            
        except Exception as e:
            logger.error(
                "Failed to add tracking info to Magento",
                order_id=magento_order_id,
                tracking_number=tracking_number,
                error=str(e)
            )
    
    async def cancel_order(self, magento_order_id: str, reason: str = "Customer request") -> Dict[str, Any]:
        """取消订单"""
        if not self.cj_client or not self.magento_client:
            await self.initialize()
            
        try:
            # 查找订单映射
            async for session in get_db():
                stmt = select(OrderMapping).where(
                    OrderMapping.magento_order_id == magento_order_id
                )
                result = await session.execute(stmt)
                order_mapping = result.scalar_one_or_none()
                
                if not order_mapping:
                    raise OrderSyncError(
                        error_code="ORDER_MAPPING_NOT_FOUND",
                        message="Order mapping not found",
                        details={"magento_order_id": magento_order_id}
                    )
                
                # 取消CJ订单
                cancel_response = await self.cj_client.cancel_order(
                    order_mapping.cj_order_id,
                    reason
                )
                
                # 更新订单状态
                await session.execute(
                    update(OrderMapping)
                    .where(OrderMapping.id == order_mapping.id)
                    .values(
                        order_status=OrderStatus.CANCELLED,
                        last_sync_at=datetime.utcnow()
                    )
                )
                
                # 更新Magento订单状态
                await self.magento_client.update_order_status(
                    int(magento_order_id),
                    "canceled"
                )
                
                await session.commit()
                
                # 记录日志
                await self._log_sync_operation(
                    session,
                    SyncType.ORDER_SYNC,
                    LogSyncStatus.SUCCESS,
                    f"Cancelled order {order_mapping.magento_order_increment_id}"
                )
                
                logger.info(
                    "Order cancelled successfully",
                    magento_order_id=magento_order_id,
                    cj_order_id=order_mapping.cj_order_id
                )
                
                return {
                    "success": True,
                    "message": "Order cancelled successfully",
                    "cj_response": cancel_response
                }
                
        except Exception as e:
            logger.error("Failed to cancel order", magento_order_id=magento_order_id, error=str(e))
            raise OrderSyncError(
                error_code="ORDER_CANCEL_ERROR",
                message="Failed to cancel order",
                details={"error": str(e), "magento_order_id": magento_order_id}
            )
    
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


# 全局订单同步服务实例
_order_sync_service: Optional[OrderSyncService] = None


async def get_order_sync_service() -> OrderSyncService:
    """获取订单同步服务实例"""
    global _order_sync_service
    
    if _order_sync_service is None:
        _order_sync_service = OrderSyncService()
        await _order_sync_service.initialize()
    
    return _order_sync_service 