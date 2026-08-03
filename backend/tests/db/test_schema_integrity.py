import pytest
from sqlalchemy import create_engine, inspect
from backend.adapters.repositories.models import BaseArticles, BaseUsers, BaseAnalytics, Familia, Grupo, Articulo, StockPorDeposito, LotePorDeposito, CodigoBarraArticulo

@pytest.fixture(scope="module")
def inspector():
    # Setup an in-memory SQLite database to inspect the declarative schema
    engine = create_engine("sqlite:///:memory:")
    BaseArticles.metadata.create_all(engine)
    BaseUsers.metadata.create_all(engine)
    BaseAnalytics.metadata.create_all(engine)
    return inspect(engine)

def test_stock_and_lotes_have_id_empresa(inspector):
    empresa_tables = ['stock_por_deposito', 'lotes_por_deposito']
    for table in empresa_tables:
        columns = [col['name'] for col in inspector.get_columns(table)]
        assert 'id_empresa' in columns, f"Table '{table}' is missing multi-tenant identifier 'id_empresa'."

def test_codigos_barra_articulo_exists(inspector):
    tables = inspector.get_table_names()
    assert 'codigos_barra_articulo' in tables, "Table 'codigos_barra_articulo' missing from schema."
    columns = [col['name'] for col in inspector.get_columns('codigos_barra_articulo')]
    assert 'id_articulo' in columns
    assert 'cod_barra' in columns

def test_foreign_key_cascades_present(inspector):
    fks = inspector.get_foreign_keys('stock_por_deposito')
    articulos_fk = next((fk for fk in fks if fk['referred_table'] == 'articulos'), None)
    assert articulos_fk is not None, "StockPorDeposito must have a foreign key to Articulos"
    assert articulos_fk.get('options', {}).get('ondelete') == 'RESTRICT', "Foreign key should ON DELETE RESTRICT"
    assert articulos_fk.get('options', {}).get('onupdate') == 'CASCADE', "Foreign key should ON UPDATE CASCADE"

def test_lotes_por_deposito_fk_cascade(inspector):
    fks = inspector.get_foreign_keys('lotes_por_deposito')
    articulos_fk = next((fk for fk in fks if fk['referred_table'] == 'articulos'), None)
    assert articulos_fk is not None, "LotePorDeposito must have a foreign key to Articulos"
    assert articulos_fk.get('options', {}).get('ondelete') == 'RESTRICT', "Foreign key should ON DELETE RESTRICT"
    assert articulos_fk.get('options', {}).get('onupdate') == 'CASCADE', "Foreign key should ON UPDATE CASCADE"

def test_codigos_barra_articulo_fk(inspector):
    fks = inspector.get_foreign_keys('codigos_barra_articulo')
    articulos_fk = next((fk for fk in fks if fk['referred_table'] == 'articulos'), None)
    assert articulos_fk is not None, "CodigoBarraArticulo must have a foreign key to Articulos"
    assert articulos_fk.get('options', {}).get('ondelete') == 'RESTRICT', "Foreign key should ON DELETE RESTRICT"

def test_articulos_decimal_price(inspector):
    columns = inspector.get_columns('articulos')
    pcio_col = next((c for c in columns if c['name'] == 'pcio_com_siva'), None)
    assert pcio_col is not None, "pcio_com_siva column missing from articulos"
    col_type_str = str(pcio_col['type']).upper()
    assert 'NUMERIC' in col_type_str or 'DECIMAL' in col_type_str, f"Expected NUMERIC/DECIMAL for pcio_com_siva, got {col_type_str}"

def test_articulos_fulltext_index_declared(inspector):
    indexes = inspector.get_indexes('articulos')
    idx_names = [idx['name'] for idx in indexes]
    assert 'ft_articulos_des_articulo' in idx_names, "Missing fulltext index 'ft_articulos_des_articulo' on articulos table."


def test_orm_relationship_cascades():
    # Verify ORM model declarations specify cascade rules
    assert "delete-orphan" in Familia.grupos.property.cascade
    assert "delete" in Familia.grupos.property.cascade

def test_db_users_tables_exist(inspector):
    tables = inspector.get_table_names()
    for db_users_table in ['users', 'roles', 'user_roles']:
        assert db_users_table in tables, f"Table '{db_users_table}' missing from schema."

def test_db_analytics_tables_exist(inspector):
    tables = inspector.get_table_names()
    for analytics_table in ['record_tenants', 'audit_records', 'daily_reports', 'critical_shrinkage_alerts']:
        assert analytics_table in tables, f"Table '{analytics_table}' missing from schema."

def test_user_roles_cascade(inspector):
    fks = inspector.get_foreign_keys('user_roles')
    users_fk = next((fk for fk in fks if fk['referred_table'] == 'users'), None)
    roles_fk = next((fk for fk in fks if fk['referred_table'] == 'roles'), None)
    assert users_fk is not None and users_fk.get('options', {}).get('ondelete') == 'CASCADE'
    assert roles_fk is not None and roles_fk.get('options', {}).get('ondelete') == 'CASCADE'

def test_analytics_fk_restrict(inspector):
    for table in ['audit_records', 'daily_reports', 'critical_shrinkage_alerts']:
        fks = inspector.get_foreign_keys(table)
        tenant_fk = next((fk for fk in fks if fk['referred_table'] == 'record_tenants'), None)
        assert tenant_fk is not None, f"Foreign key to record_tenants missing on '{table}'"
        assert tenant_fk.get('options', {}).get('ondelete') == 'RESTRICT', f"FK on '{table}' should be ON DELETE RESTRICT"

def test_analytics_indexes(inspector):
    audit_idx = inspector.get_indexes('audit_records')
    idx_names = [idx['name'] for idx in audit_idx]
    assert 'idx_audit_tenant_scan' in idx_names or any('tenant_id' in idx['column_names'] for idx in audit_idx)
    assert 'idx_audit_article' in idx_names or any('article_code' in idx['column_names'] for idx in audit_idx)

    alert_idx = inspector.get_indexes('critical_shrinkage_alerts')
    assert any('risk_level' in idx['column_names'] for idx in alert_idx)

def test_users_has_tenant_id(inspector):
    columns = [col['name'] for col in inspector.get_columns('users')]
    assert 'tenant_id' in columns, "Table 'users' is missing multi-tenant identifier 'tenant_id'."

def test_users_tenant_email_unique_index(inspector):
    indexes = inspector.get_indexes('users')
    tenant_email_idx = next(
        (idx for idx in indexes if set(idx['column_names']) == {'tenant_id', 'email'} and idx.get('unique')),
        None
    )
    assert tenant_email_idx is not None, "Missing unique composite index on (tenant_id, email) for users table."

def test_users_no_global_email_uniqueness(inspector):
    indexes = inspector.get_indexes('users')
    unique_constraints = inspector.get_unique_constraints('users')
    for idx in indexes:
        if idx['column_names'] == ['email'] and idx.get('unique'):
            raise AssertionError("Found standalone unique index on 'email' — must be scoped to (tenant_id, email).")
    for uc in unique_constraints:
        if uc['column_names'] == ['email']:
            raise AssertionError("Found standalone unique constraint on 'email' — must be scoped to (tenant_id, email).")

