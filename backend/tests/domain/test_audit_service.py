import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

from backend.app.movements.models import (
    TipoAccion,
    StockPorDeposito,
    AuditEntryInput,
    AuditBatchInput,
    AuditoriaRegistro,
)
from backend.app.movements.services import AuditService
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException

@pytest.fixture
def mock_stock_repo():
    return AsyncMock()

@pytest.fixture
def mock_audit_repo():
    return AsyncMock()

@pytest.fixture
def audit_service(mock_stock_repo, mock_audit_repo):
    return AuditService(
        stock_repository=mock_stock_repo,
        audit_repository=mock_audit_repo,
        default_vat_rate=Decimal("0.21"),
    )

def test_compute_delta_addition():
    delta, action = AuditService.compute_delta(stock_real_previo=100, stock_fisico_contado=120)
    assert delta == 20
    assert action == TipoAccion.ALTA

def test_compute_delta_deficit():
    delta, action = AuditService.compute_delta(stock_real_previo=100, stock_fisico_contado=85)
    assert delta == -15
    assert action == TipoAccion.BAJA

def test_compute_delta_no_action():
    delta, action = AuditService.compute_delta(stock_real_previo=100, stock_fisico_contado=100)
    assert delta == 0
    assert action == TipoAccion.SIN_ACCION

def test_valorized_amount_medicamentos_0_vat():
    # Medicamentos family receives 0% VAT
    cost = Decimal("150.5000")
    amount = AuditService.compute_valorized_amount(
        pcio_com_siva=cost,
        des_familia="Medicamentos",
        cantidad=10,
    )
    # 150.50 * 1.00 * 10 = 1505.0000
    assert amount == Decimal("1505.0000")

def test_valorized_amount_other_21_vat():
    # Non-medicamentos family receives 21% VAT
    cost = Decimal("100.0000")
    amount = AuditService.compute_valorized_amount(
        pcio_com_siva=cost,
        des_familia="Perfumeria",
        cantidad=5,
        default_vat_rate=Decimal("0.21"),
    )
    # 100.00 * 1.21 * 5 = 605.0000
    assert amount == Decimal("605.0000")

@pytest.mark.asyncio
async def test_register_single_audit_happy_path(audit_service, mock_stock_repo, mock_audit_repo):
    mock_audit_repo.exists_by_client_uuid.return_value = False
    mock_stock_repo.get_stock_position.return_value = StockPorDeposito(
        tenant_id="tenant_01",
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_real=100,
    )
    mock_stock_repo.get_article_cost_info.return_value = (Decimal("50.0000"), "Medicamentos")
    mock_audit_repo.create_audit_record.return_value = AuditoriaRegistro(
        id_auditoria=99,
        tenant_id="tenant_01",
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        tipo_accion=TipoAccion.BAJA,
        cantidad_afectada=10,
        monto_valorizado=Decimal("500.0000"),
        id_usuario=5,
        fecha_hora=datetime.utcnow(),
        client_uuid="uuid-abc-123",
        observacion="Recuento diario",
        tipo_accion_auditoria="ajuste",
    )

    entry = AuditEntryInput(
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_fisico_contado=90,
        observacion="Recuento diario",
        tipo_accion_auditoria="ajuste",
    )

    res = await audit_service.register_single_audit(
        tenant_id="tenant_01", id_usuario=5, entry=entry
    )

    assert res.id_articulo == "ART-001"
    assert res.stock_real == 100
    assert res.stock_fisico_contado == 90
    assert res.delta_stock == -10
    assert res.tipo_accion == TipoAccion.BAJA
    assert res.cantidad_afectada == 10
    assert res.monto_valorizado == Decimal("500.0000")
    assert res.id_auditoria == 99
    mock_stock_repo.update_stock_real.assert_called_once_with(
        tenant_id="tenant_01", id_sucursal=1, id_deposito=1, id_articulo="ART-001", new_stock_real=90
    )

@pytest.mark.asyncio
async def test_register_single_audit_article_not_found(audit_service, mock_stock_repo, mock_audit_repo):
    mock_audit_repo.exists_by_client_uuid.return_value = False
    mock_stock_repo.get_stock_position.return_value = None

    entry = AuditEntryInput(
        id_sucursal=1,
        id_deposito=1,
        id_articulo="NON-EXISTENT",
        stock_fisico_contado=10,
    )

    with pytest.raises(EntityNotFoundException):
        await audit_service.register_single_audit(
            tenant_id="tenant_01", id_usuario=5, entry=entry
        )

@pytest.mark.asyncio
async def test_register_batch_audit(audit_service, mock_stock_repo, mock_audit_repo):
    mock_stock_repo.get_stock_position.return_value = StockPorDeposito(
        tenant_id="tenant_01",
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-002",
        stock_real=50,
    )
    mock_stock_repo.get_article_cost_info.return_value = (Decimal("100.0000"), "Perfumeria")
    mock_audit_repo.create_audit_record.return_value = AuditoriaRegistro(
        id_auditoria=100,
        tenant_id="tenant_01",
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-002",
        tipo_accion=TipoAccion.ALTA,
        cantidad_afectada=5,
        monto_valorizado=Decimal("605.0000"),
        id_usuario=5,
        fecha_hora=datetime.utcnow(),
        client_uuid="uuid-2",
    )

    batch = AuditBatchInput(
        items=[
            AuditEntryInput(
                id_sucursal=1,
                id_deposito=1,
                id_articulo="ART-002",
                stock_fisico_contado=55,
            ),
        ]
    )

    res = await audit_service.register_batch_audit(
        tenant_id="tenant_01", id_usuario=5, batch=batch
    )

    assert res.total_processed == 1
    assert res.duplicates_skipped == 0
    assert len(res.results) == 1
    assert res.results[0].id_articulo == "ART-002"
