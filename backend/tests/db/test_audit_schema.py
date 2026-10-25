from backend.adapters.repositories.models.analytics import AuditRecord
from backend.adapters.repositories.models.articles import StockPorDeposito


def test_audit_record_has_required_fallback_columns():
    """Asserts that the AuditRecord table contains the required columns for multi-tenant
    fallback routing."""
    columns = [c.name for c in AuditRecord.__table__.columns]
    assert "tenant_id" in columns, "Missing tenant_id mapping"
    assert "branch_id" in columns, "Missing branch_id mapping"
    assert "warehouse_id" in columns, "Missing warehouse_id mapping"
    assert "article_code" in columns, "Missing article_code mapping"


def test_audit_record_has_fallback_composite_index():
    """Asserts that the required composite index for fast fallback lookups exists."""
    indexes = [ix.name for ix in AuditRecord.__table__.indexes]
    assert "idx_audit_fallback" in indexes, (
        "Missing idx_audit_fallback index on AuditRecord"
    )

    # Verify index columns
    fallback_idx = next(
        ix for ix in AuditRecord.__table__.indexes if ix.name == "idx_audit_fallback"
    )
    idx_cols = [c.name for c in fallback_idx.columns]
    assert idx_cols == [
        "tenant_id",
        "branch_id",
        "warehouse_id",
        "article_code",
        "scan_timestamp",
    ]


def test_db_articles_read_only_schema_constraint():
    """Asserts that the db_articles schemas remain untampered with regarding audit
    fields."""
    columns = [c.name for c in StockPorDeposito.__table__.columns]
    assert "audit_quantity" not in columns, (
        "Violation: audit fields added to read-only db_articles table"
    )
    assert "stock_real" in columns


def test_audit_record_has_shrinkage_composite_index():
    """
    Asserts that the required composite index for shrinkage report filtering exists.
    """
    indexes = [ix.name for ix in AuditRecord.__table__.indexes]
    assert "idx_audit_shrinkage" in indexes, (
        "Missing idx_audit_shrinkage index on AuditRecord"
    )

    shrinkage_idx = next(
        ix for ix in AuditRecord.__table__.indexes if ix.name == "idx_audit_shrinkage"
    )
    idx_cols = [c.name for c in shrinkage_idx.columns]
    assert idx_cols == ["tenant_id", "action_type", "scan_timestamp"]
