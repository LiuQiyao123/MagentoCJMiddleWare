"""
订单同步服务
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.cj_client import get_cj_client, CJClient
from app.clients.magento_client import get_magento_client, MagentoClient
from app.config.database import get_db
from app.models.order import OrderMapping, OrderStatus
from app.models.product import ProductMapping, SyncStatus
from app.models.sync_log import SyncLog, SyncType, SyncStatus as LogSyncStatus
from app.core.exceptions import APIException

logger = structlog.get_logger(__name__)


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
            self.cj_client = await get_cj_client()
            self.magento_client = await get_magento_client()
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
            cj_order_data = await self._build_cj_order(magento_order)
            
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
    
    async def _build_cj_order(self, magento_order: Dict[str, Any]) -> Dict[str, Any]:
        """构建CJ订单数据"""
        order_items = []
        
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
                            "shippingMethod": "CJ_STANDARD"  # 默认物流方式
                        })
                    else:
                        logger.warning(
                            "Product mapping not found for SKU",
                            sku=item["sku"],
                            order_id=magento_order["increment_id"]
                        )
        
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
        
        return cj_order
    
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
                        cj_order_status = await self.cj_client.get_order_status(mapping.cj_order_id)
                        
                        status_data = cj_order_status.get("data", {})
                        new_status = self._map_cj_status_to_local(status_data.get("status"))
                        
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
                                    status_data.get("shippingMethod", "CJ_STANDARD")
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
            await self.magento_client.add_tracking_info(
                order_id=int(magento_order_id),
                tracking_number=tracking_number,
                carrier_code="cj_dropshipping",
                title=f"CJ Dropshipping - {shipping_method}"
            )
            
            logger.info(
                "Tracking info added to Magento",
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