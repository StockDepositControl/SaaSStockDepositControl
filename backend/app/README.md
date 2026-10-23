# 🌌 Domain and Application Layer (`backend/app/`)

This directory contains the core domain and application layer for the SaaS Stock Deposit Control platform. Built following **Hexagonal Architecture (Ports & Adapters)** and **Domain-Driven Design (DDD)** principles, it encapsulates all business rules, domain calculations, value objects, and port interfaces in complete isolation from HTTP, ORM, and database infrastructure concerns.

---

## Golden Rule: Pure Domain Isolation

Modules inside `backend/app/` must **never** import infrastructure or framework libraries such as:

- `fastapi` / `starlette`
- `sqlalchemy` / `alembic`
- Database drivers (`aiomysql`, `aiosqlite`, `pymysql`)
- External HTTP clients or cryptography libraries (`jwt`, `bcrypt`)

The domain layer depends exclusively on the **Python standard library** (`abc`, `datetime`, `decimal`, `enum`, `typing`, `uuid`) and **Pydantic V2** (`BaseModel`, `ConfigDict`, `Field`, `model_validator`).

---

## Directory & Module Structure

While simple CRUD/entity modules follow the baseline `models.py` + `ports.py` + `services.py` layout, complex analytical and operational modules (`articles/`, `movements/`, `reports/`) separate pure domain rules (`domain.py`), input/output DTOs (`schemas.py`), and cross-context orchestration (`orchestrator.py`):

```text
backend/app/
├── __init__.py
├── exceptions.py               # DomainException hierarchy
├── articles/
│   ├── models.py               # Familia, Grupo, Marca, Articulo, ArticuloPublicOut, ArticuloAdminOut
│   ├── ports.py                # ArticleRepositoryPort
│   ├── services.py             # ArticleSearchService
│   └── orchestrator.py         # ArticleCatalogOrchestrator
├── movements/
│   ├── domain.py               # TipoAccion, StockPorDeposito, LotePorDeposito, AuditRecord,
│   │                           # StockLookupResult, SessionAuditAggregates, VatClassifier,
│   │                           # DeltaResult, DeltaCalculator
│   ├── schemas.py              # AuditEntryRequest, AuditEntryResult, AuditBatchInput,
│   │                           # AuditBatchResult, DashboardKPIsPublicOut, DashboardKPIsResponse
│   ├── ports.py                # StockRepositoryPort, AuditRepositoryPort
│   └── services.py             # StockLookupService, AuditService, KPICalculator, StockKPIService
├── reports/
│   ├── domain.py               # VatCalculator, ShrinkageRawRecord, GoodsReceivedRawRecord,
│   │                           # DailyInventoryBalanceRecord
│   ├── schemas.py              # ShrinkageReportFilters/LineItem/Response,
│   │                           # GoodsReceivedReportFilters/LineItem/Response,
│   │                           # DailyInventoryBalanceFilters/Summary/Response
│   ├── ports.py                # ShrinkageReportRepositoryPort, GoodsReceivedReportRepositoryPort,
│   │                           # DailyInventoryBalanceReportRepositoryPort
│   └── services.py             # ShrinkageReportService, GoodsReceivedReportService,
│                               # DailyInventoryBalanceReportService
├── users/
│   ├── models.py               # UserRole, AuthToken, LoginCredentials, User, UserCreate,
│   │                           # UserUpdate, UserStatusUpdate, UserRoleAssignment, UserResponse
│   ├── ports.py                # UserRepositoryPort
│   └── services.py             # AuthService, UserService
├── work_sessions/
│   ├── models.py               # WorkSessionBase, WorkSessionCreate, WorkSession
│   ├── ports.py                # WorkSessionRepositoryPort
│   └── services.py             # WorkSessionService
├── enterprises/
│   ├── models.py               # EnterpriseBase, EnterpriseCreate, EnterpriseUpdate, Enterprise
│   ├── ports.py                # EnterpriseRepositoryPort
│   └── services.py             # EnterpriseService
├── branches/
│   ├── models.py               # BranchBase, BranchCreate, BranchUpdate, Branch
│   ├── ports.py                # BranchRepositoryPort
│   └── services.py             # BranchService
└── ports/
    ├── database.py             # DatabaseSession, ConnectionProvider
    └── security.py             # TokenProvider, PasswordHasher
```

