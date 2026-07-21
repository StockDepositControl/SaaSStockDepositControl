import pytest
from sqlalchemy import create_engine, inspect
from backend.adapters.repositories.models import Base

@pytest.fixture(scope="module")
def inspector():
    # Setup an in-memory SQLite database to inspect the declarative schema
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return inspect(engine)

def test_usuario_has_is_active(inspector):
    columns = [col['name'] for col in inspector.get_columns('usuarios')]
    assert 'is_active' in columns, "Column 'is_active' is missing from 'usuarios' table."

def test_stock_has_stock_teorico(inspector):
    columns = [col['name'] for col in inspector.get_columns('stock_por_deposito')]
    assert 'stock_teorico' in columns, "Column 'stock_teorico' is missing from 'stock_por_deposito' table."

def test_multi_tenant_tables_have_tenant_id(inspector):
    # Tables that represent multi-tenant entities
    multi_tenant_tables = [
        'usuarios',
        'articulos',
        'stock_por_deposito',
        'lotes_por_deposito',
        'auditorias_registro'
    ]
    for table in multi_tenant_tables:
        columns = [col['name'] for col in inspector.get_columns(table)]
        assert 'tenant_id' in columns, f"Table '{table}' is missing the multi-tenant key 'tenant_id'."

def test_foreign_key_cascades_present(inspector):
    # Check that cascades exist for multi-tenant linkage
    fks = inspector.get_foreign_keys('stock_por_deposito')
    
    # In StockPorDeposito, we expect the composite FK to 'articulos' to CASCADE on delete
    articulos_fk = next((fk for fk in fks if fk['referred_table'] == 'articulos'), None)
    assert articulos_fk is not None, "StockPorDeposito must have a foreign key to Articulos"
    assert articulos_fk.get('options', {}).get('ondelete') == 'CASCADE', "Foreign key should ON DELETE CASCADE"
