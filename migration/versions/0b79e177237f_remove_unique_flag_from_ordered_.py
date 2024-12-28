"""remove unique flag from ordered_products table

Revision ID: 0b79e177237f
Revises: eab323436b77
Create Date: 2024-12-25 18:03:01.063573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql

# revision identifiers, used by Alembic.
revision: str = '0b79e177237f'
down_revision: Union[str, None] = 'eab323436b77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('ordered_products')
    op.create_table('ordered_products',
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('chosen_quantity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('order_id', 'product_id'),
    sa.UniqueConstraint('order_id', 'product_id')
    )


def downgrade() -> None:
    op.drop_table('ordered_products')
    op.create_table('ordered_products',
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('chosen_quantity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('order_id', 'product_id'),
    sa.UniqueConstraint('order_id', 'product_id'),
    sa.UniqueConstraint('product_id')
    )

