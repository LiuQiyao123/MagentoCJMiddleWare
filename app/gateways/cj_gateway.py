from typing import Any, Dict

from app.gateways.base import ExternalSupplierGateway
from app.clients.cj_client import CJClient, get_cj_client


class CJGateway(ExternalSupplierGateway):
    """CJ Dropshipping 网关，实现通用供应商接口"""

    def __init__(self, client: CJClient):
        self.client = client

    @classmethod
    async def create(cls) -> "CJGateway":
        client = await get_cj_client()
        return cls(client)

    async def create_order(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.create_order(order_payload)

    async def get_order_status(self, supplier_order_id: str) -> Dict[str, Any]:
        return await self.client.get_order_status(supplier_order_id)

    async def cancel_order(self, supplier_order_id: str, reason: str) -> Dict[str, Any]:
        return await self.client.cancel_order(supplier_order_id, reason)
