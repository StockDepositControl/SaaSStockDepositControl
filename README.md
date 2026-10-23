# 🏛️ SaaS Stock Deposit Control - Enterprise Platform

A multi-tenant inventory intelligence platform for warehouse auditing, stock reconciliation, FEFO lot tracking, branch operations, and finance-oriented reporting. The monorepo implements a strict **Hexagonal Architecture (Ports & Adapters)** across its FastAPI backend, Next.js web application, and React Native (Expo) mobile field client, backed by a consolidated 3-database MariaDB topology and an NGINX ingress gateway.

---

## 📖 Executive Summary

The platform connects warehouse operators (`auditor`), branch supervisors (`supervisor`), and organization administrators (`administrador`) through a unified multi-tenant ecosystem that isolates authentication/tenancy, operational catalog/stock, and analytical audit ledgers into distinct logical databases:

- **Field Auditing & Stock Movements**: Single and offline-batch physical stock counts, theoretical delta calculation, FEFO lot evaluation, and automatic voucher classification (`Alta`, `Baja`, `Sin Acción`).
- **Identity, Tenancy & RBAC**: Tenant-scoped authentication, enterprise/branch hierarchy, and administrator user lifecycle management (`db_users`).
- **Operational Catalog & Stock Positions**: Multi-barcode article lookup, stock per deposit, and FEFO lot expiration tracking (`db_articles`).
- **Financial & Shrinkage Analytics**: Active work sessions, immutable audit records, dashboard KPIs, and VAT-aware shrinkage, goods-received, and daily inventory balance reports (`db_analytics`).
- **Role-Based Financial Masking**: Confidential purchase costs (`pcio_com_siva`) and valorized monetary amounts (`monto_valorizado`) are structurally omitted for non-administrator roles at both the API schema layer and client adapters.

---

## 🛠️ Architecture & Technology Stack

### Backend (`backend/`)
- **Runtime & Framework**: Python 3.12+, FastAPI, Pydantic V2
- **Persistence & ORM**: SQLAlchemy 2.0 Async ORM + `aiomysql` driver
- **Migrations**: Alembic (multi-database configuration for `db_articles`, `db_users`, and `db_analytics`)
- **Security**: PyJWT (`HS256` signed claims with `tenant_id`, `branch_id`, `id_usuario`, `role`) and `bcrypt` password hashing
- **Testing**: `pytest` + `pytest-asyncio` + `aiosqlite`

### Web Frontend (`frontend-web/`)
- **Framework**: Next.js 16.2 (App Router), React 19, TypeScript 5
- **Styling**: Tailwind CSS v4 (`@tailwindcss/postcss`), Lucide React icons, glassmorphic dark UI theme
- **Scanner & Hardware**: `html5-qrcode` for camera/USB barcode scanning
- **Architecture**: Hexagonal `DataClientPort` with runtime toggle (`NEXT_PUBLIC_DATA_SOURCE=api|mock`) between `ApiDataClient` and `MockDataContext`
- **Testing**: Vitest + React Testing Library (`jsdom`)

### Mobile Frontend (`frontend-mobile/`)
- **Framework**: Expo SDK 57, React Native 0.86, React 19, TypeScript
- **Styling**: NativeWind v4 + warehouse high-contrast design tokens (48dp minimum touch targets)
- **Persistence**: `@react-native-async-storage/async-storage` with tenant-isolated session keys (`audit_global:session:{tenantId}:{branchId}`)
- **Architecture**: Hexagonal `MobileDataClientPort` (`ApiMobileDataClient` and `MockMobileDataClient` toggled via `EXPO_PUBLIC_USE_MOCK`), field-role access guard (`auditor` and `supervisor` only), recursive financial field sanitizer (`stripFinancialFields`), and pure domain services (`AuditValidator`, `DeltaCalculator`, `FefoEvaluator`)

### Shared Design System (`shared/design-tokens/`)
- Centralized cross-platform semantic color palettes, status badges (`Alta`, `Baja`, `Sin Acción`, FEFO severity), and spacing primitives shared across `frontend-web` and `frontend-mobile`.

### Infrastructure & DevOps (`docker/`, `scripts/devops/`)
- **Database Engine**: MariaDB 10.11 LTS (`saas-stock-mariadb`) consolidating three logical databases (`db_articles`, `db_users`, `db_analytics`) initialized via `docker/mariadb/init-dbs.sql`
- **Ingress Reverse Proxy**: NGINX Alpine (`saas-stock-nginx`) configured via `docker/nginx/nginx.conf` to route `/api/` to FastAPI (`:8000`) and `/` + `/_next/webpack-hmr` to Next.js (`:3000`) on a single port (`NGINX_PORT`, default `8080`)
- **Lifecycle Automation**: Single-file deployment script (`scripts/devops/deploy.sh`) with pre-flight checks and readiness health gates

