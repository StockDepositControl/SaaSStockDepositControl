import pytest
import uuid
from decimal import Decimal
from datetime import datetime
from backend.app.movements.domain import StockPorDeposito, AuditRecord, TipoAccion, StockLookupResult, AuditRecordCreate
from backend.app.movements.schemas import AuditEntryRequest
from backend.app.movements.services import StockLookupService, AuditService
from backend.app.exceptions import EntityNotFoundException

class MockStockRepo:
    def __init__(self, position=None, cost_info=None):
        self.position = position
        self.cost_info = cost_info
        self.update_called = False

    async def get_stock_position(self, tenant_id, id_sucursal, id_deposito, id_articulo):
        return self.position

    async def get_article_cost_info(self, id_articulo):
        return self.cost_info
        
    async def update_stock_real(self, *args, **kwargs):
        self.update_called = True


class MockAuditRepo:
    def __init__(self, latest_record=None):
        self.latest_record = latest_record
        self.created_records = []

    async def get_latest_audit_record(self, tenant_id, id_sucursal, id_deposito, id_articulo):
        return self.latest_record
        
    async def create_audit_record(self, record: AuditRecordCreate):
        self.created_records.append(record)
        return AuditRecord(
            audit_id=1,
            session_id=record.session_id,
            tenant_id=record.tenant_id,
            branch_id=record.branch_id,
            warehouse_id=record.warehouse_id,
            article_code=record.article_code,
            action_type=record.action_type,
            affected_amount=record.affected_amount,
            audit_quantity=record.audit_quantity,
            applied_unit_cost=record.applied_unit_cost,
            applied_vat_rate=record.applied_vat_rate,
            valorized_amount=record.valorized_amount,
            user_id=record.user_id,
            scan_timestamp=record.scan_timestamp,
            client_uuid=record.client_uuid,
            observation=record.observation,
        )


@pytest.mark.asyncio
async def test_stock_lookup_fallback_to_articles():
    stock_repo = MockStockRepo(position=StockPorDeposito(
        id_empresa=1, id_sucursal=1, id_deposito=1, id_articulo="ART1", stock_real=100
    ))
    audit_repo = MockAuditRepo(latest_record=None)
    
    svc = StockLookupService(stock_repo, audit_repo)
    result = await svc.get_effective_stock(1, 1, 1, "ART1")
    
    assert result.stock_real == 100
    assert result.source == "db_articles"


@pytest.mark.asyncio
async def test_stock_lookup_uses_audit():
    stock_repo = MockStockRepo(position=StockPorDeposito(
        id_empresa=1, id_sucursal=1, id_deposito=1, id_articulo="ART1", stock_real=100
    ))
    audit_repo = MockAuditRepo(latest_record=AuditRecord(
        audit_id=1,
        session_id=1,
        tenant_id="1", branch_id=1, warehouse_id=1, article_code="ART1",
        action_type=TipoAccion.BAJA, affected_amount=5, audit_quantity=95,
        applied_unit_cost=Decimal("10.0"), applied_vat_rate=Decimal("0.0"),
        valorized_amount=Decimal("50"), user_id=1, scan_timestamp=datetime.now()
    ))
    
    svc = StockLookupService(stock_repo, audit_repo)
    result = await svc.get_effective_stock(1, 1, 1, "ART1")
    
    assert result.stock_real == 95
    assert result.source == "db_analytics"


class MockWorkSessionService:
    async def get_active_session_id(self, branch_id):
        return 1

@pytest.mark.asyncio
async def test_register_audit_preserves_db_articles():
    stock_repo = MockStockRepo(
        position=StockPorDeposito(id_empresa=1, id_sucursal=1, id_deposito=1, id_articulo="ART1", stock_real=100),
        cost_info=(Decimal("10.0"), "Medicamentos")
    )
    audit_repo = MockAuditRepo(latest_record=None)
    lookup_svc = StockLookupService(stock_repo, audit_repo)
    ws_svc = MockWorkSessionService()
    audit_svc = AuditService(stock_repo, audit_repo, lookup_svc, ws_svc)
    
    entry = AuditEntryRequest(
        id_sucursal=1,
        id_deposito=1,
        id_articulo="ART1",
        stock_fisico_contado=95,
    )
    
    result = await audit_svc.register_single_audit("1", 1, entry)
    
    # Assert result logic
    assert result.stock_real == 100
    assert result.stock_fisico_contado == 95
    assert result.delta_stock == -5
    assert result.audit_quantity == 95
    
    # Ensure db_articles is not modified
    assert not stock_repo.update_called
    
    # Assert analytics db was written to
    assert len(audit_repo.created_records) == 1
    assert audit_repo.created_records[0].audit_quantity == 95
    assert audit_repo.created_records[0].affected_amount == 5
