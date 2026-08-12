"""alter_tenant_id_to_varchar

Revision ID: d3e4f5a6b7c8
Revises: b1c2d3e4f5a6
Create Date: 2026-08-10 09:23:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Drop foreign keys
    op.drop_constraint('work_sessions_ibfk_1', 'work_sessions', type_='foreignkey')
    op.drop_constraint('audit_records_ibfk_1', 'audit_records', type_='foreignkey')
    op.drop_constraint('daily_reports_ibfk_1', 'daily_reports', type_='foreignkey')
    op.drop_constraint('critical_shrinkage_alerts_ibfk_1', 'critical_shrinkage_alerts', type_='foreignkey')

    # Step 2: Alter columns to VARCHAR(50)
    with op.batch_alter_table('record_tenants') as batch_op:
        batch_op.alter_column('tenant_id', type_=sa.String(50), existing_nullable=False, autoincrement=False)

    with op.batch_alter_table('work_sessions') as batch_op:
        batch_op.alter_column('tenant_id', type_=sa.String(50), existing_nullable=False)

    with op.batch_alter_table('audit_records') as batch_op:
        batch_op.alter_column('tenant_id', type_=sa.String(50), existing_nullable=False)

    with op.batch_alter_table('daily_reports') as batch_op:
        batch_op.alter_column('tenant_id', type_=sa.String(50), existing_nullable=False)

    with op.batch_alter_table('critical_shrinkage_alerts') as batch_op:
        batch_op.alter_column('tenant_id', type_=sa.String(50), existing_nullable=False)

    # Step 3: Re-create foreign keys
    op.create_foreign_key('work_sessions_ibfk_1', 'work_sessions', 'record_tenants', ['tenant_id'], ['tenant_id'], ondelete='RESTRICT', onupdate='CASCADE')        
    op.create_foreign_key('audit_records_ibfk_1', 'audit_records', 'record_tenants', ['tenant_id'], ['tenant_id'], ondelete='RESTRICT', onupdate='CASCADE')        
    op.create_foreign_key('daily_reports_ibfk_1', 'daily_reports', 'record_tenants', ['tenant_id'], ['tenant_id'], ondelete='RESTRICT', onupdate='CASCADE')        
    op.create_foreign_key('critical_shrinkage_alerts_ibfk_1', 'critical_shrinkage_alerts', 'record_tenants', ['tenant_id'], ['tenant_id'], ondelete='RESTRICT', onupdate='CASCADE')



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('record_tenants', schema=None) as batch_op:
        batch_op.alter_column('tenant_id',
               existing_type=sa.String(length=50),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True)

    with op.batch_alter_table('critical_shrinkage_alerts', schema=None) as batch_op:
        batch_op.alter_column('tenant_id',
               existing_type=sa.String(length=50),
               type_=sa.Integer(),
               existing_nullable=False)

    with op.batch_alter_table('daily_reports', schema=None) as batch_op:
        batch_op.alter_column('tenant_id',
               existing_type=sa.String(length=50),
               type_=sa.Integer(),
               existing_nullable=False)

    with op.batch_alter_table('audit_records', schema=None) as batch_op:
        batch_op.alter_column('tenant_id',
               existing_type=sa.String(length=50),
               type_=sa.Integer(),
               existing_nullable=False)

    with op.batch_alter_table('work_sessions', schema=None) as batch_op:
        batch_op.alter_column('tenant_id',
               existing_type=sa.String(length=50),
               type_=sa.Integer(),
               existing_nullable=False)
