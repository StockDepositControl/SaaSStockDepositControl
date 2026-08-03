"""add_tenant_id_to_users

Revision ID: 7f2c819a3d45
Revises: 403c7fefe759
Create Date: 2026-08-01 17:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f2c819a3d45'
down_revision: Union[str, Sequence[str], None] = '403c7fefe759'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('tenant_id', sa.String(length=50), nullable=False, server_default=''))
    # Drop global unique constraint on email
    try:
        op.drop_constraint('email', 'users', type_='unique')
    except Exception:
        # On MySQL/MariaDB unique constraints are unique indexes
        try:
            op.drop_index('email', table_name='users')
        except Exception:
            pass

    op.create_index('idx_users_tenant_id', 'users', ['tenant_id'], unique=False)
    op.create_index('idx_users_tenant_email', 'users', ['tenant_id', 'email'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_users_tenant_email', table_name='users')
    op.drop_index('idx_users_tenant_id', table_name='users')
    op.create_unique_constraint('email', 'users', ['email'])
    op.drop_column('users', 'tenant_id')
