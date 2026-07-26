import pytest
from sqlalchemy import create_engine, inspect
from backend.adapters.repositories.models import Base, Familia, Grupo, Articulo, StockPorDeposito, LotePorDeposito, AuditoriaRegistro

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
    fks = inspector.get_foreign_keys('stock_por_deposito')
    articulos_fk = next((fk for fk in fks if fk['referred_table'] == 'articulos'), None)
    assert articulos_fk is not None, "StockPorDeposito must have a foreign key to Articulos"
    assert articulos_fk.get('options', {}).get('ondelete') == 'CASCADE', "Foreign key should ON DELETE CASCADE"

def test_lotes_por_deposito_fk_cascade(inspector):
    fks = inspector.get_foreign_keys('lotes_por_deposito')
    articulos_fk = next((fk for fk in fks if fk['referred_table'] == 'articulos'), None)
    assert articulos_fk is not None, "LotePorDeposito must have a foreign key to Articulos"
    assert articulos_fk.get('options', {}).get('ondelete') == 'CASCADE', "Foreign key should ON DELETE CASCADE"

def test_auditorias_registro_fk_cascades(inspector):
    fks = inspector.get_foreign_keys('auditorias_registro')
    articulos_fk = next((fk for fk in fks if fk['referred_table'] == 'articulos'), None)
    assert articulos_fk is not None, "AuditoriaRegistro must have a foreign key to Articulos"
    assert articulos_fk.get('options', {}).get('ondelete') == 'CASCADE', "Articulos FK should ON DELETE CASCADE"

    usuarios_fk = next((fk for fk in fks if fk['referred_table'] == 'usuarios'), None)
    assert usuarios_fk is not None, "AuditoriaRegistro must have a foreign key to Usuarios"
    assert usuarios_fk.get('options', {}).get('ondelete') == 'CASCADE', "Usuarios FK should ON DELETE CASCADE"

def test_composite_indexes_lead_with_tenant_id(inspector):
    multi_tenant_tables = ['usuarios', 'articulos', 'stock_por_deposito', 'lotes_por_deposito', 'auditorias_registro']
    for table in multi_tenant_tables:
        indexes = inspector.get_indexes(table)
        for idx in indexes:
            column_names = idx['column_names']
            if len(column_names) > 1 and 'tenant_id' in column_names:
                assert column_names[0] == 'tenant_id', f"Index '{idx['name']}' on '{table}' does not have leading 'tenant_id'"

def test_articulos_decimal_precision(inspector):
    columns = inspector.get_columns('articulos')
    pcio_col = next((c for c in columns if c['name'] == 'pcio_com_siva'), None)
    assert pcio_col is not None, "pcio_com_siva column missing from articulos"
    # Column type assertion
    assert 'DECIMAL' in str(pcio_col['type']).upper() or 'NUMERIC' in str(pcio_col['type']).upper()

def test_orm_relationship_cascades():
    # Verify ORM model declarations specify cascade rules
    assert "delete-orphan" in Familia.grupos.property.cascade
    assert "delete" in Familia.grupos.property.cascade
