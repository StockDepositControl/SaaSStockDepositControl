"""alter_pcio_com_siva_decimal_add_fulltext_des_articulo

Revision ID: c923f840f52e
Revises: b812f930e41f
Create Date: 2026-08-02 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c923f840f52e'
down_revision: Union[str, Sequence[str], None] = 'b812f930e41f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alter pcio_com_siva from FLOAT to DECIMAL(15, 4)
    op.alter_column(
        'articulos',
        'pcio_com_siva',
        type_=sa.Numeric(precision=15, scale=4),
        existing_type=sa.Float(),
        existing_nullable=False
    )

    # 2. Add FULLTEXT index on des_articulo for fast tokenized lookup
    op.execute("CREATE FULLTEXT INDEX ft_articulos_des_articulo ON articulos(des_articulo);")


def downgrade() -> None:
    # 1. Drop FULLTEXT index
    op.execute("DROP INDEX ft_articulos_des_articulo ON articulos;")

    # 2. Revert pcio_com_siva from DECIMAL(15, 4) to FLOAT
    op.alter_column(
        'articulos',
        'pcio_com_siva',
        type_=sa.Float(),
        existing_type=sa.Numeric(precision=15, scale=4),
        existing_nullable=False
    )
