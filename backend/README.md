# SaaS Stock Deposit Control - Backend

The backend service implements the core application logic for inventory audits, stock reconciliation, warehouse and branch operations, user administration, authentication, and financial analytics reporting. It is built with **FastAPI**, **Pydantic V2**, and **SQLAlchemy 2.0 Async** following a strict **Hexagonal Architecture (Ports & Adapters)** across a three-database topology.

---

## Prerequisites

- **Python 3.12+**
- **MariaDB / MySQL** server (production/local dev) or **SQLite (`aiosqlite`)** (automated test suite)
- Configured environment variables for the three database contexts (`db_articles`, `db_users`, `db_analytics`)

---

## Local Setup

1. **Create and activate the virtual environment**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install runtime and development dependencies**:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

3. **Configure environment variables** in `.env` (at the repository root):
   ```env
   ENVIRONMENT=production
   SECRET_KEY=<generate-32+-char-secret-via-python-secrets.token_urlsafe(48)>
   ACCESS_TOKEN_EXPIRE_MINUTES=480
   CORS_ORIGINS=http://localhost:3000,http://localhost:8080

   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=app_user
   DB_PASSWORD=your_password
   DB_SSL_MODE=disable

   DB_NAME_ARTICLES=db_articles
   DB_NAME_USERS=db_users
   DB_NAME_ANALYTICS=db_analytics
   ```
   *(Note: Specific URLs `ARTICLES_DATABASE_URL`, `USERS_DATABASE_URL`, `ANALYTICS_DATABASE_URL` or `DATABASE_URL` take precedence over `DB_*` when set. In `ENVIRONMENT=production`, startup fails fast if `SECRET_KEY` is shorter than 32 characters or set to a weak value like `changeme` or `secret`.)*

4. **Run database migrations** (from the repository root):
   ```bash
   alembic -c backend/migrations/alembic.ini upgrade head
   alembic -c backend/migrations/alembic_users.ini upgrade head
   alembic -c backend/migrations/alembic_analytics.ini upgrade head
   ```

