"""add_empresas_sucursales_depositos

Revision ID: d1a2b3c4d5e6
Revises: c923f840f52e
Create Date: 2026-08-03 17:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'c923f840f52e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create empresas table
    op.create_table(
        'empresas',
        sa.Column('id_empresa', sa.Integer(), nullable=False),
        sa.Column('des_empresa', sa.String(length=40), nullable=False),
        sa.PrimaryKeyConstraint('id_empresa')
    )

    # 2. Create sucursales table
    op.create_table(
        'sucursales',
        sa.Column('id_sucursal', sa.Integer(), nullable=False),
        sa.Column('id_empresa', sa.Integer(), nullable=False),
        sa.Column('des_sucursal', sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(
            ['id_empresa'], ['empresas.id_empresa'],
            name='fk_sucursales_id_empresa',
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id_sucursal')
    )
    op.create_index('ix_sucursales_id_empresa', 'sucursales', ['id_empresa'], unique=False)

    # 3. Create depositos table
    op.create_table(
        'depositos',
        sa.Column('id_sucursal', sa.Integer(), nullable=False),
        sa.Column('id_deposito', sa.SmallInteger(), nullable=False),
        sa.Column('id_empresa', sa.Integer(), nullable=False),
        sa.Column('des_deposito', sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(
            ['id_sucursal'], ['sucursales.id_sucursal'],
            name='fk_depositos_id_sucursal',
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.ForeignKeyConstraint(
            ['id_empresa'], ['empresas.id_empresa'],
            name='fk_depositos_id_empresa',
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id_sucursal', 'id_deposito')
    )
    op.create_index('ix_depositos_id_empresa', 'depositos', ['id_empresa'], unique=False)

    # 4. Add foreign keys to stock_por_deposito
    op.create_foreign_key(
        'fk_stock_id_empresa',
        'stock_por_deposito', 'empresas',
        ['id_empresa'], ['id_empresa'],
        onupdate='CASCADE', ondelete='RESTRICT'
    )
    op.create_foreign_key(
        'fk_stock_id_sucursal',
        'stock_por_deposito', 'sucursales',
        ['id_sucursal'], ['id_sucursal'],
        onupdate='CASCADE', ondelete='RESTRICT'
    )
    op.create_foreign_key(
        'fk_stock_id_deposito',
        'stock_por_deposito', 'depositos',
        ['id_sucursal', 'id_deposito'], ['id_sucursal', 'id_deposito'],
        onupdate='CASCADE', ondelete='RESTRICT'
    )

    # 5. Add foreign keys to lotes_por_deposito
    op.create_foreign_key(
        'fk_lotes_id_empresa',
        'lotes_por_deposito', 'empresas',
        ['id_empresa'], ['id_empresa'],
        onupdate='CASCADE', ondelete='RESTRICT'
    )
    op.create_foreign_key(
        'fk_lotes_id_sucursal',
        'lotes_por_deposito', 'sucursales',
        ['id_sucursal'], ['id_sucursal'],
        onupdate='CASCADE', ondelete='RESTRICT'
    )
    op.create_foreign_key(
        'fk_lotes_id_deposito',
        'lotes_por_deposito', 'depositos',
        ['id_sucursal', 'id_deposito'], ['id_sucursal', 'id_deposito'],
        onupdate='CASCADE', ondelete='RESTRICT'
    )


def downgrade() -> None:
    # 1. Drop foreign keys on lotes_por_deposito
    op.drop_constraint('fk_lotes_id_deposito', 'lotes_por_deposito', type_='foreignkey')
    op.drop_constraint('fk_lotes_id_sucursal', 'lotes_por_deposito', type_='foreignkey')
    op.drop_constraint('fk_lotes_id_empresa', 'lotes_por_deposito', type_='foreignkey')

    # 2. Drop foreign keys on stock_por_deposito
    op.drop_constraint('fk_stock_id_deposito', 'stock_por_deposito', type_='foreignkey')
    op.drop_constraint('fk_stock_id_sucursal', 'stock_por_deposito', type_='foreignkey')
    op.drop_constraint('fk_stock_id_empresa', 'stock_por_deposito', type_='foreignkey')

    # 3. Drop tables in reverse dependency order
    op.drop_index('ix_depositos_id_empresa', table_name='depositos')
    op.drop_table('depositos')

    op.drop_index('ix_sucursales_id_empresa', table_name='sucursales')
    op.drop_table('sucursales')

    op.drop_table('empresas')
