"""add_idx_audit_shrinkage

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-09-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create idx_audit_shrinkage for optimized shrinkage report filtering."""
    op.create_index(
        'idx_audit_shrinkage',
        'audit_records',
        ['tenant_id', 'action_type', 'scan_timestamp'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema: drop idx_audit_shrinkage."""
    op.drop_index('idx_audit_shrinkage', table_name='audit_records')
