from abc import ABC, abstractmethod
from typing import Any, Dict


class ExternalSupplierGateway(ABC):
    """供应商网关抽象接口，支持多供应商实现"""

    @abstractmethod
    async def create_order(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        """创建订单，返回原始响应"""

    @abstractmethod
    async def get_order_status(self, supplier_order_id: str) -> Dict[str, Any]:
        """查询订单状态"""

    @abstractmethod
    async def cancel_order(self, supplier_order_id: str, reason: str) -> Dict[str, Any]:
        """取消订单"""
