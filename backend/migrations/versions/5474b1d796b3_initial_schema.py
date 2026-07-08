"""initial_schema

Revision ID: 5474b1d796b3
Revises: 
Create Date: 2026-07-08 11:29:06.216969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5474b1d796b3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. familias
    op.create_table(
        'familias',
        sa.Column('id_familia', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('des_familia', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id_familia')
    )

    # 2. marcas
    op.create_table(
        'marcas',
        sa.Column('id_marca', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('des_marca', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id_marca')
    )

    # 3. grupos
    op.create_table(
        'grupos',
        sa.Column('id_familia', sa.Integer(), nullable=False),
        sa.Column('id_grupo', sa.Integer(), nullable=False),
        sa.Column('des_grupo', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['id_familia'], ['familias.id_familia'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_familia', 'id_grupo')
    )

    # 4. usuarios
    op.create_table(
        'usuarios',
        sa.Column('id_usuario', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('nombre_completo', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('rol', sa.Enum('administrador', 'supervisor', 'auditor', name='userrole'), nullable=False),
        sa.Column('id_sucursal', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id_usuario'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_usuarios_tenant', 'usuarios', ['tenant_id'], unique=False)
    op.create_index('ix_usuarios_tenant_email', 'usuarios', ['tenant_id', 'email'], unique=False)

    # 5. articulos
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

    # 6. stock_por_deposito
    op.create_table(
        'stock_por_deposito',
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('id_sucursal', sa.Integer(), nullable=False),
        sa.Column('id_deposito', sa.Integer(), nullable=False),
        sa.Column('id_articulo', sa.String(length=50), nullable=False),
        sa.Column('stock_real', sa.Integer(), nullable=False),
        sa.Column('fue_auditado', sa.Boolean(), nullable=False),
        sa.Column('fecha_hora_auditación', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id', 'id_articulo'], ['articulos.tenant_id', 'articulos.id_articulo'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('tenant_id', 'id_sucursal', 'id_deposito', 'id_articulo')
    )
    op.create_index('ix_stock_por_deposito_tenant_deposito', 'stock_por_deposito', ['tenant_id', 'id_sucursal', 'id_deposito'], unique=False)

    # 7. lotes_por_deposito
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

    # 8. auditorias_registro
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


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('auditorias_registro')
    op.drop_table('lotes_por_deposito')
    op.drop_table('stock_por_deposito')
    op.drop_table('articulos')
    op.drop_table('usuarios')
    op.drop_table('grupos')
    op.drop_table('marcas')
    op.drop_table('familias')