---

## 📁 Monorepo Map

```text
SaaSStockDepositControl/
├── backend/
│   ├── api/
│   │   ├── dependencies/          # Auth (RoleChecker, JWT claims) & DI service factories
│   │   ├── middlewares/           # Request-scoped multi-tenant JWT middleware (tenant_auth.py)
│   │   ├── v1/                    # REST routers: health, auth, users, articles, stock, enterprises, branches, reports
│   │   ├── exception_handlers.py  # Domain-to-HTTP exception mapping
│   │   ├── main.py                # FastAPI application entrypoint & CORS setup
│   │   └── README.md              # Primary adapter layer guidelines
│   ├── app/
│   │   ├── articles/              # Catalog search, pagination & barcode lookup services/ports
│   │   ├── branches/              # Branch domain models, ports & services
│   │   ├── enterprises/           # Enterprise/tenant domain models, ports & services
│   │   ├── movements/             # AuditService, StockKPIService, StockLookupService, VatClassifier, DeltaCalculator
│   │   ├── ports/                 # Core database & security abstract ports
│   │   ├── reports/               # Shrinkage, goods-received & daily balance domain services
│   │   ├── users/                 # AuthService, UserService (status/role management) & user ports
│   │   ├── work_sessions/         # Active branch work session lifecycle services & ports
│   │   ├── exceptions.py          # Pure domain exceptions
│   │   └── README.md              # Domain & application layer rules
│   ├── adapters/
│   │   ├── database/              # SQLAlchemy async engines, session factories & ContextVar tenant binding
│   │   ├── repositories/          # SQLAlchemy repositories & declarative ORM models (articles, users, analytics)
│   │   ├── security/              # PyJWT TokenProvider & BcryptPasswordHasher
│   │   └── README.md              # Secondary adapter layer rules
│   ├── migrations/
│   │   ├── versions/              # Alembic revisions for db_articles
│   │   ├── versions_users/        # Alembic revisions for db_users
│   │   ├── versions_analytics/    # Alembic revisions for db_analytics
│   │   ├── alembic.ini            # Default Alembic config (db_articles)
│   │   ├── alembic_users.ini      # Alembic config for db_users
│   │   ├── alembic_analytics.ini  # Alembic config for db_analytics
│   │   └── env.py                 # Multi-DB async migration environment (supports DB_TARGET)
│   ├── scripts/
│   │   └── seed.py                # Idempotent multi-DB data seeder (Faker es_AR)
│   ├── tests/                     # Unit, integration & security/RBAC test suites
│   ├── README.md
│   ├── requirements.txt
│   └── pytest.ini
├── frontend-web/
│   ├── app/                       # Next.js App Router: /login, /dashboard, /catalog, /audit, /reports, /users, /debug
│   ├── components/                # Layout shell, KPI cards, barcode scanner, tables & role guards
│   ├── lib/
│   │   ├── ports/                 # DataClientPort.ts contract
│   │   ├── adapters/              # ApiDataClient.ts, httpClient.ts, mappers.ts
│   │   ├── context/               # DataContext.tsx & ApiDataContext.tsx
│   │   ├── mocks/                 # MockDataContext.tsx & seed-data.ts
│   │   ├── types/                 # Domain & API TypeScript interfaces
│   │   └── utils/                 # JWT parser & formatting helpers
│   ├── package.json
│   └── README.md
├── frontend-mobile/
│   ├── src/
│   │   ├── screens/               # LoginScreen, DashboardScreen, AuditArticleScreen, CatalogScreen
│   │   ├── navigation/            # AppNavigator.tsx with TopAppBar & SidebarDrawer
│   │   ├── ports/                 # MobileDataClientPort.ts contract
│   │   ├── adapters/              # apiMobileDataClient.ts & mockMobileDataClient.ts
│   │   ├── services/domain/       # Pure domain services: AuditValidator, DeltaCalculator, FefoEvaluator
│   │   ├── context/               # AuthContext.tsx & DataContext.tsx
│   │   ├── components/            # Reusable mobile UI & layout components
│   │   ├── types/                 # Auth, article & audit TypeScript models
│   │   └── utils/                 # constants.ts, designTokens.ts, jwtDecoder.ts
│   ├── App.tsx
│   └── package.json
├── shared/
│   └── design-tokens/             # Shared semantic design tokens across Web and Mobile
├── docker/
│   ├── mariadb/
│   │   └── init-dbs.sql           # Auto-creates db_articles, db_users, db_analytics & app_user grants
│   └── nginx/
│       └── nginx.conf             # Reverse proxy routing (/api/ -> :8000, / -> :3000, HMR WebSockets)
├── scripts/
│   └── devops/
│       └── deploy.sh              # Single-file Docker Compose deployment & health check CLI
├── docs/
│   ├── ARCHITECTURE.md            # Full-stack & multi-DB Hexagonal Architecture reference
│   ├── API_DOCUMENTATION.md       # Complete REST API endpoint reference
│   ├── openapi.json               # OpenAPI 3.1.0 specification
│   ├── Plan.md
│   └── deploy/
│       └── README.md              # Container infrastructure & NGINX deployment runbook
├── specs/                         # Feature specifications & architectural plans
├── .env.example                   # Environment variable template
├── docker-compose.yml             # MariaDB 10.11 + NGINX Alpine service definitions
└── README.md
```