---

## Detailed Breakdown by Module

### 1. Articles & Catalog (`backend/app/articles/`)
- **`models.py`**: Defines catalog entities (`Familia`, `Grupo`, `Marca`, `Articulo`) and structural RBAC output schemas (`ArticuloPublicOut` without cost fields for `supervisor`/`auditor`, and `ArticuloAdminOut` extending `ArticuloPublicOut` with `pcio_com_siva: Decimal` for `administrador`).
- **`ports.py`**: Declares `ArticleRepositoryPort` (`get_by_id`, `get_by_barcode`, `search`, `list_articles`, `get_barcode_by_article_id`).
- **`services.py`**: Implements `ArticleSearchService` for multi-field search (Article ID, EAN-13 barcode, or description tokens), single-item lookup, and bounded pagination (`limit <= 200`).
- **`orchestrator.py`**: Implements `ArticleCatalogOrchestrator`, a Pure Fabrication application service that coordinates `ArticleSearchService` and `StockLookupService` to enrich catalog articles with batch-resolved effective stock levels (`stock_real`) without mutating original domain models.

### 2. Stock Movements, Audits & KPIs (`backend/app/movements/`)
- **`domain.py`**:
  - Domain entities and value objects: `TipoAccion` (`Alta`, `Baja`, `Sin Acción`), `StockPorDeposito`, `LotePorDeposito`, `AuditRecord`, `StockLookupResult`, `SessionAuditAggregates`, and `DeltaResult`.
  - `VatClassifier`: Pure Fabrication service classifying `"Medicamentos"` as tax-exempt (`0.00` VAT) and all other product families at the default VAT rate (`0.21`).
  - `DeltaCalculator`: Pure Fabrication service computing physical count discrepancies (`from_physical_count`: `delta = stock_fisico_contado - stock_real_previo`) and variance adjustments (`from_variance`).
- **`schemas.py`**:
  - Audit DTOs: `AuditEntryRequest` (enforces dual-mode input validation: either `stock_fisico_contado` OR both `cantidad_afectada` and `tipo_accion`), `AuditEntryResult`, `AuditBatchInput`, and `AuditBatchResult`.
  - Dashboard KPI DTOs: `DashboardKPIsPublicOut` (operational counters for non-admin roles) and `DashboardKPIsResponse` (extends `DashboardKPIsPublicOut` with `monto_valorizado_baja` and `monto_valorizado_alta` for administrators).
- **`ports.py`**: Declares `StockRepositoryPort` (`get_stock_position`, `get_stock_positions_batch`, `count_catalog_articles`, `count_out_of_stock_articles`) and `AuditRepositoryPort` (`create_audit_record`, `exists_by_client_uuid`, `get_latest_audit_record`, `get_latest_audits_for_articles`, `get_session_audit_aggregates`).
- **`services.py`**:
  - `StockLookupService`: Resolves effective stock by prioritizing the latest audit record in `db_analytics` with fallback to baseline `stock_por_deposito` in `db_articles` (single and batch resolution).
  - `AuditService`: Orchestrates single and batch offline audit registration, discrepancy calculation, VAT classification, financial valorization, active work session verification, and immutable ledger persistence in `db_analytics`.
  - `KPICalculator` & `StockKPIService`: Read-only CQS service combining catalog totals, out-of-stock counts, and session audit aggregates into role-aware dashboard KPIs.

