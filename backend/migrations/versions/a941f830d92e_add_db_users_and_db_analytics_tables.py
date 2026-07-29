"""add_db_users_and_db_analytics_tables

Revision ID: a941f830d92e
Revises: 283505019475
Create Date: 2026-07-27 21:07:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a941f830d92e'
down_revision: Union[str, Sequence[str], None] = '283505019475'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('idx_users_branch_id', 'users', ['branch_id'], unique=False)

    # 2. roles table
    op.create_table(
        'roles',
        sa.Column('role_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('role_id'),
        sa.UniqueConstraint('name', name='uq_roles_name'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # 3. user_roles junction table
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # 4. record_tenants table
    op.create_table(
        'record_tenants',
        sa.Column('tenant_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tenant_name', sa.String(length=150), nullable=False),
        sa.Column('pharmacy_code', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('tenant_id'),
        sa.UniqueConstraint('pharmacy_code', name='uq_tenants_pharmacy_code'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # 5. audit_records table
    op.create_table(
        'audit_records',
        sa.Column('audit_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('article_code', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.Enum('ADDITION', 'REMOVAL', 'NO_ACTION', name='actiontype'), nullable=False),
        sa.Column('affected_amount', sa.Integer(), nullable=False),
        sa.Column('applied_unit_cost', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('applied_vat_rate', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('valorized_amount', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('scan_timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['record_tenants.tenant_id'], ondelete='RESTRICT', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('audit_id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('idx_audit_tenant_scan', 'audit_records', ['tenant_id', 'scan_timestamp'], unique=False)
    op.create_index('idx_audit_article', 'audit_records', ['article_code'], unique=False)

    # 6. daily_reports table
    op.create_table(
        'daily_reports',
        sa.Column('daily_report_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('report_date', sa.Date(), nullable=False),
        sa.Column('total_audit_articles', sa.Integer(), nullable=False),
        sa.Column('total_addition_amount', sa.Integer(), nullable=False),
        sa.Column('total_shrinkage_amount', sa.Integer(), nullable=False),
        sa.Column('total_addition_value', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('total_shrinkage_value', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['record_tenants.tenant_id'], ondelete='RESTRICT', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('daily_report_id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('idx_daily_reports_tenant_date', 'daily_reports', ['tenant_id', 'report_date'], unique=True)

    # 7. critical_shrinkage_alerts table
    op.create_table(
        'critical_shrinkage_alerts',
        sa.Column('alert_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('article_code', sa.String(length=100), nullable=False),
        sa.Column('batch_number', sa.String(length=100), nullable=False),
        sa.Column('expiration_date', sa.Date(), nullable=False),
        sa.Column('days_to_expiration', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.Enum('RED', 'YELLOW', 'GREEN', name='risklevel'), nullable=False),
        sa.Column('stock_at_risk', sa.Integer(), nullable=False),
        sa.Column('amount_at_risk', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['record_tenants.tenant_id'], ondelete='RESTRICT', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('alert_id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index('idx_alerts_tenant_risk', 'critical_shrinkage_alerts', ['tenant_id', 'risk_level', 'expiration_date'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_alerts_tenant_risk', table_name='critical_shrinkage_alerts')
    op.drop_table('critical_shrinkage_alerts')

    op.drop_index('idx_daily_reports_tenant_date', table_name='daily_reports')
    op.drop_table('daily_reports')

    op.drop_index('idx_audit_article', table_name='audit_records')
    op.drop_index('idx_audit_tenant_scan', table_name='audit_records')
    op.drop_table('audit_records')

    op.drop_table('record_tenants')
    op.drop_table('user_roles')
    op.drop_table('roles')

    op.drop_index('idx_users_branch_id', table_name='users')
    op.drop_table('users')
