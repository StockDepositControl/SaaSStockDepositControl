from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from backend.app.movements.domain import SessionAuditAggregates
from backend.app.movements.ports import AuditRepositoryPort, StockRepositoryPort
from backend.app.movements.schemas import DashboardKPIsPublicOut, DashboardKPIsResponse
from backend.app.movements.services import KPICalculator, StockKPIService


@pytest.mark.parametrize(
    "total,audited,expected",
    [(100, 25, 75), (10, 10, 0), (5, 9, 0), (0, 0, 0)],
)
def test_pendientes(total, audited, expected):
    assert KPICalculator.pendientes(total, audited) == expected


@pytest.mark.parametrize(
    "total,audited,expected",
    [(0, 0, 0), (0, 5, 0), (200, 50, 25), (3, 1, 33), (3, 2, 67)],
)
def test_porcentaje_avance(total, audited, expected):
    assert KPICalculator.porcentaje_avance(total, audited) == expected


@pytest.fixture
def ports():
    stock = AsyncMock(spec=StockRepositoryPort)
    audit = AsyncMock(spec=AuditRepositoryPort)
    stock.count_catalog_articles.return_value = 200
    stock.count_out_of_stock_articles.return_value = 7
    audit.get_session_audit_aggregates.return_value = SessionAuditAggregates(
        audited_count=50,
        alta_count=4,
        baja_count=6,
        sin_accion_count=40,
        monto_valorizado_baja=Decimal("123.45"),
        monto_valorizado_alta=Decimal("10.00"),
    )
    return stock, audit


@pytest.mark.asyncio
async def test_admin_receives_amounts(ports):
    stock, audit = ports
    service = StockKPIService(stock, audit)

    result = await service.get_dashboard_kpis("1", 1, 1, 99, is_admin=True)

    assert isinstance(result, DashboardKPIsResponse)
    assert result.total_articulos == 200
    assert result.auditados == 50
    assert result.pendientes == 150
    assert result.porcentaje_avance == 25
    assert result.out_of_stock_count == 7
    assert result.discrepancias_alta == 4
    assert result.discrepancias_baja == 6
    assert result.sin_accion == 40
    assert result.monto_valorizado_baja == Decimal("123.45")
    assert result.monto_valorizado_alta == Decimal("10.00")


@pytest.mark.asyncio
async def test_non_admin_has_no_financial_fields(ports):
    stock, audit = ports
    service = StockKPIService(stock, audit)

    result = await service.get_dashboard_kpis("1", 1, 1, 99, is_admin=False)

    assert isinstance(result, DashboardKPIsPublicOut)
    assert not isinstance(result, DashboardKPIsResponse)
    dumped = result.model_dump()
    assert "monto_valorizado_baja" not in dumped
    assert "monto_valorizado_alta" not in dumped


@pytest.mark.asyncio
async def test_ports_called_with_scope(ports):
    stock, audit = ports
    service = StockKPIService(stock, audit)

    await service.get_dashboard_kpis("3", 2, 5, 42, is_admin=False)

    stock.count_out_of_stock_articles.assert_awaited_once_with(3, 2, 5)
    audit.get_session_audit_aggregates.assert_awaited_once_with(3, 2, 5, 42)


@pytest.mark.asyncio
async def test_empty_catalog_does_not_divide_by_zero(ports):
    stock, audit = ports
    stock.count_catalog_articles.return_value = 0
    audit.get_session_audit_aggregates.return_value = SessionAuditAggregates()
    service = StockKPIService(stock, audit)

    result = await service.get_dashboard_kpis("1", 1, 1, 1, is_admin=True)

    assert result.porcentaje_avance == 0
    assert result.pendientes == 0
    assert result.monto_valorizado_baja == Decimal("0")
