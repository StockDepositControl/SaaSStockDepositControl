from sqlalchemy import BigInteger, Integer

from backend.adapters.repositories.models import (
    Articulo,
    AuditRecord,
    RecordTenant,
    StockPorDeposito,
    WorkSession,
)


def test_stock_pk_prefix_matches_kpi_filter():
    """Out-of-stock KPI filters by (id_empresa, id_sucursal, id_deposito): must be the PK prefix."""
    pk_cols = [c.name for c in StockPorDeposito.__table__.primary_key.columns]
    assert pk_cols[:3] == ["id_empresa", "id_sucursal", "id_deposito"]
    assert "stock_real" in StockPorDeposito.__table__.columns


def test_articles_db_immutability_guard():
    """Client legacy schema must not carry audit/session columns."""
    forbidden = {"session_id", "fue_auditado", "audit_quantity", "tenant_id"}
    for model in (Articulo, StockPorDeposito):
        cols = {c.name for c in model.__table__.columns}
        assert not (forbidden & cols), f"{model.__tablename__} leaked analytics columns"


def test_audit_records_tenant_and_session_non_nullable():
    cols = AuditRecord.__table__.columns
    for name in ("tenant_id", "session_id", "action_type", "valorized_amount", "article_code"):
        assert cols[name].nullable is False, f"audit_records.{name} must be NOT NULL"


def test_work_sessions_tenant_non_nullable():
    assert WorkSession.__table__.columns["tenant_id"].nullable is False


def test_audit_records_session_fk_rules():
    fks = [
        fk
        for fk in AuditRecord.__table__.foreign_keys
        if fk.column.table.name == "work_sessions"
    ]
    assert len(fks) == 1
    assert fks[0].ondelete == "RESTRICT"
    assert fks[0].onupdate == "CASCADE"


def test_audit_records_session_index_columns():
    idx = next(
        (i for i in AuditRecord.__table__.indexes if i.name == "idx_audit_session_article_ts"),
        None,
    )
    assert idx is not None, "Missing idx_audit_session_article_ts"
    assert [c.name for c in idx.columns] == ["session_id", "article_code", "scan_timestamp"]


def test_tenant_leading_indexes_on_analytics_tables():
    for table, idx_name in (
        (WorkSession.__table__, "idx_ws_lookup"),
        (AuditRecord.__table__, "idx_audit_tenant_scan"),
    ):
        idx = next((i for i in table.indexes if i.name == idx_name), None)
        assert idx is not None, f"Missing {idx_name}"
        assert [c.name for c in idx.columns][0] == "tenant_id"


def test_session_id_type_is_bigint_with_sqlite_variant():
    col_type = AuditRecord.__table__.columns["session_id"].type
    assert isinstance(col_type, (BigInteger, Integer))


def test_orm_cascades_declared():
    assert "delete-orphan" in RecordTenant.work_sessions.property.cascade
    assert "delete-orphan" in WorkSession.audit_records.property.cascade
    assert "delete-orphan" in RecordTenant.audit_records.property.cascade