---

## 🔐 Multi-Database & Tenant Model

The persistence layer consolidates **three logical MariaDB databases** inside a single MariaDB 10.11 engine (`backend/adapters/database/connection.py`), each backed by its own SQLAlchemy declarative base and async session factory:

| Logical Database | Declarative Base | Session Factory | Primary Tables | Domain Repositories |
|:-----------------|:-----------------|:----------------|:---------------|:--------------------|
| `db_users` | `BaseUsers` | `get_users_session_factory()` | `enterprises`, `branches`, `users`, `roles`, `user_roles` | `SQLAlchemyUserRepository`, `SQLAlchemyEnterpriseRepository`, `SQLAlchemyBranchRepository` |
| `db_articles` | `BaseArticles` | `get_articles_session_factory()` | `familias`, `grupos`, `marcas`, `articulos`, `stock_por_deposito`, `lotes_por_deposito`, `codigos_barra_articulo`, plus legacy catalog tables (`empresas`, `sucursales`, `depositos`) | `SQLAlchemyArticleRepository`, `SQLAlchemyStockRepository` |
| `db_analytics` | `BaseAnalytics` | `get_analytics_session_factory()` | `record_tenants`, `work_sessions`, `audit_records`, `daily_reports`, `critical_shrinkage_alerts` | `SQLAlchemyAuditRepository`, `SQLAlchemyWorkSessionRepository`, `SQLAlchemyReportRepository` |

### Request-Scoped Tenant Isolation
- `TenantAuthMiddleware` (`backend/api/middlewares/tenant_auth.py`) intercepts incoming HTTP requests, verifies the Bearer JWT via `TokenProvider`, and extracts `tenant_id`, `branch_id`, and `user_id` (`id_usuario`).
- The extracted identity is bound to a request-scoped `ContextVar` (`backend/adapters/database/multi_tenant.py`) and automatically reset in a `finally` block after response completion, preventing cross-request state leakage.

---

## 🧩 Domain & API Boundaries (` API v1 `)

All REST routes are mounted under `/api/v1` in `backend/api/main.py` and wired through `backend/api/dependencies/services.py`:

