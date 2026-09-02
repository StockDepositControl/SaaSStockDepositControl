import pytest
from sqlalchemy import create_engine, inspect
from backend.adapters.repositories.models import (
    BaseArticles, BaseUsers, BaseAnalytics, RecordTenant, WorkSession, AuditRecord, Articulo
)


@pytest.fixture(scope="module")
def analytics_inspector():
    engine = create_engine("sqlite:///:memory:")
    BaseArticles.metadata.create_all(engine)
    BaseUsers.metadata.create_all(engine)
    BaseAnalytics.metadata.create_all(engine)
    return inspect(engine)


def test_work_sessions_table_exists(analytics_inspector):
    """Asserts that the work_sessions table exists in db_analytics."""
    tables = analytics_inspector.get_table_names()
    assert 'work_sessions' in tables, "Table 'work_sessions' missing from db_analytics schema."


def test_work_sessions_has_required_columns(analytics_inspector):
    """Asserts that work_sessions has all specified columns and correct nullability."""
    cols = {col['name']: col for col in analytics_inspector.get_columns('work_sessions')}
    expected_cols = {'session_id', 'tenant_id', 'branch_id', 'opened_at', 'closed_at', 'status', 'created_at'}
    assert expected_cols.issubset(cols.keys()), f"Missing columns in work_sessions: {expected_cols - set(cols.keys())}"
    assert cols['session_id']['primary_key'] == 1, "session_id must be PK"
    assert cols['tenant_id']['nullable'] is False, "tenant_id must be non-nullable"
    assert cols['branch_id']['nullable'] is False, "branch_id must be non-nullable"
    assert cols['opened_at']['nullable'] is False, "opened_at must be non-nullable"
    assert cols['closed_at']['nullable'] is True, "closed_at must be nullable"
    assert cols['status']['nullable'] is False, "status must be non-nullable"


def test_work_sessions_tenant_fk(analytics_inspector):
    """Asserts that work_sessions has an explicit FK constraint to record_tenants with RESTRICT/CASCADE."""
    fks = analytics_inspector.get_foreign_keys('work_sessions')
    tenant_fk = next((fk for fk in fks if fk['referred_table'] == 'record_tenants'), None)
    assert tenant_fk is not None, "Missing foreign key constraint from work_sessions to record_tenants."
    assert tenant_fk.get('options', {}).get('ondelete') == 'RESTRICT', "FK ondelete should be RESTRICT"
    assert tenant_fk.get('options', {}).get('onupdate') == 'CASCADE', "FK onupdate should be CASCADE"


def test_work_sessions_indexes(analytics_inspector):
    """Asserts that multi-tenant leading indexes idx_ws_lookup and idx_ws_status are defined."""
    indexes = analytics_inspector.get_indexes('work_sessions')
    idx_names = [idx['name'] for idx in indexes]
    assert 'idx_ws_lookup' in idx_names, "Missing index idx_ws_lookup on work_sessions"
    assert 'idx_ws_status' in idx_names, "Missing index idx_ws_status on work_sessions"

    lookup_idx = next(idx for idx in indexes if idx['name'] == 'idx_ws_lookup')
    assert lookup_idx['column_names'] == ['tenant_id', 'branch_id', 'opened_at', 'closed_at']

    status_idx = next(idx for idx in indexes if idx['name'] == 'idx_ws_status')
    assert status_idx['column_names'] == ['tenant_id', 'branch_id', 'status']


def test_audit_records_has_session_id(analytics_inspector):
    """Asserts that audit_records contains non-nullable session_id column."""
    columns = {col['name']: col for col in analytics_inspector.get_columns('audit_records')}
    assert 'session_id' in columns, "Table audit_records missing session_id column"
    assert columns['session_id']['nullable'] is False, "session_id column on audit_records must be non-nullable"


def test_audit_records_session_id_fk(analytics_inspector):
    """Asserts that audit_records has FK to work_sessions.session_id with RESTRICT/CASCADE."""
    fks = analytics_inspector.get_foreign_keys('audit_records')
    session_fk = next((fk for fk in fks if fk['referred_table'] == 'work_sessions'), None)
    assert session_fk is not None, "Missing foreign key constraint from audit_records to work_sessions"
    assert session_fk.get('options', {}).get('ondelete') == 'RESTRICT', "FK ondelete should be RESTRICT"
    assert session_fk.get('options', {}).get('onupdate') == 'CASCADE', "FK onupdate should be CASCADE"


def test_audit_records_session_article_index(analytics_inspector):
    """Asserts that covering index idx_audit_session_article_ts exists for fast EXISTS subqueries and batch ordering."""
    indexes = analytics_inspector.get_indexes('audit_records')
    idx_names = [idx['name'] for idx in indexes]
    assert 'idx_audit_session_article_ts' in idx_names, "Missing index idx_audit_session_article_ts on audit_records"

    session_art_idx = next(idx for idx in indexes if idx['name'] == 'idx_audit_session_article_ts')
    assert session_art_idx['column_names'] == ['session_id', 'article_code', 'scan_timestamp']


def test_work_session_cascade_from_tenant():
    """Asserts ORM model level cascade rule from RecordTenant to WorkSession."""
    assert "delete-orphan" in RecordTenant.work_sessions.property.cascade
    assert "all" in RecordTenant.work_sessions.property.cascade or "delete" in RecordTenant.work_sessions.property.cascade


def test_work_session_cascade_to_audit_records():
    """Asserts ORM model level cascade rule from WorkSession to AuditRecord."""
    assert "delete-orphan" in WorkSession.audit_records.property.cascade
    assert "all" in WorkSession.audit_records.property.cascade or "delete" in WorkSession.audit_records.property.cascade


def test_db_articles_not_modified(analytics_inspector):
    """Immutability Guard: Asserts that articulos table structure remains strictly untouched."""
    art_cols = [c['name'] for c in analytics_inspector.get_columns('articulos')]
    assert 'session_id' not in art_cols, "Violation: session_id found in articulos table"
    assert 'fue_auditado' not in art_cols, "Violation: fue_auditado found in articulos table"
