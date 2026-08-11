"""add_enterprise_and_branch

Revision ID: a1b2c3d4e5f6
Revises: e5f6a7b8c9d0
Create Date: 2026-08-11 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create enterprises table
    op.create_table(
        'enterprises',
        sa.Column('id_enterprise', sa.Integer().with_variant(sa.Integer(), 'sqlite'), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id_enterprise')
    )
    op.create_index('idx_enterprises_tenant_id', 'enterprises', ['tenant_id'], unique=False)

    # 2. Create branches table
    op.create_table(
        'branches',
        sa.Column('id_branch', sa.Integer().with_variant(sa.Integer(), 'sqlite'), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('enterprise_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id_enterprise'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id_branch')
    )
    op.create_index('idx_branches_tenant_id', 'branches', ['tenant_id'], unique=False)
    op.create_index('idx_branches_tenant_enterprise', 'branches', ['tenant_id', 'enterprise_id'], unique=False)

    # 3. Alter users table to add enterprise_id and update branch_id foreign keys
    op.execute("UPDATE users SET branch_id = NULL WHERE branch_id IS NOT NULL")
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('enterprise_id', sa.Integer(), nullable=True))
        batch_op.alter_column('branch_id', existing_type=sa.String(length=50), type_=sa.Integer(), existing_nullable=True)
        batch_op.create_foreign_key('fk_users_enterprise_id', 'enterprises', ['enterprise_id'], ['id_enterprise'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_users_branch_id', 'branches', ['branch_id'], ['id_branch'], ondelete='SET NULL')
        batch_op.create_index('idx_users_enterprise_id', ['enterprise_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_branch_id', type_='foreignkey')
        batch_op.drop_constraint('fk_users_enterprise_id', type_='foreignkey')
        batch_op.drop_index('idx_users_enterprise_id')
        batch_op.alter_column('branch_id', existing_type=sa.Integer(), type_=sa.String(length=50), existing_nullable=True)
        batch_op.drop_column('enterprise_id')

    op.execute("DROP TABLE IF EXISTS branches")
    op.execute("DROP TABLE IF EXISTS enterprises")
