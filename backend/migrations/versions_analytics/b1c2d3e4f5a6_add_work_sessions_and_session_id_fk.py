"""add_work_sessions_and_session_id_fk

Revision ID: b1c2d3e4f5a6
Revises: ef8be726db43
Create Date: 2026-08-07 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'ef8be726db43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'work_sessions',
        sa.Column('session_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False, primary_key=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='OPEN', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['record_tenants.tenant_id'], ondelete='RESTRICT', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index('idx_ws_lookup', 'work_sessions', ['tenant_id', 'branch_id', 'opened_at', 'closed_at'], unique=False)
    op.create_index('idx_ws_status', 'work_sessions', ['tenant_id', 'branch_id', 'status'], unique=False)

    bind = op.get_bind()
    has_tenant = bind.execute(sa.text("SELECT COUNT(*) FROM record_tenants")).scalar()
    if not has_tenant:
        bind.execute(sa.text("INSERT INTO record_tenants (tenant_id, tenant_name, pharmacy_code, created_at) VALUES (1, 'Default Tenant', 'FARMA-000', NOW())"))

    has_session = bind.execute(sa.text("SELECT COUNT(*) FROM work_sessions WHERE session_id=1")).scalar()
    if not has_session:
        bind.execute(sa.text("INSERT INTO work_sessions (session_id, tenant_id, branch_id, opened_at, closed_at, status, created_at) VALUES (1, 1, 1, '2000-01-01 00:00:00', '2099-12-31 23:59:59', 'CLOSED', NOW())"))

    op.add_column('audit_records', sa.Column('session_id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), server_default='1', nullable=False))
    op.create_foreign_key('fk_audit_records_session_id', 'audit_records', 'work_sessions', ['session_id'], ['session_id'], ondelete='RESTRICT', onupdate='CASCADE')
    op.create_index('idx_audit_session_article', 'audit_records', ['session_id', 'article_code'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_audit_records_session_id', 'audit_records', type_='foreignkey')
    op.drop_index('idx_audit_session_article', table_name='audit_records')
    op.drop_column('audit_records', 'session_id')
    op.drop_table('work_sessions')
