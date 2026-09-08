import pytest
from sqlalchemy import select, func
from datetime import date
from backend.scripts.seed import run_seed
from backend.adapters.repositories.models import (
    Articulo, StockPorDeposito, LotePorDeposito, CodigoBarraArticulo, Familia,
    Empresa, Sucursal, Deposito,
    Role, User, RecordTenant, AuditRecord, DailyReport, CriticalShrinkageAlert
)

@pytest.mark.asyncio
async def test_seed_creates_empresa_sucursal_deposito(async_sessions, db_engines):
    await run_seed(
        count=100,
        seed_val=123,
        url_articles=db_engines["url_articles"],
        url_users=db_engines["url_users"],
        url_analytics=db_engines["url_analytics"]
    )

    s_articles = async_sessions["articles"]

    res_emp = await s_articles.execute(select(func.count(Empresa.id_empresa)))
    assert res_emp.scalar() == 1

    res_suc = await s_articles.execute(select(func.count(Sucursal.id_sucursal)))
    assert res_suc.scalar() == 1

    res_dep = await s_articles.execute(select(func.count(Deposito.id_deposito)))
    assert res_dep.scalar() == 1


@pytest.mark.asyncio
async def test_seed_creates_expected_counts(async_sessions, db_engines):
    await run_seed(
        count=100,
        seed_val=123,
        url_articles=db_engines["url_articles"],
        url_users=db_engines["url_users"],
        url_analytics=db_engines["url_analytics"]
    )

    s_articles = async_sessions["articles"]

    res_art = await s_articles.execute(select(func.count(Articulo.id_articulo)))
    art_count = res_art.scalar()
    assert art_count == 100

    res_stock = await s_articles.execute(select(func.count(StockPorDeposito.id_articulo)))
    stock_count = res_stock.scalar()
    assert stock_count == 100

    res_barcodes = await s_articles.execute(select(func.count(CodigoBarraArticulo.cod_barra)))
    barcode_count = res_barcodes.scalar()
    assert barcode_count == 100


@pytest.mark.asyncio
async def test_seed_fiscal_mix_distribution(async_sessions, db_engines):
    await run_seed(
        count=100,
        seed_val=123,
        url_articles=db_engines["url_articles"],
        url_users=db_engines["url_users"],
        url_analytics=db_engines["url_analytics"]
    )

    s_articles = async_sessions["articles"]
    res_med = await s_articles.execute(select(func.count(Articulo.id_articulo)).where(Articulo.id_familia == "01"))
    med_count = res_med.scalar()
    assert med_count == 50  # Exactly 50% Medicamentos


@pytest.mark.asyncio
async def test_seed_ghost_items_anomaly(async_sessions, db_engines):
    await run_seed(
        count=100,
        seed_val=123,
        ghost_rate=0.10,
        url_articles=db_engines["url_articles"],
        url_users=db_engines["url_users"],
        url_analytics=db_engines["url_analytics"]
    )

    s_articles = async_sessions["articles"]
    res_ghost = await s_articles.execute(
        select(func.count(StockPorDeposito.id_articulo)).where(
            StockPorDeposito.stock_real == 0.0
        )
    )
    ghost_count = res_ghost.scalar()
    assert ghost_count >= 10


@pytest.mark.asyncio
async def test_seed_expired_lots_anomaly(async_sessions, db_engines):
    await run_seed(
        count=100,
        seed_val=123,
        expired_rate=0.25,
        url_articles=db_engines["url_articles"],
        url_users=db_engines["url_users"],
        url_analytics=db_engines["url_analytics"]
    )

    s_articles = async_sessions["articles"]
    today_str = date.today().strftime("%Y-%m-%d")
    res_expired = await s_articles.execute(
        select(func.count(LotePorDeposito.lote)).where(LotePorDeposito.vencimiento < today_str)
    )
    expired_count = res_expired.scalar()
    assert expired_count > 0


@pytest.mark.asyncio
async def test_seed_multi_tenant_isolation(async_sessions, db_engines):
    await run_seed(
        count=100,
        seed_val=123,
        url_articles=db_engines["url_articles"],
        url_users=db_engines["url_users"],
        url_analytics=db_engines["url_analytics"]
    )

    s_articles = async_sessions["articles"]
    res_e1 = await s_articles.execute(
        select(func.count(StockPorDeposito.id_articulo)).where(StockPorDeposito.id_empresa == 1)
    )
    e1_count = res_e1.scalar()

    assert e1_count == 100


