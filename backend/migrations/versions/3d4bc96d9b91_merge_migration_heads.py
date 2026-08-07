"""Merge migration heads

Revision ID: 3d4bc96d9b91
Revises: 1b57abb2e053, d1a2b3c4d5e6
Create Date: 2026-08-03 17:53:35.322227

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d4bc96d9b91'
down_revision: Union[str, Sequence[str], None] = ('1b57abb2e053', 'd1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
