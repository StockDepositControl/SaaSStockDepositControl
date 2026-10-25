import pytest
from backend.adapters.repositories.models import (
    BaseAnalytics,
    BaseArticles,
    BaseUsers,
    RecordTenant,
)
from sqlalchemy import create_engine, inspect


@pytest.fixture(scope="module")
def inspector():
    """Setup an in-memory SQLite database to inspect declarative schema metadata."""
    engine = create_engine("sqlite:///:memory:")
    BaseArticles.metadata.create_all(engine)
    BaseUsers.metadata.create_all(engine)
    BaseAnalytics.metadata.create_all(engine)
    return inspect(engine)


def test_daily_reports_columns_integrity(inspector):
    """1. Table Metadata Integrity: Assert daily_reports has branch_id,
    total_processed_units, and net_patrimonial_variation."""
    tables = inspector.get_table_names()
    assert "daily_reports" in tables, (
        "Table 'daily_reports' missing from analytics schema."
    )

    columns = {col["name"]: col for col in inspector.get_columns("daily_reports")}
    assert "branch_id" in columns, "Missing 'branch_id' column in 'daily_reports'."
    assert "total_processed_units" in columns, (
        "Missing 'total_processed_units' column in 'daily_reports'."
    )
    assert "net_patrimonial_variation" in columns, (
        "Missing 'net_patrimonial_variation' column in 'daily_reports'."
    )
    assert "total_addition_amount" in columns, (
        "Missing 'total_addition_amount' column in 'daily_reports'."
    )
    assert "total_shrinkage_amount" in columns, (
        "Missing 'total_shrinkage_amount' column in 'daily_reports'."
    )
    assert "total_addition_value" in columns, (
        "Missing 'total_addition_value' column in 'daily_reports'."
    )
    assert "total_shrinkage_value" in columns, (
        "Missing 'total_shrinkage_value' column in 'daily_reports'."
    )

    # Type assertions
    assert "INT" in str(columns["branch_id"]["type"]).upper()
    assert "INT" in str(columns["total_processed_units"]["type"]).upper()
    net_var_type = str(columns["net_patrimonial_variation"]["type"]).upper()
    assert "NUMERIC" in net_var_type or "DECIMAL" in net_var_type


def test_daily_reports_unique_composite_index(inspector):
    """2. Unique Composite Index: Assert idx_daily_reports_tenant_branch_date exists and
    idx_daily_reports_tenant_date is absent."""
    indexes = inspector.get_indexes("daily_reports")
    idx_map = {idx["name"]: idx for idx in indexes}

    assert "idx_daily_reports_tenant_branch_date" in idx_map, (
        "Missing unique composite index 'idx_daily_reports_tenant_branch_date' on "
        "daily_reports."
    )
    branch_date_idx = idx_map["idx_daily_reports_tenant_branch_date"]
    assert branch_date_idx["column_names"] == [
        "tenant_id",
        "branch_id",
        "report_date",
    ], (
        "Expected columns ['tenant_id', 'branch_id', 'report_date'], got "
        f"{branch_date_idx['column_names']}"
    )
    assert (
        branch_date_idx.get("unique") is True or branch_date_idx.get("unique") == 1
    ), "Index 'idx_daily_reports_tenant_branch_date' must be unique."

    assert "idx_daily_reports_tenant_date" not in idx_map, (
        "Obsolete index 'idx_daily_reports_tenant_date' must be removed."
    )


def test_record_tenant_daily_reports_cascade():
    """3. Foreign Keys & Cascade: Assert RecordTenant.daily_reports cascade delete-
    orphan is preserved."""
    cascade_rules = RecordTenant.daily_reports.property.cascade
    assert "delete-orphan" in cascade_rules, (
        "RecordTenant.daily_reports must specify delete-orphan cascade."
    )
    assert "delete" in cascade_rules, (
        "RecordTenant.daily_reports must specify delete cascade."
    )


def test_audit_records_supporting_indexes(inspector):
    """Verify supporting indexes on audit_records for daily aggregation and filtering
    fallbacks."""
    indexes = inspector.get_indexes("audit_records")
    idx_map = {idx["name"]: idx for idx in indexes}

    assert "idx_audit_tenant_scan" in idx_map, (
        "Missing 'idx_audit_tenant_scan' on audit_records."
    )
    assert idx_map["idx_audit_tenant_scan"]["column_names"] == [
        "tenant_id",
        "scan_timestamp",
    ]

    assert "idx_audit_goods_received" in idx_map, (
        "Missing 'idx_audit_goods_received' on audit_records."
    )
    assert idx_map["idx_audit_goods_received"]["column_names"] == [
        "tenant_id",
        "action_type",
        "scan_timestamp",
    ]

    assert "idx_audit_shrinkage" in idx_map, (
        "Missing 'idx_audit_shrinkage' on audit_records."
    )
    assert idx_map["idx_audit_shrinkage"]["column_names"] == [
        "tenant_id",
        "action_type",
        "scan_timestamp",
    ]


def test_client_articles_db_immutability(inspector):
    """4. Client DB Protection: Assert BaseArticles tables and schema remain intact and
    unaltered."""
    tables = inspector.get_table_names()
    expected_articles_tables = [
        "articulos",
        "familias",
        "grupos",
        "marcas",
        "stock_por_deposito",
        "lotes_por_deposito",
        "codigos_barra_articulo",
        "empresas",
        "sucursales",
        "depositos",
    ]
    for table_name in expected_articles_tables:
        assert table_name in tables, (
            f"Expected legacy table '{table_name}' in BaseArticles metadata."
        )