5. **Seed demo data** (optional, see [Database Seeding](#database-seeding) below):
   ```bash
   python -m backend.scripts.seed
   ```

6. **Start the API server**:
   ```bash
   uvicorn backend.api.main:app --reload
   ```
   *(Or `uvicorn api.main:app --reload` when running from inside `backend/`.)*

The API is available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### API Documentation & OpenAPI Specification
- **Full API Documentation**: [`../docs/API_DOCUMENTATION.md`](../docs/API_DOCUMENTATION.md)
- **OpenAPI 3.1.0 JSON Specification**: [`../docs/openapi.json`](../docs/openapi.json)
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **Interactive ReDoc**: `http://localhost:8000/redoc`

---

## Architecture Overview

The backend enforces strict Hexagonal Architecture boundaries:

```text
backend/
├── api/          # Primary (Driving) Adapters: FastAPI routers, middlewares, DI wiring, exception handlers
├── app/          # Domain & Application Layer: pure business logic, Pydantic V2 schemas, port interfaces
├── adapters/     # Secondary (Driven) Adapters: SQLAlchemy 2.0 async repositories, ORM models, JWT/Bcrypt
├── migrations/   # Multi-database Alembic environment and version directories
├── scripts/      # Parametric multi-database seeding and operational utilities
└── tests/        # Unit, domain, adapter, database, report, and API integration tests
```

- [`backend/api/README.md`](./api/README.md) — Primary HTTP adapters and dependency injection
- [`backend/app/README.md`](./app/README.md) — Pure domain models, ports, orchestrators, and services
- [`backend/adapters/README.md`](./adapters/README.md) — Database connection factories, repositories, and security adapters

---

## Multi-Database Topology & Alembic Migrations

### Database Contexts

The platform partitions persistence across three isolated relational schemas:

| Database | Declarative Base | ORM Module | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| **`db_articles`** | `BaseArticles` | `adapters/repositories/models/articles.py` | Master catalog (`articulos`, `familias`, `grupos`, `marcas`, `codigos_barra_articulo`), legacy organizational entities (`empresas`, `sucursales`, `depositos`), and baseline stock (`stock_por_deposito`, `lotes_por_deposito`). Treated as **read-only** by audit operations. |
| **`db_users`** | `BaseUsers` | `adapters/repositories/models/users.py` | Multi-tenant SaaS hierarchy (`enterprises`, `branches`), user accounts (`users`), RBAC roles (`roles`), and role assignments (`user_roles`). |
| **`db_analytics`** | `BaseAnalytics` | `adapters/repositories/models/analytics.py` | Operational audit ledger (`record_tenants`, `work_sessions`, `audit_records`), consolidated daily balance snapshots (`daily_reports`), and FEFO expiration alerts (`critical_shrinkage_alerts`). |

### Multi-Database Alembic Configuration (`backend/migrations/env.py`)

Migrations are managed by a unified async migration environment (`backend/migrations/env.py`) paired with three dedicated Alembic configuration files:

| Config File | Target Database | `DB_TARGET` Value | Metadata Base | Revisions Directory |
| :--- | :--- | :--- | :--- | :--- |
| `backend/migrations/alembic.ini` | `db_articles` | `articles` | `BaseArticles.metadata` | `backend/migrations/versions/` |
| `backend/migrations/alembic_users.ini` | `db_users` | `users` | `BaseUsers.metadata` | `backend/migrations/versions_users/` |
| `backend/migrations/alembic_analytics.ini` | `db_analytics` | `analytics` | `BaseAnalytics.metadata` | `backend/migrations/versions_analytics/` |

#### How `DB_TARGET` Resolution Works
`backend/migrations/env.py` determines which schema to migrate using the following precedence:
1. **`DB_TARGET` environment variable**: Explicitly set `DB_TARGET=articles`, `DB_TARGET=users`, or `DB_TARGET=analytics`.
2. **Config filename inference**: If `DB_TARGET` is unset, `env.py` inspects `context.config.config_file_name` (`"analytics"` -> `analytics`, `"users"` -> `users`, otherwise -> `articles`).
3. **Dynamic binding**: Based on the resolved target, `env.py` selects the corresponding `target_metadata`, resolves the database name (`DB_NAME_ARTICLES`, `DB_NAME_USERS`, or `DB_NAME_ANALYTICS`), and dynamically sets `version_locations` to `versions/`, `versions_users/`, or `versions_analytics/`.

#### Common Migration Commands
```bash
# Apply all pending migrations per database using the dedicated .ini files
alembic -c backend/migrations/alembic.ini upgrade head
alembic -c backend/migrations/alembic_users.ini upgrade head
alembic -c backend/migrations/alembic_analytics.ini upgrade head

# Or using DB_TARGET explicitly
DB_TARGET=articles alembic -c backend/migrations/alembic.ini upgrade head
DB_TARGET=users alembic -c backend/migrations/alembic.ini upgrade head
DB_TARGET=analytics alembic -c backend/migrations/alembic.ini upgrade head

# Autogenerate a new revision for a specific target
alembic -c backend/migrations/alembic_analytics.ini revision --autogenerate -m "description"
```

---

## Database Seeding (`backend/scripts/seed.py`)

The parametric seeding script (`backend/scripts/seed.py`) populates deterministic, realistic Argentine pharmacy and warehouse data (`Faker('es_AR')`) across all three databases idempotently.

### Running the Seeder

From the project root:
```bash
python -m backend.scripts.seed
```

With custom CLI flags:
```bash
python -m backend.scripts.seed \
  --count 500 \
  --seed 42 \
  --deposits 1 \
  --ghost-rate 0.10 \
  --expired-rate 0.25 \
  --vat-rate 0.21 \
  --shrinkage-rate 0.30 \
  --goods-received-rate 0.15
```

### What the Seeder Populates

1. **`db_articles` (Catalog & Stock)**:
   - `Empresa` (`id_empresa=1`, `"Empresa Principal"`), `Sucursal` (`id_sucursal=1`, `"Sucursal Central"`), and `Deposito`s (`1..N`).
   - **4 Product Families (`Familia`)**: `"01"` (*Medicamentos* — 0% VAT exempt), `"02"` (*Perfumería*), `"03"` (*Cosmética*), and `"04"` (*Accesorios*) — 21% taxable.
   - **12 Product Groups (`Grupo`)** (3 per family) and **15 Brands/Laboratories (`Marca`)**.
   - **Articles (`Articulo`)**: 500 SKUs by default (50% tax-exempt `MED` medications, 50% taxable `ART` items) with `Decimal` purchase costs (`pcio_com_siva`).
   - **Stock, Barcodes & Batches**: `StockPorDeposito` rows (including 10% "ghost items" with `stock_real=0`), `CodigoBarraArticulo` EAN-13 barcodes (`779...`), and 1–3 `LotePorDeposito` FEFO batches per SKU distributed across expired, expiring (<30d, 31–60d), and healthy (>60d) dates.

2. **`db_users` (Tenants, Roles & Demo Users)**:
   - `Enterprise` (`tenant_id=1`, `"Empresa Principal"`) and `Branch` (`id_branch=1`, `"Sucursal Central"`).
   - **3 RBAC Roles (`Role`)**: `administrador`, `supervisor`, and `auditor`.
   - **3 Demo Users (`User`)** for Tenant 1 (all with password **`123456`**):
     | Email | Role | Active Status | Purpose |
     | :--- | :--- | :--- | :--- |
     | `admin@globalmedica.com` | `administrador` | Active (`True`) | Full access, cost visibility (`pcio_com_siva`), reports, user management |
     | `supervisor@globalmedica.com` | `supervisor` | Active (`True`) | Branch supervision and audit operations (masked financial costs) |
     | `auditor@globalmedica.com` | `auditor` | Active (`True`) | Field barcode scanning and stock counting (masked financial costs) |

3. **`db_analytics` (Sessions, Audits, Reports & Alerts)**:
   - `RecordTenant` (`tenant_id=1`, `"GlobalMedica Inc."`, `pharmacy_code="FARMA-001"`).
   - Active 24-hour `WorkSession` (`status="OPEN"`) for Tenant 1 / Branch 1.
   - `AuditRecord` entries for shrinkage (`REMOVAL`) and goods received (`ADDITION` / `Alta` / `Ingreso`) with computed VAT and valorized amounts.
   - Consolidated `DailyReport` rows across branches and recent days.
   - `CriticalShrinkageAlert` records (`RED` / `YELLOW` / `GREEN` risk levels) generated from expired and near-expiry lots.

---

## Business Modules & API Endpoints

### Domain Modules (`backend/app/`)

- `app/articles/`: Catalog search, pagination, barcode lookup (`ArticleSearchService`), and cross-context stock enrichment (`ArticleCatalogOrchestrator`).
- `app/movements/`: Physical count vs. variance delta math (`DeltaCalculator`), family VAT classification (`VatClassifier`), audit registration and offline batch sync (`AuditService`), effective stock resolution (`StockLookupService`), and real-time session KPI aggregation (`StockKPIService`, `KPICalculator`).
- `app/reports/`: Financial erosion from shrinkage (`ShrinkageReportService`), injected capital from goods received (`GoodsReceivedReportService`), and consolidated daily inventory balance ledger (`DailyInventoryBalanceReportService`).
- `app/users/`: JWT authentication (`AuthService`) and tenant user administration with self-deactivation and self-demotion safety guards (`UserService`).
- `app/work_sessions/`: Daily branch audit session lifecycle (`WorkSessionService`).
- `app/enterprises/`: Multi-tenant enterprise CRUD (`EnterpriseService`).
- `app/branches/`: Tenant branch CRUD (`BranchService`).
- `app/ports/`: Cross-cutting infrastructure interfaces (`ConnectionProvider`, `DatabaseSession`, `TokenProvider`, `PasswordHasher`).

### REST API Endpoints (`backend/api/v1/`)

| Router | Method & Path | Service / Use Case | Role Access |
| :--- | :--- | :--- | :--- |
| **Health** | `GET /health`<br>`GET /api/v1/health` | `ConnectionProvider.check_databases` (probes `articles`, `users`, `analytics`) | Public |
| **Auth** | `POST /api/v1/auth/login` | `AuthService.authenticate` | Public |
| **Articles** | `GET /api/v1/articles`<br>`GET /api/v1/articles/search`<br>`GET /api/v1/articles/{id_articulo}` | `ArticleCatalogOrchestrator`<br>`ArticleSearchService` | Authenticated (Admin sees `pcio_com_siva`; Supervisor/Auditor receive `ArticuloPublicOut`) |
| **Stock & Audit** | `POST /api/v1/stock/audit`<br>`POST /api/v1/stock/audit/batch`<br>`GET /api/v1/stock/position`<br>`GET /api/v1/stock/kpis` | `AuditService.register_single_audit`<br>`AuditService.register_batch_audit`<br>`StockLookupService.get_effective_stock`<br>`StockKPIService.get_dashboard_kpis` | `administrador`, `supervisor`, `auditor` (Financial KPIs & `pcio_com_siva` restricted to `administrador`) |
| **Users** | `GET /api/v1/users`<br>`PATCH /api/v1/users/{user_id}/status`<br>`PUT /api/v1/users/{user_id}/roles` | `UserService.list_users`<br>`UserService.update_status`<br>`UserService.assign_roles` | `administrador` only |
| **Reports** | `GET /api/v1/reports/shrinkage`<br>`GET /api/v1/reports/goods-received`<br>`GET /api/v1/reports/inventory-balance` | `ShrinkageReportService`<br>`GoodsReceivedReportService`<br>`DailyInventoryBalanceReportService` | `administrador` only |
| **Enterprises** | `GET /api/v1/enterprises`<br>`GET /api/v1/enterprises/{tenant_id}`<br>`POST /api/v1/enterprises`<br>`PUT /api/v1/enterprises/{tenant_id}`<br>`DELETE /api/v1/enterprises/{tenant_id}` | `EnterpriseService` | Authenticated |
| **Branches** | `GET /api/v1/branches/{branch_id}`<br>`GET /api/v1/branches/tenant/{tenant_id}`<br>`POST /api/v1/branches`<br>`PUT /api/v1/branches/{branch_id}`<br>`DELETE /api/v1/branches/{branch_id}` | `BranchService` | Authenticated |

---

## Testing, Linting & Security Audit (`backend/tests/`)

The test suite is organized by architectural layer and concern (`pytest.ini` configures `pythonpath = . ..` and `testpaths = tests`, so run pytest from inside `backend/`):

```text
backend/tests/
├── adapters/   # Repository integration tests (article, stock, audit, user, report, work_session)
├── api/        # FastAPI endpoint, RBAC, CORS, financial privacy, and middleware tests
├── db/         # Multi-database schema, URL precedence, ORM constraints, and seed script verification tests
├── domain/     # Pure domain unit tests (DeltaCalculator, VatClassifier, AuditService, StockKPIService, UserService, orchestrator)
├── reports/    # Shrinkage, goods received, and daily inventory balance calculation tests
└── unit/       # Security adapters (JWT, Bcrypt), health probes, entrypoint flags, deploy.sh, and verify-local-package.sh tests
```

### Running Tests, Coverage & Linting (`cd backend`)

```bash
cd backend
source .venv/bin/activate

# Run the full backend test suite
pytest

# Run with coverage report
pytest --cov=backend --cov-report=term-missing tests/

# Run focused test suites
pytest tests/domain
pytest tests/api
pytest tests/unit/test_docker_entrypoint.py tests/unit/test_deploy_script.py tests/unit/test_verify_local_package.py

# Lint and format check with Ruff (configured in pyproject.toml)
ruff check . && ruff format --check .

# Audit production dependencies for known vulnerabilities
pip-audit -r requirements.txt
```

---

## Development Rules & Invariants

- **Pure Domain Isolation**: Keep `backend/app/` completely free of SQLAlchemy, FastAPI, Starlette, and infrastructure imports.
- **Port-Driven Dependency Injection**: Inject abstract repository and security ports into domain services via `backend/api/dependencies/services.py`.
- **Financial Precision**: Always represent monetary values and tax rates as `Decimal` (`Numeric(15, 4)` / `Numeric(5, 4)`), never `float`.
- **Structural Financial Privacy**: Never expose `pcio_com_siva` or valorized dashboard KPIs (`monto_valorizado_baja`, `monto_valorizado_alta`) to non-administrator roles (`supervisor`, `auditor`). Use separate Pydantic output schemas (`ArticuloPublicOut` vs. `ArticuloAdminOut`, `DashboardKPIsPublicOut` vs. `DashboardKPIsResponse`).
- **Tenant & Session Isolation**: Derive `tenant_id`, `branch_id`, and `user_id` from verified JWT claims rather than client request payloads.
