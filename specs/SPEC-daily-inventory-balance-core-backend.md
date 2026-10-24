# Spec: Daily Inventory Balance Report - Core Backend Agent Task & Specification

## Objective

This specification details the domain entities, Pydantic schemas, abstract ports, domain service orchestrator, concrete SQLAlchemy repository implementation, FastAPI primary adapter endpoints, and automated tests that the **Core Backend Agent** (`core-backend-agent` / Jules) must implement to complete the **Balance Diario de Inventario (Daily Inventory Cost Ledger)** functionality.

This feature complements the database schema changes, ORM model extensions (`branch_id`, `total_processed_units`, `net_patrimonial_variation`), and migrations performed by the **DBA Agent** (`dba-agent`), providing a complete, clean, end-to-end reporting service and API.

---

## Tech Stack

- **Framework**: FastAPI (Python 3.11/3.12+)
- **Data Validation & Schemas**: Pydantic V2 (`BaseModel`, `ConfigDict`, `Field`)
- **Financial Math**: `decimal.Decimal` (100% exact precision, floats prohibited)
- **Database Access / ORM**: Async SQLAlchemy 2.0 (encapsulated in repository adapter)
- **Security & Authorization**: JWT Claims decoding, `RoleChecker(allowed_roles=["administrador"])`
- **Testing Framework**: Pytest (`pytest`, `pytest-asyncio`, `httpx.AsyncClient`)

---

## Commands

Execute the following verification commands within the `/backend` directory context:

```bash
# Run unit tests for daily inventory balance domain & services
pytest tests/unit/test_daily_inventory_balance.py -v

# Run integration tests for report endpoints
pytest tests/api/test_reports_api.py -v

# Run hexagonal architecture compliance check
python scripts/check_hexagonal.py
```

---

## Project Structure & Ownership Boundaries

```
backend/
├── app/
│   └── reports/                  → [CORE BACKEND OWNED] Domain (domain.py, ports.py, schemas.py, services.py)
├── adapters/
│   └── repositories/
│       └── report_repository.py  → [CORE BACKEND OWNED] Repository Adapter
├── api/
│   ├── dependencies/             → [CORE BACKEND OWNED] Service Injection Dependencies
│   └── v1/
│       └── reports.py            → [CORE BACKEND OWNED] FastAPI Primary Adapter Router
└── tests/                        → [CORE BACKEND OWNED] Unit & API Integration Tests
```

### Strict Core Backend Boundaries:
- **OWNED PATHS**: `backend/app/*`, `backend/adapters/repositories/*` (except `models/`), `backend/api/*`, `backend/tests/unit/*`, `backend/tests/api/*`.
- **PROHIBITED PATHS**: The Core Backend Agent MUST NEVER modify `backend/migrations/*`, `backend/scripts/*`, or `backend/adapters/repositories/models/*` (owned exclusively by DBA-Agent).

---

## Architectural Design & Components

### 1. Pure Domain Layer (`backend/app/reports/`)

#### A. Domain Value Objects / Entities (`domain.py`)
Ensure domain math uses `VatCalculator` and define pure domain structures:

```python
class DailyInventoryBalanceRecord(BaseModel):
    """
    Pure domain representation of daily consolidated inventory balance data per branch.
    """
    tenant_id: int
    branch_id: int
    report_date: date
    total_audit_articles: int
    total_processed_units: int
    total_addition_amount: int
    total_shrinkage_amount: int
    total_addition_value: Decimal
    total_shrinkage_value: Decimal
    net_patrimonial_variation: Decimal

    model_config = ConfigDict(from_attributes=True)
```

#### B. Pydantic Schemas (`schemas.py`)
Define request filter parameters and output schemas:

- `DailyInventoryBalanceFilters`:
  - `start_date: date` (inclusive, required)
  - `end_date: date` (inclusive, required)
  - `branch_id: Optional[int]` (ge=1, optional)
- `DailyInventoryBalanceSummary`:
  - Summary metrics per day or consolidated range: `report_date`, `total_audit_articles`, `total_processed_units`, `total_addition_units`, `total_shrinkage_units`, `total_addition_value`, `total_shrinkage_value`, `net_patrimonial_variation`.
- `DailyInventoryBalanceResponse`:
  - `tenant_id: str`, `branch_id: Optional[int]`, `start_date: date`, `end_date: date`, `total_days: int`, `total_addition_value: Decimal`, `total_shrinkage_value: Decimal`, `net_patrimonial_variation: Decimal`, `daily_summaries: List[DailyInventoryBalanceSummary]`.

#### C. Abstract Port (`ports.py`)
Define abstract interface `DailyInventoryBalanceReportRepositoryPort`:

```python
class DailyInventoryBalanceReportRepositoryPort(ABC):
    @abstractmethod
    async def fetch_daily_balance_records(
        self,
        tenant_id: int,
        start_date: date,
        end_date: date,
        branch_id: Optional[int] = None,
    ) -> List[DailyInventoryBalanceRecord]:
        """
        Retrieves consolidated daily inventory balance records filtered by tenant, date range, and branch.
        """
        pass
```

