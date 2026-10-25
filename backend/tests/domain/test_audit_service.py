from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from backend.app.articles.models import Articulo
from backend.app.exceptions import (
    BusinessRuleViolationException,
    EntityNotFoundException,
    NoActiveWorkSessionError,
)
from backend.app.movements.domain import (
    AuditRecord,
    DeltaCalculator,
    StockPorDeposito,
    TipoAccion,
    VatClassifier,
)
from backend.app.movements.schemas import (
    AuditBatchInput,
    AuditEntryRequest,
)
from backend.app.movements.services import AuditService, StockLookupService


@pytest.fixture
def mock_stock_repo():
    return AsyncMock()


@pytest.fixture
def mock_article_repo():
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
    return StockLookupService(
        stock_repository=mock_stock_repo, audit_repository=mock_audit_repo
    )


@pytest.fixture
def audit_service(
    mock_article_repo, mock_audit_repo, mock_lookup_service, mock_work_session_service
):
    return AuditService(
        article_repository=mock_article_repo,
        audit_repository=mock_audit_repo,
        stock_lookup_service=mock_lookup_service,
        work_session_service=mock_work_session_service,
        default_vat_rate=Decimal("0.21"),
    )


def test_delta_calculator_from_physical_count():
    res_add = DeltaCalculator.from_physical_count(
        stock_real_previo=100, stock_fisico_contado=120
    )
    assert res_add.delta_stock == 20
    assert res_add.tipo_accion == TipoAccion.ALTA
    assert res_add.cantidad_afectada == 20
    assert res_add.audit_quantity == 120

    res_def = DeltaCalculator.from_physical_count(
        stock_real_previo=100, stock_fisico_contado=85
    )
    assert res_def.delta_stock == -15
    assert res_def.tipo_accion == TipoAccion.BAJA
    assert res_def.cantidad_afectada == 15
    assert res_def.audit_quantity == 85

    res_eq = DeltaCalculator.from_physical_count(
        stock_real_previo=100, stock_fisico_contado=100
    )
    assert res_eq.delta_stock == 0
    assert res_eq.tipo_accion == TipoAccion.SIN_ACCION
    assert res_eq.cantidad_afectada == 0
    assert res_eq.audit_quantity == 100


def test_delta_calculator_from_variance():
    res_baja = DeltaCalculator.from_variance(
        stock_real_previo=100, cantidad_afectada=10, tipo_accion=TipoAccion.BAJA
    )
    assert res_baja.delta_stock == -10
    assert res_baja.tipo_accion == TipoAccion.BAJA
    assert res_baja.cantidad_afectada == 10
    assert res_baja.audit_quantity == 90

    res_alta = DeltaCalculator.from_variance(
        stock_real_previo=100, cantidad_afectada=15, tipo_accion=TipoAccion.ALTA
    )
    assert res_alta.delta_stock == 15
    assert res_alta.tipo_accion == TipoAccion.ALTA
    assert res_alta.cantidad_afectada == 15
    assert res_alta.audit_quantity == 115

    res_none = DeltaCalculator.from_variance(
        stock_real_previo=100, cantidad_afectada=0, tipo_accion=TipoAccion.SIN_ACCION
    )
    assert res_none.delta_stock == 0
    assert res_none.tipo_accion == TipoAccion.SIN_ACCION
    assert res_none.cantidad_afectada == 0
    assert res_none.audit_quantity == 100


def test_compute_delta_delegation():
    delta, action = AuditService.compute_delta(
        stock_real_previo=100, stock_fisico_contado=120
    )
    assert delta == 20
    assert action == TipoAccion.ALTA


def test_vat_classifier():
    assert VatClassifier.classify("Medicamentos") == Decimal("0.00")
    assert VatClassifier.classify(" MEDICAMENTOS ") == Decimal("0.00")
    assert VatClassifier.classify("Perfumeria") == Decimal("0.21")
    assert VatClassifier.classify(
        "Higiene", default_vat_rate=Decimal("0.105")
    ) == Decimal("0.105")
    assert VatClassifier.classify(None) == Decimal("0.21")


def test_valorized_amount_medicamentos_0_vat():
    cost = Decimal("150.5000")
    amount = AuditService.compute_valorized_amount(
        pcio_com_siva=cost,
        des_familia="Medicamentos",
        cantidad=10,
    )
    assert amount == Decimal("1505.0000")


def test_valorized_amount_other_21_vat():
    cost = Decimal("100.0000")
    amount = AuditService.compute_valorized_amount(
        pcio_com_siva=cost,
        des_familia="Perfumeria",
        cantidad=5,
        default_vat_rate=Decimal("0.21"),
    )
    assert amount == Decimal("605.0000")


