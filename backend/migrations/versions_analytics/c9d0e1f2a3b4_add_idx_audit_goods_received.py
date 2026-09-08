"""add_idx_audit_goods_received

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-09-08 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, Sequence[str], None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create idx_audit_goods_received for optimized goods received report filtering."""
    op.create_index(
        'idx_audit_goods_received',
        'audit_records',
        ['tenant_id', 'action_type', 'scan_timestamp'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema: drop idx_audit_goods_received."""
    op.drop_index('idx_audit_goods_received', table_name='audit_records')
