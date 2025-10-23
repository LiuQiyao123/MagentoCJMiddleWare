"""create store and order_mapping tables

Revision ID: 20251023
Revises: b152d3e31588
Create Date: 2025-10-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "20251023"
down_revision = "b152d3e31588"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("magento_base_url", sa.String(length=255), nullable=False),
        sa.Column("magento_access_token", sa.String(length=255), nullable=False),
        sa.Column("magento_store_code", sa.String(length=50)),
        sa.Column("supplier_type", sa.String(length=50), nullable=False, server_default="cj"),
        sa.Column("supplier_credentials", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_supplier_type", "stores", ["supplier_type"])

    op.create_table(
        "order_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("magento_order_id", sa.String(length=50), nullable=False),
        sa.Column("magento_order_increment_id", sa.String(length=50), nullable=False),
        sa.Column("cj_order_id", sa.String(length=50), nullable=False),
        sa.Column("order_status", sa.Enum("pending", "processing", "shipped", "delivered", "cancelled", "failed", name="orderstatus"), nullable=False, server_default="pending"),
        sa.Column("total_amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="USD"),
        sa.Column("tracking_number", sa.String(length=100)),
        sa.Column("shipping_method", sa.String(length=100)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("order_metadata", sa.JSON()),
        mysql_charset="utf8mb4",
    )
    op.create_index("idx_magento_order_id", "order_mappings", ["magento_order_id"])
    op.create_index("idx_cj_order_id", "order_mappings", ["cj_order_id"])
    op.create_index("idx_order_status", "order_mappings", ["order_status"])
    op.create_index("idx_tracking_number", "order_mappings", ["tracking_number"])
    op.create_index("idx_last_sync_at", "order_mappings", ["last_sync_at"])
    op.create_index("idx_created_at", "order_mappings", ["created_at"])


def downgrade() -> None:
    op.drop_table("order_mappings")
    op.drop_table("stores")
