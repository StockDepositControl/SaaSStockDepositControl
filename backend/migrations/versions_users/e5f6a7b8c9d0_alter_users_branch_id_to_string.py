"""alter_users_branch_id_to_string

Revision ID: e5f6a7b8c9d0
Revises: 8c3f921d7e56
Create Date: 2026-08-11 08:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = '8c3f921d7e56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: alter users.branch_id from Integer to String(50)."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'branch_id',
            existing_type=sa.Integer(),
            type_=sa.String(length=50),
            existing_nullable=True
        )


def downgrade() -> None:
    """Downgrade schema: alter users.branch_id from String(50) back to Integer."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'branch_id',
            existing_type=sa.String(length=50),
            type_=sa.Integer(),
            existing_nullable=True
        )
