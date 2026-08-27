import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

from backend.app.movements.domain import (
    TipoAccion,
    StockPorDeposito,
    AuditRecord,
)
from backend.app.movements.schemas import (
    AuditEntryRequest,
    AuditBatchInput,
)
from backend.app.movements.services import AuditService, StockLookupService
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException

@pytest.fixture
def mock_stock_repo():
    return AsyncMock()

@pytest.fixture
def mock_audit_repo():
    repo = AsyncMock()
    return repo

@pytest.fixture
def mock_work_session_service():
    svc = AsyncMock()
    svc.get_active_session_id.return_value = 1
    return svc

@pytest.fixture
def mock_lookup_service(mock_stock_repo, mock_audit_repo):
    return StockLookupService(stock_repository=mock_stock_repo, audit_repository=mock_audit_repo)

@pytest.fixture
def audit_service(mock_stock_repo, mock_audit_repo, mock_lookup_service, mock_work_session_service):
    return AuditService(
        stock_repository=mock_stock_repo,
        audit_repository=mock_audit_repo,
        stock_lookup_service=mock_lookup_service,
        work_session_service=mock_work_session_service,
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
    assert amount == Decimal("605.0000")

@pytest.mark.asyncio
async def test_register_single_audit_happy_path(audit_service, mock_stock_repo, mock_audit_repo):
    mock_audit_repo.exists_by_client_uuid.return_value = False
    mock_audit_repo.get_latest_audit_record.return_value = None
    mock_stock_repo.get_stock_position.return_value = StockPorDeposito(
        id_empresa=1,
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_real=100,
    )
    mock_stock_repo.get_article_cost_info.return_value = (Decimal("50.0000"), "Medicamentos")
    mock_audit_repo.create_audit_record.return_value = AuditRecord(
        audit_id=99,
        session_id=1,
        tenant_id="1",
        branch_id=1,
        warehouse_id=1,
        article_code="ART-001",
        action_type=TipoAccion.BAJA,
        affected_amount=10,
        audit_quantity=90,
        applied_unit_cost=Decimal("50.0000"),
        applied_vat_rate=Decimal("0.00"),
        valorized_amount=Decimal("500.0000"),
        user_id=5,
        scan_timestamp=datetime.utcnow(),
        client_uuid="uuid-abc-123",
        observation="Recuento diario",
    )

    entry = AuditEntryRequest(
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_fisico_contado=90,
        observation="Recuento diario",
    )

    res = await audit_service.register_single_audit(
        tenant_id="1", id_usuario=5, entry=entry
    )

    assert res.id_articulo == "ART-001"
    assert res.stock_real == 100
    assert res.stock_fisico_contado == 90
    assert res.delta_stock == -10
    assert res.tipo_accion == TipoAccion.BAJA
    assert res.cantidad_afectada == 10
    assert res.audit_quantity == 90
    assert res.monto_valorizado == Decimal("500.0000")
    assert res.audit_id == 99

@pytest.mark.asyncio
async def test_register_single_audit_variance_decrease(audit_service, mock_stock_repo, mock_audit_repo):
    mock_audit_repo.exists_by_client_uuid.return_value = False
    mock_audit_repo.get_latest_audit_record.return_value = None
    mock_stock_repo.get_stock_position.return_value = StockPorDeposito(
        id_empresa=1,
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_real=100,
    )
    mock_stock_repo.get_article_cost_info.return_value = (Decimal("50.0000"), "Medicamentos")
    mock_audit_repo.create_audit_record.return_value = AuditRecord(
        audit_id=101,
        session_id=1,
        tenant_id="1",
        branch_id=1,
        warehouse_id=1,
        article_code="ART-001",
        action_type=TipoAccion.BAJA,
        affected_amount=5,
        audit_quantity=95,
        applied_unit_cost=Decimal("50.0000"),
        applied_vat_rate=Decimal("0.00"),
        valorized_amount=Decimal("250.0000"),
        user_id=5,
        scan_timestamp=datetime.utcnow(),
    )

    # Variance: 5 items removed (decrease / BAJA)
    entry = AuditEntryRequest(
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        cantidad_afectada=5,
        tipo_accion=TipoAccion.BAJA,
    )

    res = await audit_service.register_single_audit(
        tenant_id="1", id_usuario=5, entry=entry
    )

    assert res.id_articulo == "ART-001"
    assert res.stock_real == 100
    assert res.delta_stock == -5
    assert res.tipo_accion == TipoAccion.BAJA
    assert res.cantidad_afectada == 5
    assert res.audit_quantity == 95

@pytest.mark.asyncio
async def test_register_single_audit_article_not_found(audit_service, mock_stock_repo, mock_audit_repo):
    mock_audit_repo.exists_by_client_uuid.return_value = False
    mock_audit_repo.get_latest_audit_record.return_value = None
    mock_stock_repo.get_stock_position.return_value = None

    entry = AuditEntryRequest(
        id_sucursal=1,
        id_deposito=1,
        id_articulo="NON-EXISTENT",
        stock_fisico_contado=10,
    )

    with pytest.raises(EntityNotFoundException):
        await audit_service.register_single_audit(
            tenant_id="1", id_usuario=5, entry=entry
        )

@pytest.mark.asyncio
async def test_register_batch_audit(audit_service, mock_stock_repo, mock_audit_repo):
    mock_audit_repo.get_latest_audit_record.return_value = None
    mock_stock_repo.get_stock_position.return_value = StockPorDeposito(
        id_empresa=1,
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-002",
        stock_real=50,
    )
    mock_stock_repo.get_article_cost_info.return_value = (Decimal("100.0000"), "Perfumeria")
    mock_audit_repo.create_audit_record.return_value = AuditRecord(
        audit_id=100,
        session_id=1,
        tenant_id="1",
        branch_id=1,
        warehouse_id=1,
        article_code="ART-002",
        action_type=TipoAccion.ALTA,
        affected_amount=5,
        audit_quantity=55,
        applied_unit_cost=Decimal("100.0000"),
        applied_vat_rate=Decimal("0.21"),
        valorized_amount=Decimal("605.0000"),
        user_id=5,
        scan_timestamp=datetime.utcnow(),
        client_uuid="uuid-2",
    )

    batch = AuditBatchInput(
        items=[
            AuditEntryRequest(
                id_sucursal=1,
                id_deposito=1,
                id_articulo="ART-002",
                stock_fisico_contado=55,
            ),
        ]
    )

    res = await audit_service.register_batch_audit(
        tenant_id="1", id_usuario=5, batch=batch
    )

    assert res.total_processed == 1
    assert res.duplicates_skipped == 0
    assert len(res.results) == 1
    assert res.results[0].id_articulo == "ART-002"