### 3. Financial & Inventory Reports (`backend/app/reports/`)
- **`domain.py`**: Defines `VatCalculator` (`calculate_total_unit_cost`, `calculate_financial_loss`) and raw ledger records (`ShrinkageRawRecord`, `GoodsReceivedRawRecord`, `DailyInventoryBalanceRecord`).
- **`schemas.py`**: Defines request filter models and response contracts for the three administrative reports:
  - `ShrinkageReportFilters`, `ShrinkageLineItem`, `ShrinkageReportResponse`
  - `GoodsReceivedReportFilters`, `GoodsReceivedLineItem`, `GoodsReceivedReportResponse`
  - `DailyInventoryBalanceFilters`, `DailyInventoryBalanceSummary`, `DailyInventoryBalanceResponse`
- **`ports.py`**: Declares `ShrinkageReportRepositoryPort`, `GoodsReceivedReportRepositoryPort`, and `DailyInventoryBalanceReportRepositoryPort`.
- **`services.py`**:
  - `ShrinkageReportService`: Aggregates `REMOVAL` (`Baja`) audit movements by article, enriches with catalog metadata and VAT classification, and computes total financial erosion (`total_financial_erosion`).
  - `GoodsReceivedReportService`: Aggregates `ADDITION` (`Alta`) audit movements by `(article_code, reason)`, resolves primary barcodes and catalog costs, and computes total injected capital (`total_capital_inyectado`).
  - `DailyInventoryBalanceReportService`: Computes daily consolidated additions vs. shrinkage and net patrimonial variation (`net_patrimonial_variation = total_addition_value - total_shrinkage_value`).

### 4. Users, Authentication & RBAC Administration (`backend/app/users/`)
- **`models.py`**: Defines `UserRole` (`administrador`, `supervisor`, `auditor`), `AuthToken`, `LoginCredentials`, `User`, `UserCreate`, `UserUpdate`, `UserStatusUpdate`, `UserRoleAssignment`, and `UserResponse`.
- **`ports.py`**: Declares `UserRepositoryPort` (`get_by_email`, `get_by_id`, `get_password_hash`, `list_by_tenant`, `update_status`, `update_roles`).
- **`services.py`**:
  - `AuthService`: Authenticates user credentials via `PasswordHasher`, rejects inactive accounts (`is_active == False`), and issues signed JWTs via `TokenProvider` containing `sub`, `role`, `tenant_id`, `branch_id`, `user_id`, and `id_usuario`.
  - `UserService`: Manages tenant user listing (`list_users`), account activation toggling (`update_status`), and role assignment (`assign_roles`). Enforces strict domain safety guards:
    - **Self-deactivation guard**: Administrators cannot deactivate their own account (`target_user_id == actor_user_id and not is_active`).
    - **Single-role & self-demotion guard**: Enforces exactly one role per user and prevents administrators from removing the `administrador` role from their own account.

### 5. Work Sessions, Enterprises & Branches
- **`work_sessions/`**: `WorkSession` models, `WorkSessionRepositoryPort`, and `WorkSessionService` (`get_active_session_id`, `get_or_create_active_session` managing 24-hour branch audit sessions).
- **`enterprises/`**: `Enterprise` models, `EnterpriseRepositoryPort`, and `EnterpriseService` (CRUD operations and duplicate `tenant_id` validation).
- **`branches/`**: `Branch` models, `BranchRepositoryPort`, and `BranchService` (tenant-scoped branch CRUD with parent enterprise existence verification).

### 6. Cross-Cutting Ports & Domain Exceptions
- **`ports/database.py`**: `DatabaseSession` (`commit`, `rollback`, `raw_session`) and `ConnectionProvider` (`session`, `check_connectivity`).
- **`ports/security.py`**: `TokenProvider` (`create_token`, `decode_token`) and `PasswordHasher` (`hash`, `verify`).
- **`exceptions.py`**: Pure domain exception hierarchy translated into HTTP status codes by `backend/api/exception_handlers.py`:
  - `DomainException` (base error -> HTTP 500)
  - `EntityNotFoundException` (missing entity -> HTTP 404)
  - `BusinessRuleViolationException` (domain invariant violation -> HTTP 400)
  - `NoActiveWorkSessionError` / `NoActiveWorkSessionException` (missing open session -> HTTP 409)
