"""update_audit_record_fields

Revision ID: c8d9e0f1a2b3
Revises: a9b8c7d6e5f4
Create Date: 2026-08-04 18:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, Sequence[str], None] = 'a9b8c7d6e5f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('audit_records', sa.Column('audit_quantity', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('audit_records', sa.Column('observation', sa.String(length=255), nullable=True))
    # Modify action_type to String(50) if needed, or handle gracefully
    try:
        op.alter_column('audit_records', 'action_type', type_=sa.String(length=50), existing_nullable=False)
    except Exception:
        pass


def downgrade() -> None:
    """Downgrade schema."""
    try:
        op.drop_column('audit_records', 'observation')
    except Exception:
        pass
    try:
        op.drop_column('audit_records', 'audit_quantity')
    except Exception:
        pass
