"""alter_branch_id_to_string

Revision ID: f1e2d3c4b5a6
Revises: d3e4f5a6b7c8
Create Date: 2026-08-11 08:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1e2d3c4b5a6'
down_revision: Union[str, Sequence[str], None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: alter work_sessions.branch_id and audit_records.branch_id from Integer to String(50)."""
    with op.batch_alter_table('work_sessions', schema=None) as batch_op:
        batch_op.alter_column(
            'branch_id',
            existing_type=sa.Integer(),
            type_=sa.String(length=50),
            existing_nullable=False
        )

    with op.batch_alter_table('audit_records', schema=None) as batch_op:
        batch_op.alter_column(
            'branch_id',
            existing_type=sa.Integer(),
            type_=sa.String(length=50),
            existing_nullable=False,
            existing_server_default='1'
        )


def downgrade() -> None:
    """Downgrade schema: alter work_sessions.branch_id and audit_records.branch_id from String(50) back to Integer."""
    with op.batch_alter_table('audit_records', schema=None) as batch_op:
        batch_op.alter_column(
            'branch_id',
            existing_type=sa.String(length=50),
            type_=sa.Integer(),
            existing_nullable=False,
            existing_server_default='1'
        )

    with op.batch_alter_table('work_sessions', schema=None) as batch_op:
        batch_op.alter_column(
            'branch_id',
            existing_type=sa.String(length=50),
            type_=sa.Integer(),
            existing_nullable=False
        )
