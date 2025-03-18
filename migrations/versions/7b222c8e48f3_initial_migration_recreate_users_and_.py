"""Initial migration - recreate users and orders tables

Revision ID: 7b222c8e48f3
Revises: 
Create Date: 2025-03-16 23:34:32.160567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b222c8e48f3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Recreate users and orders tables."""
    
    # ✅ Create Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(25), nullable=False, unique=True),
        sa.Column('email', sa.String(80), nullable=False, unique=True),
        sa.Column('password', sa.Text(), nullable=False),
        sa.Column('is_staff', sa.Boolean(), default=False, nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
    )

    # ✅ Create Orders Table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('order_status', sa.String(255), nullable=True, default="PENDING"),
        sa.Column('pizza_size', sa.String(255), nullable=True, default="SMALL"),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('paid', sa.Boolean(), default=False, nullable=False),
        sa.Column('stripe_payment_id', sa.String(255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema: Drop users and orders tables."""
    
    op.drop_table('orders')
    op.drop_table('users')