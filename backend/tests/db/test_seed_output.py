import pytest
from sqlalchemy import select, func
from datetime import date
from backend.scripts.seed import run_seed
from backend.adapters.repositories.models import Articulo, StockPorDeposito, LotePorDeposito, AuditoriaRegistro, Familia

@pytest.mark.asyncio
async def test_seed_creates_expected_counts(async_session, async_db_engine):
    # Run seed script on SQLite in-memory engine
    db_url = str(async_db_engine.url)
    await run_seed(count=100, seed_val=123, database_url=db_url)

    res_art = await async_session.execute(select(func.count(Articulo.id_articulo)))
    art_count = res_art.scalar()
    assert art_count == 100

    res_stock = await async_session.execute(select(func.count(StockPorDeposito.id_articulo)))
    stock_count = res_stock.scalar()
    assert stock_count == 100

@pytest.mark.asyncio
async def test_seed_fiscal_mix_distribution(async_session, async_db_engine):
    db_url = str(async_db_engine.url)
    await run_seed(count=100, seed_val=123, database_url=db_url)

    # Find Medicamentos family ID
    res_fam = await async_session.execute(select(Familia.id_familia).where(Familia.des_familia == "Medicamentos"))
    med_fam_id = res_fam.scalar()

    res_med = await async_session.execute(select(func.count(Articulo.id_articulo)).where(Articulo.id_familia == med_fam_id))
    med_count = res_med.scalar()
    assert med_count == 50  # Exactly 50% Medicamentos

@pytest.mark.asyncio
async def test_seed_ghost_items_anomaly(async_session, async_db_engine):
    db_url = str(async_db_engine.url)
    await run_seed(count=100, seed_val=123, ghost_rate=0.10, database_url=db_url)

    # Ghost items: stock_teorico > 0 and stock_real == 0
    res_ghost = await async_session.execute(
        select(func.count(StockPorDeposito.id_articulo)).where(
            StockPorDeposito.stock_teorico > 0,
            StockPorDeposito.stock_real == 0
        )
    )
    ghost_count = res_ghost.scalar()
    assert ghost_count >= 10

@pytest.mark.asyncio
async def test_seed_expired_lots_anomaly(async_session, async_db_engine):
    db_url = str(async_db_engine.url)
    await run_seed(count=100, seed_val=123, expired_rate=0.25, database_url=db_url)

    res_expired = await async_session.execute(
        select(func.count(LotePorDeposito.lote)).where(LotePorDeposito.vencimiento < date.today())
    )
    expired_count = res_expired.scalar()
    assert expired_count > 0

@pytest.mark.asyncio
async def test_seed_auditoria_registro_movements(async_session, async_db_engine):
    db_url = str(async_db_engine.url)
    await run_seed(count=100, seed_val=123, database_url=db_url)

    res_audit = await async_session.execute(select(func.count(AuditoriaRegistro.id_auditoria)))
    audit_count = res_audit.scalar()
    assert audit_count > 0

@pytest.mark.asyncio
async def test_seed_multi_tenant_isolation(async_session, async_db_engine):
    db_url = str(async_db_engine.url)
    await run_seed(count=100, seed_val=123, database_url=db_url)

    res_t1 = await async_session.execute(
        select(func.count(Articulo.id_articulo)).where(Articulo.tenant_id == "GlobalMedica_01")
    )
    res_t2 = await async_session.execute(
        select(func.count(Articulo.id_articulo)).where(Articulo.tenant_id == "Farmanor_Branch_02")
    )
    t1_count = res_t1.scalar()
    t2_count = res_t2.scalar()

    assert t1_count > 0
    assert t2_count > 0
    assert t1_count + t2_count == 100