@pytest.mark.asyncio
async def test_register_single_audit_happy_path(
    audit_service, mock_stock_repo, mock_article_repo, mock_audit_repo
):
    mock_audit_repo.exists_by_client_uuid.return_value = False
    mock_audit_repo.get_latest_audit_record.return_value = None
    mock_stock_repo.get_stock_position.return_value = StockPorDeposito(
        id_empresa=1,
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_real=100,
    )
    mock_article_repo.get_by_id.return_value = Articulo(
        id_articulo="ART-001",
        des_articulo="Medicamento 1",
        des_familia="Medicamentos",
        pcio_com_siva=Decimal("50.0000"),
    )
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
async def test_register_single_audit_variance_decrease(
    audit_service, mock_stock_repo, mock_article_repo, mock_audit_repo
):
    mock_audit_repo.exists_by_client_uuid.return_value = False
    mock_audit_repo.get_latest_audit_record.return_value = None
    mock_stock_repo.get_stock_position.return_value = StockPorDeposito(
        id_empresa=1,
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_real=100,
    )
    mock_article_repo.get_by_id.return_value = Articulo(
        id_articulo="ART-001",
        des_articulo="Medicamento 1",
        des_familia="Medicamentos",
        pcio_com_siva=Decimal("50.0000"),
    )
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
async def test_register_single_audit_no_active_session_raises(
    audit_service,
    mock_stock_repo,
    mock_article_repo,
    mock_audit_repo,
    mock_work_session_service,
):
    mock_work_session_service.get_active_session_id.return_value = None
    mock_audit_repo.get_latest_audit_record.return_value = None
    mock_stock_repo.get_stock_position.return_value = StockPorDeposito(
        id_empresa=1,
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_real=100,
    )
    mock_article_repo.get_by_id.return_value = Articulo(
        id_articulo="ART-001",
        des_articulo="Medicamento 1",
        des_familia="Medicamentos",
        pcio_com_siva=Decimal("50.0000"),
    )

    entry = AuditEntryRequest(
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_fisico_contado=90,
    )

    with pytest.raises(NoActiveWorkSessionError) as exc_info:
        await audit_service.register_single_audit(
            tenant_id="1", id_usuario=5, entry=entry
        )

    assert "No active work session found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_register_single_audit_invalid_tenant_raises(audit_service):
    entry = AuditEntryRequest(
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_fisico_contado=90,
    )

    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await audit_service.register_single_audit(
            tenant_id="invalid-tenant-string", id_usuario=5, entry=entry
        )

    assert "Invalid tenant_id" in str(exc_info.value)


@pytest.mark.asyncio
async def test_register_single_audit_missing_branch_or_deposit_raises(audit_service):
    entry_no_branch = AuditEntryRequest(
        id_sucursal=None,
        id_deposito=1,
        id_articulo="ART-001",
        stock_fisico_contado=90,
    )

    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await audit_service.register_single_audit(
            tenant_id="1", id_usuario=5, entry=entry_no_branch
        )

    assert "Branch ID (id_sucursal) and Deposit ID (id_deposito) are required" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_register_single_audit_stock_position_not_found(
    audit_service, mock_stock_repo, mock_audit_repo
):
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
async def test_register_single_audit_master_article_not_found(
    audit_service, mock_stock_repo, mock_article_repo, mock_audit_repo
):
    mock_audit_repo.exists_by_client_uuid.return_value = False
    mock_audit_repo.get_latest_audit_record.return_value = None
    mock_stock_repo.get_stock_position.return_value = StockPorDeposito(
        id_empresa=1,
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_real=100,
    )
    mock_article_repo.get_by_id.return_value = None

    entry = AuditEntryRequest(
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-001",
        stock_fisico_contado=10,
    )

    with pytest.raises(EntityNotFoundException) as exc_info:
        await audit_service.register_single_audit(
            tenant_id="1", id_usuario=5, entry=entry
        )
    assert "Article 'ART-001' not found." in str(exc_info.value)


@pytest.mark.asyncio
async def test_register_batch_audit(
    audit_service, mock_stock_repo, mock_article_repo, mock_audit_repo
):
    mock_audit_repo.get_latest_audit_record.return_value = None
    mock_stock_repo.get_stock_position.return_value = StockPorDeposito(
        id_empresa=1,
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART-002",
        stock_real=50,
    )
    mock_article_repo.get_by_id.return_value = Articulo(
        id_articulo="ART-002",
        des_articulo="Perfume 1",
        des_familia="Perfumeria",
        pcio_com_siva=Decimal("100.0000"),
    )
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
