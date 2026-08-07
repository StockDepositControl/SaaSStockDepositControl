"""refactor_db_articles_production_schema

Revision ID: b812f930e41f
Revises: a941f830d92e
Create Date: 2026-07-28 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b812f930e41f'
down_revision: Union[str, Sequence[str], None] = 'a941f830d92e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop existing db_articles and legacy tables in reverse dependency order
    op.execute("SET FOREIGN_KEY_CHECKS = 0;")
    op.drop_table('auditorias_registro', if_exists=True)
    op.drop_table('lotes_por_deposito', if_exists=True)
    op.drop_table('stock_por_deposito', if_exists=True)
    op.drop_table('articulos', if_exists=True)
    op.drop_table('grupos', if_exists=True)
    op.drop_table('marcas', if_exists=True)
    op.drop_table('familias', if_exists=True)
    op.drop_table('usuarios', if_exists=True)
    op.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # 2. Create production familias
    op.create_table(
        'familias',
        sa.Column('id_familia', sa.String(length=2), nullable=False),
        sa.Column('des_familia', sa.String(length=40), nullable=False),
        sa.PrimaryKeyConstraint('id_familia')
    )

    # 3. Create production grupos
    op.create_table(
        'grupos',
        sa.Column('id_familia', sa.String(length=2), nullable=False),
        sa.Column('id_grupo', sa.String(length=2), nullable=False),
        sa.Column('des_grupo', sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(
            ['id_familia'], ['familias.id_familia'],
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id_familia', 'id_grupo')
    )

    # 4. Create production marcas
    op.create_table(
        'marcas',
        sa.Column('id_marca', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('des_marca', sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint('id_marca')
    )

    # 5. Create production articulos
    op.create_table(
        'articulos',
        sa.Column('id_articulo', sa.CHAR(length=25), nullable=False),
        sa.Column('presentacion', sa.CHAR(length=255), nullable=True),
        sa.Column('des_articulo', sa.CHAR(length=255), nullable=False),
        sa.Column('id_marca', sa.Integer(), nullable=False),
        sa.Column('id_familia', sa.String(length=2), nullable=False),
        sa.Column('id_grupo', sa.String(length=2), nullable=False),
        sa.Column('pcio_com_siva', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ['id_marca'], ['marcas.id_marca'],
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.ForeignKeyConstraint(
            ['id_familia', 'id_grupo'], ['grupos.id_familia', 'grupos.id_grupo'],
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id_articulo')
    )
    op.create_index('ix_articulos_id_marca', 'articulos', ['id_marca'], unique=False)
    op.create_index('ix_articulos_id_familia_id_grupo', 'articulos', ['id_familia', 'id_grupo'], unique=False)

    # 6. Create production stock_por_deposito
    op.create_table(
        'stock_por_deposito',
        sa.Column('id_empresa', sa.Integer(), nullable=False),
        sa.Column('id_sucursal', sa.Integer(), nullable=False),
        sa.Column('id_deposito', sa.SmallInteger(), nullable=False),
        sa.Column('id_articulo', sa.CHAR(length=25), nullable=False),
        sa.Column('stock_real', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(
            ['id_articulo'], ['articulos.id_articulo'],
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id_empresa', 'id_sucursal', 'id_deposito', 'id_articulo')
    )
    op.create_index('ix_stock_deposito_empresa_sucursal', 'stock_por_deposito', ['id_empresa', 'id_sucursal'], unique=False)
    op.create_index('ix_stock_deposito_id_articulo', 'stock_por_deposito', ['id_articulo'], unique=False)

    # 7. Create production lotes_por_deposito
    op.create_table(
        'lotes_por_deposito',
        sa.Column('id_empresa', sa.Integer(), nullable=False),
        sa.Column('id_sucursal', sa.Integer(), nullable=False),
        sa.Column('id_deposito', sa.SmallInteger(), nullable=False),
        sa.Column('id_articulo', sa.CHAR(length=25), nullable=False),
        sa.Column('lote', sa.String(length=10), nullable=False),
        sa.Column('vencimiento', sa.String(length=10), nullable=True),
        sa.Column('stock_real', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(
            ['id_articulo'], ['articulos.id_articulo'],
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id_empresa', 'id_sucursal', 'id_deposito', 'id_articulo', 'lote')
    )
    op.create_index('ix_lotes_deposito_empresa_sucursal', 'lotes_por_deposito', ['id_empresa', 'id_sucursal'], unique=False)
    op.create_index('ix_lotes_deposito_id_articulo', 'lotes_por_deposito', ['id_articulo'], unique=False)
    op.create_index('ix_lotes_deposito_vencimiento', 'lotes_por_deposito', ['vencimiento'], unique=False)

    # 8. Create production codigos_barra_articulo
    op.create_table(
        'codigos_barra_articulo',
        sa.Column('id_articulo', sa.CHAR(length=25), nullable=False),
        sa.Column('cod_barra', sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(
            ['id_articulo'], ['articulos.id_articulo'],
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id_articulo', 'cod_barra')
    )
    op.create_index('ix_codigos_barra_cod_barra', 'codigos_barra_articulo', ['cod_barra'], unique=False)
    op.create_index('ix_codigos_barra_id_articulo', 'codigos_barra_articulo', ['id_articulo'], unique=False)


def downgrade() -> None:
    # 1. Drop production tables
    op.execute("SET FOREIGN_KEY_CHECKS = 0;")
    op.drop_table('codigos_barra_articulo', if_exists=True)
    op.drop_table('lotes_por_deposito', if_exists=True)
    op.drop_table('stock_por_deposito', if_exists=True)
    op.drop_table('articulos', if_exists=True)
    op.drop_table('marcas', if_exists=True)
    op.drop_table('grupos', if_exists=True)
    op.drop_table('familias', if_exists=True)
    op.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # 2. Recreate previous schema tables
    op.create_table(
        'familias',
        sa.Column('id_familia', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('des_familia', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id_familia')
    )

    op.create_table(
        'marcas',
        sa.Column('id_marca', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('des_marca', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id_marca')
    )

    op.create_table(
        'grupos',
        sa.Column('id_familia', sa.Integer(), nullable=False),
        sa.Column('id_grupo', sa.Integer(), nullable=False),
        sa.Column('des_grupo', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['id_familia'], ['familias.id_familia'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_familia', 'id_grupo')
    )

    op.create_table(
        'usuarios',
        sa.Column('id_usuario', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('nombre_completo', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('rol', sa.Enum('administrador', 'supervisor', 'auditor', name='userrole'), nullable=False),
        sa.Column('id_sucursal', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id_usuario'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_usuarios_tenant', 'usuarios', ['tenant_id'], unique=False)
    op.create_index('ix_usuarios_tenant_email', 'usuarios', ['tenant_id', 'email'], unique=False)

    op.create_table(
        'articulos',
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('id_articulo', sa.String(length=50), nullable=False),
        sa.Column('presentacion', sa.String(length=255), nullable=True),
        sa.Column('des_articulo', sa.String(length=255), nullable=False),
        sa.Column('id_marca', sa.Integer(), nullable=True),
        sa.Column('id_familia', sa.Integer(), nullable=True),
        sa.Column('id_grupo', sa.Integer(), nullable=True),
        sa.Column('pcio_com_siva', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.ForeignKeyConstraint(['id_marca'], ['marcas.id_marca'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['id_familia'], ['familias.id_familia'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['id_familia', 'id_grupo'], ['grupos.id_familia', 'grupos.id_grupo'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('tenant_id', 'id_articulo')
    )
    op.create_index('ix_articulos_tenant_articulo', 'articulos', ['tenant_id', 'id_articulo'], unique=False)
    op.create_index('ix_articulos_id_marca', 'articulos', ['id_marca'], unique=False)
    op.create_index('ix_articulos_id_familia_id_grupo', 'articulos', ['id_familia', 'id_grupo'], unique=False)

    op.create_table(
        'stock_por_deposito',
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('id_sucursal', sa.Integer(), nullable=False),
        sa.Column('id_deposito', sa.Integer(), nullable=False),
        sa.Column('id_articulo', sa.String(length=50), nullable=False),
        sa.Column('stock_real', sa.Integer(), nullable=False),
        sa.Column('stock_teorico', sa.Integer(), server_default='0', nullable=False),
        sa.Column('fue_auditado', sa.Boolean(), nullable=False),
        sa.Column('fecha_hora_auditación', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id', 'id_articulo'], ['articulos.tenant_id', 'articulos.id_articulo'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tenant_id', 'id_sucursal', 'id_deposito', 'id_articulo')
    )
    op.create_index('ix_stock_por_deposito_tenant_deposito', 'stock_por_deposito', ['tenant_id', 'id_sucursal', 'id_deposito'], unique=False)

    op.create_table(
        'lotes_por_deposito',
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('id_deposito', sa.Integer(), nullable=False),
        sa.Column('id_articulo', sa.String(length=50), nullable=False),
        sa.Column('lote', sa.String(length=50), nullable=False),
        sa.Column('vencimiento', sa.Date(), nullable=False),
        sa.Column('stock_real', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id', 'id_articulo'], ['articulos.tenant_id', 'articulos.id_articulo'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tenant_id', 'id_deposito', 'id_articulo', 'lote')
    )
    op.create_index('ix_lotes_por_deposito_tenant_deposito', 'lotes_por_deposito', ['tenant_id', 'id_deposito'], unique=False)
    op.create_index('ix_lotes_por_deposito_vencimiento', 'lotes_por_deposito', ['vencimiento'], unique=False)

    op.create_table(
        'auditorias_registro',
        sa.Column('id_auditoria', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('id_sucursal', sa.Integer(), nullable=False),
        sa.Column('id_deposito', sa.Integer(), nullable=False),
        sa.Column('id_articulo', sa.String(length=50), nullable=False),
        sa.Column('tipo_accion', sa.Enum('Alta', 'Baja', 'Sin Acción', name='tipoaccion'), nullable=False),
        sa.Column('cantidad_afectada', sa.Integer(), nullable=False),
        sa.Column('monto_valorizado', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('id_usuario', sa.Integer(), nullable=False),
        sa.Column('fecha_hora', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id', 'id_articulo'], ['articulos.tenant_id', 'articulos.id_articulo'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_usuario'], ['usuarios.id_usuario'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_auditoria')
    )
    op.create_index('ix_auditorias_registro_tenant_sucursal', 'auditorias_registro', ['tenant_id', 'id_sucursal'], unique=False)
    op.create_index('ix_auditorias_registro_id_usuario', 'auditorias_registro', ['id_usuario'], unique=False)
