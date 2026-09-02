"""add_covering_idx_audit_session_article_ts

Revision ID: a7b8c9d0e1f2
Revises: f1e2d3c4b5a6
Create Date: 2026-09-02 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f1e2d3c4b5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create covering idx_audit_session_article_ts first to satisfy FK requirement, then drop redundant idx_audit_session_article."""
    op.create_index(
        'idx_audit_session_article_ts',
        'audit_records',
        ['session_id', 'article_code', 'scan_timestamp'],
        unique=False
    )
    op.drop_index('idx_audit_session_article', table_name='audit_records')


def downgrade() -> None:
    """Downgrade schema: create idx_audit_session_article first to satisfy FK requirement, then drop idx_audit_session_article_ts."""
    op.create_index(
        'idx_audit_session_article',
        'audit_records',
        ['session_id', 'article_code'],
        unique=False
    )
    op.drop_index('idx_audit_session_article_ts', table_name='audit_records')
