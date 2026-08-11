"""alter_users_tenant_id_to_string

Revision ID: 8c3f921d7e56
Revises: 7f2c819a3d45
Create Date: 2026-08-10 20:18:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c3f921d7e56'
down_revision: Union[str, Sequence[str], None] = '7f2c819a3d45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: alter users.tenant_id from Integer to String(50)."""
    op.alter_column(
        'users',
        'tenant_id',
        existing_type=sa.Integer(),
        type_=sa.String(length=50),
        existing_nullable=False
    )


def downgrade() -> None:
    """Downgrade schema: alter users.tenant_id from String(50) back to Integer."""
    op.alter_column(
        'users',
        'tenant_id',
        existing_type=sa.String(length=50),
        type_=sa.Integer(),
        existing_nullable=False
    )
