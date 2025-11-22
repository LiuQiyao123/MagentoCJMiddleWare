"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建产品表
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('magento_id', sa.String(length=255), nullable=True),
        sa.Column('cj_product_id', sa.String(length=255), nullable=True),
        sa.Column('sku', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Decimal(precision=10, scale=2), nullable=True),
        sa.Column('cost_price', sa.Decimal(precision=10, scale=2), nullable=True),
        sa.Column('stock_quantity', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('brand', sa.String(length=255), nullable=True),
        sa.Column('weight', sa.Decimal(precision=8, scale=3), nullable=True),
        sa.Column('dimensions', sa.JSON(), nullable=True),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('attributes', sa.JSON(), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku'),
        sa.Index('idx_magento_id', 'magento_id'),
        sa.Index('idx_cj_product_id', 'cj_product_id'),
        sa.Index('idx_sync_status', 'sync_status')
    )

    # 创建订单表
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('magento_order_id', sa.String(length=255), nullable=True),
        sa.Column('cj_order_id', sa.String(length=255), nullable=True),
        sa.Column('order_number', sa.String(length=255), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('order_status', sa.String(length=50), nullable=True),
        sa.Column('payment_status', sa.String(length=50), nullable=True),
        sa.Column('shipping_status', sa.String(length=50), nullable=True),
        sa.Column('total_amount', sa.Decimal(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('shipping_address', sa.JSON(), nullable=True),
        sa.Column('billing_address', sa.JSON(), nullable=True),
        sa.Column('items', sa.JSON(), nullable=True),
        sa.Column('shipping_method', sa.String(length=255), nullable=True),
        sa.Column('payment_method', sa.String(length=255), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number'),
        sa.Index('idx_magento_order_id', 'magento_order_id'),
        sa.Index('idx_cj_order_id', 'cj_order_id'),
        sa.Index('idx_sync_status', 'sync_status'),
        sa.Index('idx_customer_email', 'customer_email')
    )

    # 创建同步日志表
    op.create_table('sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_sync_type', 'sync_type'),
        sa.Index('idx_entity_type', 'entity_type'),
        sa.Index('idx_status', 'status'),
        sa.Index('idx_started_at', 'started_at')
    )


def downgrade() -> None:
    op.drop_table('sync_logs')
    op.drop_table('orders')
    op.drop_table('products') 