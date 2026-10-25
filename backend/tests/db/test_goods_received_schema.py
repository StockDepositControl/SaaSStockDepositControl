import os
import re

import pytest
from backend.adapters.repositories.models import (
    AuditRecord,
    BaseAnalytics,
    BaseArticles,
    BaseUsers,
    RecordTenant,
    WorkSession,
)
from sqlalchemy import Numeric, create_engine, inspect
from sqlalchemy.orm import class_mapper


@pytest.fixture(scope="module")
def db_inspector():
    """Setup an in-memory SQLite database to inspect declarative schema metadata."""
    engine = create_engine("sqlite:///:memory:")
    BaseArticles.metadata.create_all(engine)
    BaseUsers.metadata.create_all(engine)
    BaseAnalytics.metadata.create_all(engine)
    return inspect(engine)


def test_audit_records_metadata_integrity(db_inspector):
    """
    1. Confirm audit_records table exists with all required columns and proper types.
    """
    tables = db_inspector.get_table_names()
    assert "audit_records" in tables, "Table audit_records not found in metadata"

    columns = {col["name"]: col for col in db_inspector.get_columns("audit_records")}
    required_columns = [
        "audit_id",
        "tenant_id",
        "session_id",
        "branch_id",
        "warehouse_id",
        "article_code",
        "user_id",
        "action_type",
        "affected_amount",
        "applied_unit_cost",
        "applied_vat_rate",
        "valorized_amount",
        "scan_timestamp",
        "observation",
    ]

    for col_name in required_columns:
        assert col_name in columns, (
            f"Missing required column '{col_name}' on audit_records"
        )

    # Verify non-nullability where required
    non_nullable = [
        "audit_id",
        "tenant_id",
        "session_id",
        "branch_id",
        "article_code",
        "user_id",
        "action_type",
        "affected_amount",
        "applied_unit_cost",
        "applied_vat_rate",
        "valorized_amount",
        "scan_timestamp",
    ]
    for col_name in non_nullable:
        assert not columns[col_name]["nullable"], (
            f"Column '{col_name}' should be non-nullable"
        )

    # Verify financial precision columns
    table = AuditRecord.__table__
    assert isinstance(table.c.applied_unit_cost.type, Numeric)
    assert table.c.applied_unit_cost.type.precision == 15
    assert table.c.applied_unit_cost.type.scale == 4

    assert isinstance(table.c.applied_vat_rate.type, Numeric)
    assert table.c.applied_vat_rate.type.precision == 5
    assert table.c.applied_vat_rate.type.scale == 4

    assert isinstance(table.c.valorized_amount.type, Numeric)
    assert table.c.valorized_amount.type.precision == 15
    assert table.c.valorized_amount.type.scale == 4


def test_multi_tenant_isolation_and_composite_index():
    """2. Verify tenant_id is present and indexed as the leading column on
    idx_audit_goods_received."""
    table = AuditRecord.__table__
    index_names = {ix.name: ix for ix in table.indexes}

    assert "idx_audit_goods_received" in index_names, (
        "Missing idx_audit_goods_received index on AuditRecord"
    )
    gr_idx = index_names["idx_audit_goods_received"]
    idx_cols = [col.name for col in gr_idx.columns]

    # Verify leading column is tenant_id
    assert idx_cols[0] == "tenant_id", (
        "idx_audit_goods_received must have tenant_id as leading column, got: "
        f"{idx_cols}"
    )
    assert idx_cols == ["tenant_id", "action_type", "scan_timestamp"], (
        f"Unexpected column order: {idx_cols}"
    )

    # Verify idx_audit_article index for JOIN optimization
    assert "idx_audit_article" in index_names, (
        "Missing idx_audit_article index on AuditRecord"
    )
    article_idx = index_names["idx_audit_article"]
    assert [c.name for c in article_idx.columns] == ["article_code"]


def test_cascade_rules_on_relationships():
    """3. Confirm explicit cascade rules on RecordTenant.audit_records and
    WorkSession.audit_records."""
    # Check RecordTenant -> audit_records cascade
    tenant_mapper = class_mapper(RecordTenant)
    tenant_rel = tenant_mapper.relationships["audit_records"]
    assert tenant_rel.cascade.delete, (
        "RecordTenant.audit_records must have cascade delete"
    )
    assert tenant_rel.cascade.delete_orphan, (
        "RecordTenant.audit_records must have cascade delete-orphan"
    )

    # Check WorkSession -> audit_records cascade
    session_mapper = class_mapper(WorkSession)
    session_rel = session_mapper.relationships["audit_records"]
    assert session_rel.cascade.delete, (
        "WorkSession.audit_records must have cascade delete"
    )
    assert session_rel.cascade.delete_orphan, (
        "WorkSession.audit_records must have cascade delete-orphan"
    )


def test_client_database_immutability(db_inspector):
    """4. Assert that no schema migration scripts in analytics alter tables in
    BaseArticles and model remains untouched."""
    legacy_tables = set(BaseArticles.metadata.tables.keys())
    assert "articulos" in legacy_tables
    assert "stock_por_deposito" in legacy_tables

    # 1. Model level immutability: Ensure no analytics or audit fields were leaked into
    # legacy tables
    art_cols = [col["name"] for col in db_inspector.get_columns("articulos")]
    stock_cols = [col["name"] for col in db_inspector.get_columns("stock_por_deposito")]

    forbidden_fields = [
        "audit_id",
        "session_id",
        "audit_quantity",
        "action_type",
        "valorized_amount",
    ]
    for field in forbidden_fields:
        assert field not in art_cols, (
            f"Violation: '{field}' leaked into legacy 'articulos' table"
        )
        assert field not in stock_cols, (
            f"Violation: '{field}' leaked into legacy 'stock_por_deposito' table"
        )

    # 2. Migration level immutability: Ensure versions_analytics migrations never touch
    # BaseArticles tables
    analytics_migrations_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../migrations/versions_analytics")
    )
    prohibited_ops = ["drop_table", "alter_column", "drop_column", "rename_table"]

    checked_scripts = 0
    for root, _, files in os.walk(analytics_migrations_dir):
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                checked_scripts += 1
                filepath = os.path.join(root, f)
                with open(filepath, "r", encoding="utf-8") as script_file:
                    content = script_file.read()
                    for tbl in legacy_tables:
                        for op in prohibited_ops:
                            pattern = rf"{op}\s*\(\s*['\"]{tbl}['\"]"
                            match = re.search(pattern, content)
                            assert not match, (
                                f"Violation: analytics migration {f} contains "
                                f"forbidden alteration '{op}' on legacy table '{tbl}'"
                            )

    assert checked_scripts > 0, (
        "Expected to find and verify analytics migration scripts"
    )
