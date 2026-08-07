"""add_client_uuid_to_audit_records

Revision ID: a9b8c7d6e5f4
Revises: 269a76e86f31
Create Date: 2026-08-03 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9b8c7d6e5f4'
down_revision: Union[str, Sequence[str], None] = '269a76e86f31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('audit_records', sa.Column('client_uuid', sa.String(length=36), nullable=True))
    op.create_unique_constraint('uq_audit_records_client_uuid', 'audit_records', ['client_uuid'])
    op.create_index('idx_audit_tenant_client_uuid', 'audit_records', ['tenant_id', 'client_uuid'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_audit_tenant_client_uuid', table_name='audit_records')
    op.drop_constraint('uq_audit_records_client_uuid', 'audit_records', type_='unique')
    op.drop_column('audit_records', 'client_uuid')