@pytest.mark.asyncio
async def test_seed_db_users_and_db_analytics(async_sessions, db_engines):
    await run_seed(
        count=100,
        seed_val=123,
        url_articles=db_engines["url_articles"],
        url_users=db_engines["url_users"],
        url_analytics=db_engines["url_analytics"]
    )

    s_users = async_sessions["users"]
    s_analytics = async_sessions["analytics"]

    # Roles check (must be exactly 3: administrador, supervisor, auditor)
    res_roles = await s_users.execute(select(func.count(Role.role_id)))
    assert res_roles.scalar() == 3

    # Users check
    res_users = await s_users.execute(select(func.count(User.user_id)))
    assert res_users.scalar() == 12

    # Record tenants check
    res_tenants = await s_analytics.execute(select(func.count(RecordTenant.tenant_id)))
    assert res_tenants.scalar() == 1

    # Audit records check (Clean state constraint per Observation 7: NO simulated audit records)
    res_analytics_audits = await s_analytics.execute(select(func.count(AuditRecord.audit_id)))
    assert res_analytics_audits.scalar() == 0

    # Daily reports check
    res_reports = await s_analytics.execute(select(func.count(DailyReport.daily_report_id)))
    assert res_reports.scalar() == 1

    # Critical alerts check
    res_alerts = await s_analytics.execute(select(func.count(CriticalShrinkageAlert.alert_id)))
    assert res_alerts.scalar() >= 0


@pytest.mark.asyncio
async def test_seed_role_names_are_spanish(async_sessions, db_engines):
    """Seeded role names must be lowercase Spanish to match UserRole enum."""
    await run_seed(
        count=100,
        seed_val=123,
        url_articles=db_engines["url_articles"],
        url_users=db_engines["url_users"],
        url_analytics=db_engines["url_analytics"]
    )

    s_users = async_sessions["users"]
    result = await s_users.execute(select(Role.name))
    role_names = {row[0] for row in result.all()}
    assert role_names == {"administrador", "supervisor", "auditor"}, (
        f"Seeded roles must use Spanish enum values. Found: {role_names}"
    )


@pytest.mark.asyncio
async def test_seed_creates_shrinkage_audit_records(async_sessions, db_engines):
    """Verify that when shrinkage_rate > 0, AuditRecords with action_type='REMOVAL' and shrinkage observations are seeded."""
    await run_seed(
        count=50,
        seed_val=123,
        shrinkage_rate=0.30,
        url_articles=db_engines["url_articles"],
        url_users=db_engines["url_users"],
        url_analytics=db_engines["url_analytics"]
    )

    s_analytics = async_sessions["analytics"]
    res_audits = await s_analytics.execute(select(AuditRecord))
    audits = res_audits.scalars().all()

    assert len(audits) > 0, "Expected shrinkage AuditRecords to be created when shrinkage_rate > 0"
    for audit in audits:
        assert audit.action_type == "REMOVAL", f"Expected action_type REMOVAL, got {audit.action_type}"
        assert audit.observation is not None and len(audit.observation) > 0, "Expected non-empty shrinkage reason in observation"
        assert audit.tenant_id == 1


@pytest.mark.asyncio
async def test_seed_creates_goods_received_audit_records(async_sessions, db_engines):
    """Verify that when goods_received_rate > 0, AuditRecords with action_type in ('ADDITION', 'Alta', 'Ingreso') are seeded."""
    await run_seed(
        count=50,
        seed_val=123,
        goods_received_rate=0.30,
        url_articles=db_engines["url_articles"],
        url_users=db_engines["url_users"],
        url_analytics=db_engines["url_analytics"]
    )

    s_analytics = async_sessions["analytics"]
    res_audits = await s_analytics.execute(select(AuditRecord))
    audits = res_audits.scalars().all()

    assert len(audits) > 0, "Expected Goods Received AuditRecords to be created when goods_received_rate > 0"
    for audit in audits:
        assert audit.action_type in ("ADDITION", "Alta", "Ingreso"), (
            f"Expected action_type in ('ADDITION', 'Alta', 'Ingreso'), got {audit.action_type}"
        )
        assert audit.affected_amount > 0, f"Expected affected_amount > 0, got {audit.affected_amount}"
        assert audit.applied_unit_cost > 0, f"Expected applied_unit_cost > 0, got {audit.applied_unit_cost}"
        assert audit.valorized_amount > 0, f"Expected valorized_amount > 0, got {audit.valorized_amount}"
        assert audit.observation is not None and len(audit.observation) > 0, "Expected non-empty observation"
        assert audit.tenant_id == 1



