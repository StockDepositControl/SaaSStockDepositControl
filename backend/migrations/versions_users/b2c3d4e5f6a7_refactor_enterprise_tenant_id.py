"""refactor_enterprise_tenant_id

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-11 09:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop existing FKs and tables safely if present
    try:
        op.execute("ALTER TABLE users DROP FOREIGN KEY fk_users_enterprise_id")
    except Exception:
        pass
    try:
        op.execute("ALTER TABLE users DROP FOREIGN KEY fk_users_branch_id")
    except Exception:
        pass
    try:
        op.execute("ALTER TABLE users DROP INDEX idx_users_enterprise_id")
    except Exception:
        pass
    try:
        op.execute("ALTER TABLE users DROP COLUMN enterprise_id")
    except Exception:
        pass

    op.execute("DROP TABLE IF EXISTS branches")
    op.execute("DROP TABLE IF EXISTS enterprises")

    # 2. Recreate enterprises table with tenant_id (Integer) as Primary Key
    op.create_table(
        'enterprises',
        sa.Column('tenant_id', sa.Integer().with_variant(sa.Integer(), 'sqlite'), nullable=False, autoincrement=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('tenant_id')
    )

    # 3. Recreate branches table referencing enterprises.tenant_id
    op.create_table(
        'branches',
        sa.Column('id_branch', sa.Integer().with_variant(sa.Integer(), 'sqlite'), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['enterprises.tenant_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_branch')
    )
    op.create_index('idx_branches_tenant_id', 'branches', ['tenant_id'], unique=False)

    # 4. Alter users table: convert non-numeric tenant_id to 1 and alter tenant_id to Integer
    op.execute("UPDATE users SET tenant_id = '1' WHERE tenant_id NOT REGEXP '^[0-9]+$' OR tenant_id IS NULL OR tenant_id = ''")
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('tenant_id', existing_type=sa.String(length=50), type_=sa.Integer(), existing_nullable=False)

    # Ensure all existing tenant_ids in users exist in enterprises before creating FK
    op.execute("INSERT IGNORE INTO enterprises (tenant_id, description) SELECT DISTINCT tenant_id, 'Default Enterprise' FROM users WHERE tenant_id IS NOT NULL AND tenant_id != 0")

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_users_tenant_id', 'enterprises', ['tenant_id'], ['tenant_id'], ondelete='CASCADE')
        batch_op.create_foreign_key('fk_users_branch_id', 'branches', ['branch_id'], ['id_branch'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_tenant_id', type_='foreignkey')
        batch_op.drop_constraint('fk_users_branch_id', type_='foreignkey')
        batch_op.alter_column('tenant_id', existing_type=sa.Integer(), type_=sa.String(length=50), existing_nullable=False)
        batch_op.add_column(sa.Column('enterprise_id', sa.Integer(), nullable=True))

    op.execute("DROP TABLE IF EXISTS branches")
    op.execute("DROP TABLE IF EXISTS enterprises")

    op.create_table(
        'enterprises',
        sa.Column('id_enterprise', sa.Integer().with_variant(sa.Integer(), 'sqlite'), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id_enterprise')
    )
    op.create_table(
        'branches',
        sa.Column('id_branch', sa.Integer().with_variant(sa.Integer(), 'sqlite'), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('enterprise_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id_enterprise'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_branch')
    )