| Module / Prefix | Router File | Key Endpoints | Domain Services & Capabilities |
|:----------------|:------------|:--------------|:-------------------------------|
| `/api/v1/health` | `api/v1/health.py` | `GET /api/v1/health` | Probes database connectivity (`SELECT 1`) and returns HTTP `200` (`healthy`) or `503` (`unhealthy`). |
| `/api/v1/auth` | `api/v1/auth.py` | `POST /api/v1/auth/login` | `AuthService`: Validates credentials against `db_users`, checks `is_active`, and issues signed JWT with `tenant_id`, `branch_id`, `id_usuario`, and primary `role`. |
| `/api/v1/users` | `api/v1/users.py` | `GET /api/v1/users`<br/>`PATCH /api/v1/users/{id}/status`<br/>`PUT /api/v1/users/{id}/roles` | `UserService` (`administrador` only): Tenant-scoped user listing, active status toggle with **self-lockout protection**, and role assignment enforcing a **single-role constraint** and **self-demotion protection**. |
| `/api/v1/articles` | `api/v1/articles.py` | `GET /api/v1/articles`<br/>`GET /api/v1/articles/search`<br/>`GET /api/v1/articles/{id}` | `ArticleSearchService`: Paginated catalog filtering, multi-barcode/SKU lookup, FEFO expiration projection, and role-based output serialization (`ArticuloAdminOut` vs `ArticuloPublicOut`). |
| `/api/v1/stock` | `api/v1/stock.py` | `POST /api/v1/stock/audit`<br/>`POST /api/v1/stock/audit/batch`<br/>`GET /api/v1/stock/position`<br/>`GET /api/v1/stock/kpis` | `AuditService`, `StockLookupService`, `StockKPIService`, `WorkSessionService`: Single and offline-batch physical audit registration, stock position lookup with fallback, and database-aggregated dashboard KPIs (`GET /api/v1/stock/kpis`). |
| `/api/v1/enterprises` | `api/v1/enterprises.py` | `GET`, `POST`, `PUT`, `DELETE` | `EnterpriseService` (`administrador` only): CRUD management for tenant enterprises in `db_users`. |
| `/api/v1/branches` | `api/v1/branches.py` | `GET`, `POST`, `PUT`, `DELETE` | `BranchService` (`administrador` only): Tenant-scoped branch CRUD operations in `db_users`. |
| `/api/v1/reports` | `api/v1/reports.py` | `GET /api/v1/reports/shrinkage`<br/>`GET /api/v1/reports/goods-received`<br/>`GET /api/v1/reports/inventory-balance` | `ReportService` (`administrador` only): Financial shrinkage (`Baja`), goods received (`Alta`), and daily inventory balance reports with VAT-aware (`0%` pharmaceuticals vs `21%` standard) `Decimal` valuation. |

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` at the repository root before launching containers or backend services:

```bash
cp .env.example .env
```

### Root & Backend Environment Variables (`.env`)

| Variable | Default / Example | Description |
|:---------|:------------------|:------------|
| `MARIADB_ROOT_PASSWORD` | `changeme_root_password` | MariaDB container `root` superuser password |
| `MARIADB_APP_PASSWORD` | `changeme_app_password` | Password granted to `app_user` by `init-dbs.sql` |
| `MARIADB_USER` / `MARIADB_PASSWORD` | `app_user` / `changeme_app_password` | Optional standard MariaDB container user credentials |
| `MARIADB_PORT` | `3306` | Host port mapped to the MariaDB container (`saas-stock-mariadb`) |
| `DB_HOST` | `localhost` | Database hostname for backend & Alembic connections |
| `DB_PORT` | `3306` | Database port for backend & Alembic connections |
| `DB_USER` | `app_user` | Application database user |
| `DB_PASSWORD` (`DB_PASS`) | `changeme_app_password` | Application database password |
| `DB_NAME_ARTICLES` | `db_articles` | Catalog and stock logical database name |
| `DB_NAME_USERS` | `db_users` | Identity, enterprises, branches, and RBAC logical database name |
| `DB_NAME_ANALYTICS` | `db_analytics` | Work sessions, audit ledger, and reports logical database name |
| `DATABASE_URL` (`ARTICLES_DATABASE_URL`) | `mysql+aiomysql://app_user:...@localhost:3306/db_articles` | Full SQLAlchemy async connection URL for `db_articles` |
| `USERS_DATABASE_URL` | `mysql+aiomysql://app_user:...@localhost:3306/db_users` | Full SQLAlchemy async connection URL for `db_users` |
| `ANALYTICS_DATABASE_URL` | `mysql+aiomysql://app_user:...@localhost:3306/db_analytics` | Full SQLAlchemy async connection URL for `db_analytics` |
| `SECRET_KEY` (`JWT_SECRET_KEY`) | `changeme_secret_key` | HMAC signing secret for JWT authentication tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm used by `TokenProvider` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | JWT expiration window in minutes (default 8 hours) |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:8080,...` | Comma-separated list of allowed CORS origins |
| `API_V1_STR` | `/api/v1` | Base path prefix for v1 REST API endpoints |
| `PROJECT_NAME` | `SaaS Stock Deposit Control API` | FastAPI application title |
| `DEBUG` | `false` | Enables verbose debug mode when set to `true` |
| `NGINX_PORT` | `8080` | Host port exposed by the `saas-stock-nginx` reverse proxy gateway |

### Frontend Environment Variables

| Client | Variable | Default | Description |
|:-------|:---------|:--------|:------------|
| `frontend-web` | `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL for backend API requests (use `http://localhost:8080` when routing through NGINX) |
| `frontend-web` | `NEXT_PUBLIC_DATA_SOURCE` | `api` | Adapter toggle: `api` uses live `ApiDataClient`; `mock` uses in-memory `MockDataProvider` |
| `frontend-mobile` | `EXPO_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL for mobile field requests |
| `frontend-mobile` | `EXPO_PUBLIC_USE_MOCK` | `false` | Adapter toggle: `'true'` selects `mockMobileDataClient`; otherwise uses `apiMobileDataClient` |

---

## 🚀 Useful Commands

### 1. Infrastructure Lifecycle (MariaDB + NGINX Gateway)
```bash
# Start MariaDB 10.11 + NGINX reverse proxy and wait for health checks
./scripts/devops/deploy.sh up

