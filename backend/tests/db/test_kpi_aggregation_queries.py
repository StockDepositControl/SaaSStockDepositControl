import pytest
import pytest_asyncio
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from backend.adapters.repositories.audit_repository import SQLAlchemyAuditRepository
from backend.adapters.repositories.stock_repository import SQLAlchemyStockRepository
from backend.adapters.repositories.models import (
    Articulo,
    AuditRecord,
    Marca,
    StockPorDeposito,
    Familia,
    Grupo,
)

NOW = datetime(2026, 1, 1, 10, 0, 0)


def _audit(session_id, article, action, amount, tenant=1, branch=1, warehouse=1):
    return AuditRecord(
        tenant_id=tenant,
        session_id=session_id,
        branch_id=branch,
        warehouse_id=warehouse,
        article_code=article,
        user_id=1,
        action_type=action,
        affected_amount=1,
        audit_quantity=1,
        applied_unit_cost=Decimal("1.0000"),
        applied_vat_rate=Decimal("0.2100"),
        valorized_amount=Decimal(amount),
        scan_timestamp=NOW,
    )


@pytest_asyncio.fixture
async def analytics_factory(db_engines):
    return async_sessionmaker(bind=db_engines["analytics"], expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def articles_factory(db_engines):
    return async_sessionmaker(bind=db_engines["articles"], expire_on_commit=False, class_=AsyncSession)


@pytest.mark.asyncio
async def test_audit_aggregates_scoped_to_session(analytics_factory):
    async with analytics_factory() as s:
        s.add_all([
            _audit(1, "A", "REMOVAL", "100.50"),
            _audit(1, "A", "REMOVAL", "10.00"),
            _audit(1, "B", "ADDITION", "20.00"),
            _audit(1, "C", "NO_ACTION", "0"),
            _audit(1, "D", "REMOVAL", "5.00", warehouse=2),
            _audit(1, "E", "REMOVAL", "7.00", tenant=2),
            _audit(2, "F", "REMOVAL", "999.00"),
        ])
        await s.commit()

    repo = SQLAlchemyAuditRepository(analytics_factory)
    agg = await repo.get_session_audit_aggregates(
        tenant_id=1, branch_id=1, deposit_id=1, session_id=1
    )

    assert agg.audited_count == 3
    assert agg.baja_count == 1
    assert agg.alta_count == 1
    assert agg.sin_accion_count == 1
    assert agg.monto_valorizado_baja == Decimal("110.50")
    assert agg.monto_valorizado_alta == Decimal("20.00")


@pytest.mark.asyncio
async def test_audit_aggregates_empty_session_returns_zeros(analytics_factory):
    repo = SQLAlchemyAuditRepository(analytics_factory)

    agg = await repo.get_session_audit_aggregates(
        tenant_id=1, branch_id=1, deposit_id=1, session_id=999
    )

    assert agg.audited_count == 0
    assert agg.monto_valorizado_baja == Decimal("0")
    assert agg.monto_valorizado_alta == Decimal("0")


@pytest.mark.asyncio
async def test_stock_counts(articles_factory):
    async with articles_factory() as s:
        s.add_all([
            Familia(id_familia="01", des_familia="Medicamentos"),
            Marca(id_marca=1, des_marca="Bayer"),
        ])
        await s.flush()
        s.add(Grupo(id_familia="01", id_grupo="01", des_grupo="Analgesicos"))
        await s.flush()
        for code in ("1", "2", "3"):
            s.add(Articulo(
                id_articulo=code, des_articulo=f"Art {code}", id_marca=1,
                id_familia="01", id_grupo="01", pcio_com_siva=Decimal("1.0000"),
            ))
        await s.flush()
        s.add_all([
            StockPorDeposito(id_empresa=1, id_sucursal=1, id_deposito=1, id_articulo="1", stock_real=0),
            StockPorDeposito(id_empresa=1, id_sucursal=1, id_deposito=1, id_articulo="2", stock_real=5),
            StockPorDeposito(id_empresa=1, id_sucursal=1, id_deposito=2, id_articulo="3", stock_real=0),
        ])
        await s.commit()

    repo = SQLAlchemyStockRepository(articles_factory)

    assert await repo.count_catalog_articles() == 3
    assert await repo.count_out_of_stock_articles(1, 1, 1) == 1
    assert await repo.count_out_of_stock_articles(1, 1, 2) == 1
    assert await repo.count_out_of_stock_articles(2, 1, 1) == 0
