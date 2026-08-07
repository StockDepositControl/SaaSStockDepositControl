"""Add branch_id to audit_records and idx_audit_fallback

Revision ID: ef8be726db43
Revises: 3d4bc96d9b91
Create Date: 2026-08-05 09:26:17.732284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef8be726db43'
down_revision: Union[str, Sequence[str], None] = 'c8d9e0f1a2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('audit_records', sa.Column('branch_id', sa.Integer(), server_default='1', nullable=False))
    op.create_index('idx_audit_fallback', 'audit_records', ['tenant_id', 'branch_id', 'warehouse_id', 'article_code', 'scan_timestamp'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_audit_fallback', table_name='audit_records')
    op.drop_column('audit_records', 'branch_id')
