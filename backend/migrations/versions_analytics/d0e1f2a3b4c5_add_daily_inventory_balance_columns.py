"""add_daily_inventory_balance_columns

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-09-10 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, Sequence[str], None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add branch_id, total_processed_units, net_patrimonial_variation to daily_reports and update index."""
    op.add_column('daily_reports', sa.Column('branch_id', sa.Integer(), server_default='1', nullable=False))
    op.add_column('daily_reports', sa.Column('total_processed_units', sa.Integer(), server_default='0', nullable=False))
    op.add_column('daily_reports', sa.Column('net_patrimonial_variation', sa.Numeric(precision=15, scale=4), server_default='0.0000', nullable=False))
    # Create the new index first so MySQL retains an index on tenant_id for the foreign key constraint
    op.create_index('idx_daily_reports_tenant_branch_date', 'daily_reports', ['tenant_id', 'branch_id', 'report_date'], unique=True)
    op.drop_index('idx_daily_reports_tenant_date', table_name='daily_reports')


def downgrade() -> None:
    """Downgrade schema: restore idx_daily_reports_tenant_date and remove added columns."""
    # Restore the original index first before dropping the replacement index
    op.create_index('idx_daily_reports_tenant_date', 'daily_reports', ['tenant_id', 'report_date'], unique=True)
    op.drop_index('idx_daily_reports_tenant_branch_date', table_name='daily_reports')
    op.drop_column('daily_reports', 'net_patrimonial_variation')
    op.drop_column('daily_reports', 'total_processed_units')
    op.drop_column('daily_reports', 'branch_id')