#### D. Controller Service (`services.py`)
Implement `DailyInventoryBalanceReportService`:
- Orchestrates repository queries via `DailyInventoryBalanceReportRepositoryPort`.
- Calculates fallback aggregates dynamically from `AuditRecord` if pre-aggregated `DailyReport` records do not exist for a given date range.
- Formulates `DailyInventoryBalanceResponse` ensuring net patrimonial calculation ($\Delta = \text{Altas} - \text{Mermas}$).

---

### 2. Secondary Adapter Layer (`backend/adapters/repositories/`)

#### Extension in `report_repository.py`
Implement `SQLAlchemyDailyInventoryBalanceReportRepository` implementing `DailyInventoryBalanceReportRepositoryPort`:
- Queries `DailyReport` ORM model in `db_analytics`.
- Applies filters: `tenant_id`, `report_date >= start_date`, `report_date <= end_date`, and optional `branch_id == branch_id`.
- Performs dynamic aggregation fallback from `AuditRecordORM` if no pre-calculated `DailyReport` records are present.

---

### 3. Primary Adapter Layer (`backend/api/`)

#### A. Service Dependency Factory (`api/dependencies/services.py`)
Add dependency provider:

```python
def get_daily_inventory_balance_report_service(
    repo: DailyInventoryBalanceReportRepositoryPort = Depends(get_daily_inventory_balance_repository),
) -> DailyInventoryBalanceReportService:
    return DailyInventoryBalanceReportService(report_repository=repo)
```

#### B. API Endpoint Router (`api/v1/reports.py`)
Expose endpoint `GET /api/v1/reports/inventory-balance`:

```python
@router.get(
    "/inventory-balance",
    response_model=DailyInventoryBalanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Daily Inventory Cost Ledger Report",
    description="Retrieves consolidated daily inventory balance (Goods Received vs Shrinkage), "
    "calculates net patrimonial variation (Delta = Altas - Mermas). Exclusive to administrator role.",
)
async def get_daily_inventory_balance_report(
    start_date: date = Query(..., description="Start date for audit records (inclusive)"),
    end_date: date = Query(..., description="End date for audit records (inclusive)"),
    branch_id: Optional[int] = Query(default=None, description="Optional branch ID filter", ge=1),
    claims: dict = Depends(require_admin),
    service: DailyInventoryBalanceReportService = Depends(get_daily_inventory_balance_report_service),
) -> DailyInventoryBalanceResponse:
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date",
        )
    ...
```

---

## Testing Strategy & Quality Checklist

### 1. Unit Tests (`backend/tests/unit/test_daily_inventory_balance.py`)
- Test `DailyInventoryBalanceReportService` with a mock repository port returning test records.
- Verify exact net patrimonial math:
  - $\text{net\_patrimonial\_variation} = 250000.00 - 45000.00 = 205000.00$.
- Verify handling of empty date ranges and invalid date validations (`start_date > end_date`).

### 2. Integration & RBAC Tests (`backend/tests/api/test_reports_api.py`)
- Assert `GET /api/v1/reports/inventory-balance` with non-admin JWT returns `403 FORBIDDEN`.
- Assert request with admin JWT returns `200 OK` and valid `DailyInventoryBalanceResponse`.

---

## Boundaries & Guardrails

- **Always do**:
  - Enforce `RoleChecker(allowed_roles=["administrador"])` on the endpoint.
  - Use `Decimal` for all financial metrics (never native Python `float`).
  - Keep `backend/app/` 100% pure (no ORM or FastAPI imports in domain).
- **Ask first**:
  - Modifying JWT claims structure or changing existing endpoint response models.
- **Never do**:
  - Touch files in `backend/migrations/`, `backend/scripts/`, or `backend/adapters/repositories/models/`.
  - Expose cost/financial fields to non-admin roles.

---

## Success Criteria

- [ ] Abstract port `DailyInventoryBalanceReportRepositoryPort` declared in `backend/app/reports/ports.py`.
- [ ] Domain entity and Pydantic schemas added to `backend/app/reports/domain.py` and `backend/app/reports/schemas.py`.
- [ ] `DailyInventoryBalanceReportService` implemented in `backend/app/reports/services.py`.
- [ ] Repository adapter `SQLAlchemyDailyInventoryBalanceReportRepository` implemented in `backend/adapters/repositories/report_repository.py`.
- [ ] Primary adapter endpoint `GET /api/v1/reports/inventory-balance` added to `backend/api/v1/reports.py` and secured with `require_admin`.
- [ ] Unit tests (`tests/unit/test_daily_inventory_balance.py`) and API tests (`tests/api/test_reports_api.py`) pass with 100% success.
- [ ] `python backend/scripts/check_hexagonal.py` confirms zero hexagonal architecture violations.
