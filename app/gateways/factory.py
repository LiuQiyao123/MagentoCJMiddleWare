from typing import Dict

from app.gateways.base import ExternalSupplierGateway
from app.gateways.cj_gateway import CJGateway

SUPPORTED_SUPPLIERS = {
    "cj": CJGateway,
}


async def get_supplier_gateway(supplier_type: str) -> ExternalSupplierGateway:
    supplier_type = supplier_type.lower()
    if supplier_type not in SUPPORTED_SUPPLIERS:
        raise ValueError(f"Unsupported supplier type: {supplier_type}")
    gateway_cls = SUPPORTED_SUPPLIERS[supplier_type]
    return await gateway_cls.create()