# Check container status and port bindings
./scripts/devops/deploy.sh status

# Execute instant health probes (MariaDB, NGINX, and /api/v1/health proxy check)
./scripts/devops/deploy.sh health

# Tail container logs (optional service filter: mariadb | nginx)
./scripts/devops/deploy.sh logs
./scripts/devops/deploy.sh logs nginx

# Stop containers gracefully (preserves mariadb_data volume)
./scripts/devops/deploy.sh down
```

### 2. Multi-Database Alembic Migrations
Run migrations from the repository root (with your Python virtual environment active):

```bash
# Migrate db_articles (default config)
alembic -c backend/migrations/alembic.ini upgrade head

# Migrate db_users
alembic -c backend/migrations/alembic_users.ini upgrade head

# Migrate db_analytics
alembic -c backend/migrations/alembic_analytics.ini upgrade head
```

Alternatively, override the target database dynamically via `DB_TARGET`:
```bash
DB_TARGET=articles alembic -c backend/migrations/alembic.ini upgrade head
DB_TARGET=users alembic -c backend/migrations/alembic.ini upgrade head
DB_TARGET=analytics alembic -c backend/migrations/alembic.ini upgrade head
```

### 3. Database Seeding
Populate all three databases (`db_users`, `db_articles`, `db_analytics`) with realistic multi-tenant catalog, FEFO lots, users (`password123`), and work sessions:
```bash
python -m backend.scripts.seed
```

### 4. Backend Development Server & Tests
```bash
# Activate virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Start FastAPI development server on port 8000
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

# Run backend test suite
pytest
```

### 5. Web Frontend (`frontend-web/`)
```bash
cd frontend-web
npm install

# Start Next.js development server on http://localhost:3000
npm run dev

# Run unit and component tests with Vitest
npx vitest run

# Build production bundle
npm run build
```

### 6. Mobile Frontend (`frontend-mobile/`)
```bash
cd frontend-mobile
npm install

# Start Expo Metro bundler
npx expo start
```

---

## ✅ Development Rules

1. **Pure Domain Layer**: Keep `backend/app/` and `frontend-mobile/src/services/domain/` free of HTTP, ORM, or storage framework imports.
2. **Hexagonal Port/Adapter Discipline**: Route all persistence and external API calls through abstract ports (`backend/app/*/ports.py`, `DataClientPort`, `MobileDataClientPort`).
3. **Tenant Context Isolation**: Scope all multi-tenant queries using JWT-derived context (`tenant_id`, `branch_id`, `id_usuario`).
4. **Strict Financial Masking**: Never expose `pcio_com_siva` or valorized currency fields (`monto_valorizado`, `applied_unit_cost`) to `supervisor` or `auditor` roles.
5. **Exact Monetary Arithmetic**: Use `Decimal` for all backend financial and VAT calculations—never floating-point numbers.
6. **Database Ownership Boundaries**: Respect the separation between `BaseUsers` (`db_users`), `BaseArticles` (`db_articles`), and `BaseAnalytics` (`db_analytics`).

---

## 📚 Key Documentation

- **[Architecture Reference (`docs/ARCHITECTURE.md`)](docs/ARCHITECTURE.md)** — Full-stack Hexagonal Architecture, multi-DB ownership, and client adapter design
- **[REST API Documentation (`docs/API_DOCUMENTATION.md`)](docs/API_DOCUMENTATION.md)** — Complete endpoint contracts, request/response payloads, and RBAC matrix
- **[OpenAPI 3.1.0 Specification (`docs/openapi.json`)](docs/openapi.json)** — Machine-readable OpenAPI schema
- **[Deployment & Infrastructure Runbook (`docs/deploy/README.md`)](docs/deploy/README.md)** — MariaDB 10.11 consolidation, NGINX ingress proxy, and `deploy.sh` guide
- **[Backend Guide (`backend/README.md`)](backend/README.md)** — Backend setup, layers ([`backend/api/README.md`](backend/api/README.md), [`backend/app/README.md`](backend/app/README.md), [`backend/adapters/README.md`](backend/adapters/README.md)), and testing
- **[Web Frontend Guide (`frontend-web/README.md`)](frontend-web/README.md)** — Next.js web application setup and scripts
- **Mobile Frontend (`frontend-mobile/package.json`)** — Expo SDK 57 / React Native 0.86 mobile audit client (`frontend-mobile/README.md` if added in future iterations)
