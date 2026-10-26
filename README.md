# 🏛️ SaaS Stock Deposit Control - Enterprise Platform

A multi-tenant inventory intelligence platform for warehouse auditing, stock reconciliation, FEFO lot tracking, branch operations, and finance-oriented reporting. The monorepo implements a strict **Hexagonal Architecture (Ports & Adapters)** across its FastAPI backend, Next.js web application, and React Native (Expo) mobile field client, backed by a 3-database MariaDB topology, a single-origin Caddy 2 reverse proxy, and a portable multi-profile Docker Compose stack.

---

## 📖 Executive Summary

The platform connects warehouse operators (`auditor`), branch supervisors (`supervisor`), and organization administrators (`administrador`) through a unified multi-tenant ecosystem that isolates authentication/tenancy, operational catalog/stock, and analytical audit ledgers into distinct logical databases:

- **Field Auditing & Stock Movements**: Single and offline-batch physical stock counts, theoretical delta calculation, FEFO lot evaluation, and automatic voucher classification (`Alta`, `Baja`, `Sin Acción`).
- **Identity, Tenancy & RBAC**: Tenant-scoped authentication, enterprise/branch hierarchy, and administrator user lifecycle management (`db_users`).
- **Operational Catalog & Stock Positions**: Multi-barcode article lookup, stock per deposit, and FEFO lot expiration tracking (`db_articles`). Supports **read-only hybrid on-premise mode** (`RUN_MIGRATIONS_ARTICLES=false`) for connecting directly to existing pharmacy databases.
- **Financial & Shrinkage Analytics**: Active work sessions, immutable audit records, database-aggregated dashboard KPIs, and VAT-aware shrinkage, goods-received, and daily inventory balance reports (`db_analytics`).
- **Role-Based Financial Masking**: Confidential purchase costs (`pcio_com_siva`) and valorized monetary amounts (`monto_valorizado`) are structurally omitted for non-administrator roles at both the API schema layer and client adapters.

---

## 🛠️ Architecture & Technology Stack

### Backend (`backend/`)
- **Runtime & Framework**: Python 3.12+, FastAPI, Pydantic V2 (containerized as non-root `appuser` UID `10001`)
- **Persistence & ORM**: SQLAlchemy 2.0 Async ORM + `aiomysql` driver with configurable TLS (`DB_SSL_MODE=disable|require|verify-ca`) and deterministic URL precedence (`<TARGET>_DATABASE_URL` $\rightarrow$ `DATABASE_URL` $\rightarrow$ `DB_*`)
- **Migrations**: Alembic multi-database configuration (`db_articles`, `db_users`, `db_analytics`) with per-database entrypoint switches (`RUN_MIGRATIONS_ARTICLES`, `RUN_MIGRATIONS_USERS`, `RUN_MIGRATIONS_ANALYTICS`)
- **Security**: PyJWT (`HS256` signed claims with `tenant_id`, `branch_id`, `id_usuario`, `role`), `bcrypt` password hashing, and startup `SECRET_KEY` enforcement in `ENVIRONMENT=production`
- **Quality & Testing**: `pytest` + `pytest-asyncio` + `pytest-cov` + `aiosqlite`, `ruff` (lint & format via `backend/pyproject.toml`), and `pip-audit`

### Web Frontend (`frontend-web/`)
- **Framework**: Next.js 16.4 (App Router, `output: "standalone"`), React 19, TypeScript 5 (containerized as non-root `nextjs` UID `1001`)
- **Styling**: Tailwind CSS v4 (`@tailwindcss/postcss`), Lucide React icons, glassmorphic dark UI theme
- **Scanner & Hardware**: `html5-qrcode` paired with native `BarcodeDetector`, permission fast-path + 150ms HAL release delay (`useCameraPermissions`), and start/stop promise mutex (`useBarcodeScanner`)
- **Architecture**: Hexagonal `DataClientPort` with runtime toggle (`NEXT_PUBLIC_DATA_SOURCE=api|mock`) and relative API URLs (`NEXT_PUBLIC_API_URL=""`) behind the single-origin proxy
- **Testing**: Vitest + React Testing Library (`jsdom`)

### Mobile Frontend (`frontend-mobile/`)
- **Framework**: Expo SDK 57, React Native 0.86, React 19, TypeScript
- **Styling**: NativeWind v4 + warehouse high-contrast design tokens (48dp minimum touch targets)
- **Persistence & Dynamic Server Discovery**: `@react-native-async-storage/async-storage` storing tenant-isolated sessions (`audit_global:session:{tenantId}:{branchId}`) and dynamic runtime server URLs (`@stock_server_url`) configured via `ServerSettingsModal` (**Configuración del Servidor** + `/api/v1/health` probe) with cleartext HTTP LAN support (`expo-build-properties`)
- **Architecture**: Hexagonal `MobileDataClientPort` (`ApiMobileDataClient` and `MockMobileDataClient` toggled via `EXPO_PUBLIC_USE_MOCK`), field-role access guard (`auditor` and `supervisor` only), recursive financial field sanitizer (`stripFinancialFields`), and pure domain services (`AuditValidator`, `DeltaCalculator`, `FefoEvaluator`)

### Shared Design System (`shared/design-tokens/`)
- Centralized cross-platform semantic color palettes, status badges (`Alta`, `Baja`, `Sin Acción`, FEFO severity), and spacing primitives shared across `frontend-web` and `frontend-mobile`.

### Infrastructure, DevOps & CI/CD (`docker/`, `scripts/devops/`, `.github/workflows/`)
- **Single-Origin Reverse Proxy**: Caddy 2 Alpine (`docker/caddy/Caddyfile`) serving plain HTTP on `:8080` (LAN, on-premise, or Cloudflare Tunnel) or automatic Let's Encrypt HTTPS when `SERVER_NAME` is a domain and `docker-compose.public.yml` is enabled
- **Database Engine**: MariaDB 10.11 LTS (`--profile with-db`, bound strictly to `127.0.0.1:3306`) consolidating `db_articles`, `db_users`, and `db_analytics` via `docker/mariadb/01-init-dbs.sh`
- **Compose Profiles**: `default` (external DB), `with-db` (bundled MariaDB), `demo` (one-shot `seed` container), `tunnel` (`cloudflared` Zero Trust tunnel), plus `docker-compose.dev.yml` (hot-reload bind mounts) and `docker-compose.public.yml` (ports `80`/`443`)
- **Lifecycle & Verification CLI**: `scripts/devops/deploy.sh` (`up`, `down`, `status`, `health`, `logs`, `pull`, `update` with automatic rollback via `.previous_tag`, `rollback`, `backup`) and `scripts/devops/verify-local-package.sh`
- **CI/CD Pipelines**: GitHub Actions `.github/workflows/ci.yml` (path-filtered backend/web/mobile tests, MariaDB 10.11 migration reversibility + seed smoke test, Hadolint, Trivy, Gitleaks), `.github/workflows/cd.yml` (multi-arch `amd64`/`arm64` GHCR builds, SSH staging/production deploys with automatic rollback), and `.github/workflows/mobile-release.yml`

---

## 📁 Monorepo Map

```text
SaaSStockDepositControl/
├── .github/
│   ├── workflows/                 # ci.yml, cd.yml, mobile-release.yml
│   └── dependabot.yml             # Automated dependency & GitHub Actions updates
├── backend/
│   ├── api/
│   │   ├── dependencies/          # Auth (RoleChecker, JWT claims) & DI service factories
│   │   ├── middlewares/           # Request-scoped multi-tenant JWT middleware (tenant_auth.py)
│   │   ├── v1/                    # REST routers: health, auth, users, articles, stock, enterprises, branches, reports
│   │   ├── exception_handlers.py  # Domain-to-HTTP exception mapping
│   │   ├── main.py                # FastAPI entrypoint, production SECRET_KEY lifespan guard & CORS setup
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
│   │   ├── database/              # SQLAlchemy async engines, TLS/URL resolution & ContextVar tenant binding
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
│   │   ├── env.py                 # Multi-DB async migration environment
│   │   └── url_config.py          # URL precedence, configparser %-escaping & SSL connect_args helpers
│   ├── scripts/
│   │   └── seed.py                # Idempotent multi-DB data seeder (Faker es_AR)
│   ├── tests/                     # Unit, domain, adapter, db, report & API integration test suites
│   ├── Dockerfile                 # Multi-stage Python 3.12-slim production image (UID 10001)
│   ├── docker-entrypoint.sh       # Per-database migration runner & uvicorn launcher
│   ├── pyproject.toml             # Ruff linter and formatter configuration
│   ├── requirements.txt           # Production runtime dependencies
│   ├── requirements-dev.txt       # Test, coverage, lint & security audit dependencies
│   ├── pytest.ini
│   └── README.md
├── frontend-web/
│   ├── app/                       # Next.js App Router: /login, /dashboard, /catalog, /audit, /reports, /users, /debug
│   ├── components/                # Layout shell, KPI cards, BarcodeScannerModal, tables & role guards
│   ├── lib/
│   │   ├── ports/                 # DataClientPort.ts contract
│   │   ├── adapters/              # ApiDataClient.ts, httpClient.ts, mappers.ts
│   │   ├── context/               # DataContext.tsx & ApiDataContext.tsx
│   │   ├── hooks/                 # useBarcodeScanner.ts, useCameraPermissions.ts, catalog/KPI hooks
│   │   ├── mocks/                 # MockDataContext.tsx & seed-data.ts
│   │   ├── types/                 # Domain & API TypeScript interfaces
│   │   └── utils/                 # JWT parser & formatting helpers
│   ├── Dockerfile                 # Multi-stage Node 20 Alpine standalone image (UID 1001)
│   ├── next.config.ts             # Standalone output configuration
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
│   │   ├── components/            # Reusable mobile UI & ServerSettingsModal.tsx
│   │   ├── types/                 # Auth, article & audit TypeScript models
│   │   └── utils/                 # serverUrl.ts, constants.ts, designTokens.ts, jwtDecoder.ts
│   ├── App.tsx
│   ├── app.json                   # Expo config with cleartext HTTP LAN support
│   ├── package.json
│   └── README.md
├── shared/
│   └── design-tokens/             # Shared semantic design tokens across Web and Mobile
├── docker/
│   ├── caddy/
│   │   ├── Caddyfile              # Single-origin reverse proxy (/api/* -> backend:8000, /* -> web:3000)
│   │   └── Dockerfile             # Caddy 2 Alpine image
│   └── mariadb/
│       └── 01-init-dbs.sh         # Creates db_articles, db_users, db_analytics & app_user grants
├── scripts/
│   └── devops/
│       ├── deploy.sh              # Deployment, health-gated update, rollback & backup CLI
│       └── verify-local-package.sh # Read-only on-premise verification probe
├── docs/
│   ├── ARCHITECTURE.md            # Full-stack & multi-DB Hexagonal Architecture reference
│   ├── API_DOCUMENTATION.md       # Complete REST API endpoint reference
│   ├── MANUAL_TESTING_AND_DEMO_GUIDE.md # Step-by-step manual testing, QA use cases & live demo script
│   ├── openapi.json               # OpenAPI 3.1.0 specification
│   ├── adr/                       # Architectural Decision Records
│   ├── cliente/                   # Pharmacy client commercial & operational dossier (Spanish)
│   └── deploy/
│       ├── README.md              # Multi-target deployment runbooks (On-Premise, Oracle ARM64, Tunnel)
│       └── local-onpremise-runbook.md # Hybrid pharmacy on-premise runbook (read-only db_articles)
├── specs/                         # Feature specifications, task slices & handoff logs
├── GLOSSARY.md                    # Ubiquitous domain language definitions
├── AGENTS.md                      # Canonical commands, architecture rules & workflow boundaries
├── .env.example                   # Environment variable template
├── docker-compose.yml             # Base multi-profile stack (proxy, backend, web, mariadb, seed, cloudflared)
├── docker-compose.public.yml      # Opt-in override publishing ports 80/443 for public HTTPS domains
├── docker-compose.dev.yml         # Local development override with bind mounts & hot reload
└── README.md
```

---

## 🔐 Multi-Database & Tenant Model

The persistence layer consolidates **three logical MariaDB databases** (`backend/adapters/database/connection.py`), each backed by its own SQLAlchemy declarative base and async session factory:

| Logical Database | Declarative Base | Session Factory | Primary Tables | Domain Repositories |
|:-----------------|:-----------------|:----------------|:---------------|:--------------------|
| `db_users` | `BaseUsers` | `get_users_session_factory()` | `enterprises`, `branches`, `users`, `roles`, `user_roles` | `SQLAlchemyUserRepository`, `SQLAlchemyEnterpriseRepository`, `SQLAlchemyBranchRepository` |
| `db_articles` | `BaseArticles` | `get_articles_session_factory()` | `familias`, `grupos`, `marcas`, `articulos`, `stock_por_deposito`, `lotes_por_deposito`, `codigos_barra_articulo`, plus legacy catalog tables (`empresas`, `sucursales`, `depositos`) | `SQLAlchemyArticleRepository`, `SQLAlchemyStockRepository` |
| `db_analytics` | `BaseAnalytics` | `get_analytics_session_factory()` | `record_tenants`, `work_sessions`, `audit_records`, `daily_reports`, `critical_shrinkage_alerts` | `SQLAlchemyAuditRepository`, `SQLAlchemyWorkSessionRepository`, `SQLAlchemyReportRepository` |

### Request-Scoped Tenant Isolation
- `TenantAuthMiddleware` (`backend/api/middlewares/tenant_auth.py`) intercepts incoming HTTP requests, verifies the Bearer JWT via `TokenProvider`, and extracts `tenant_id`, `branch_id`, and `user_id` (`id_usuario`).
- The extracted identity is bound to a request-scoped `ContextVar` (`backend/adapters/database/multi_tenant.py`) and automatically reset in a `finally` block after response completion, preventing cross-request state leakage.

---

## 🧩 Domain & API Boundaries (`API v1`)

All REST routes are mounted under `/api/v1` in `backend/api/main.py` and wired through `backend/api/dependencies/services.py`:

| Module / Prefix | Router File | Key Endpoints | Domain Services & Capabilities |
|:----------------|:------------|:--------------|:-------------------------------|
| `/api/v1/health` | `api/v1/health.py` | `GET /health`<br/>`GET /api/v1/health` | Probes connectivity (`SELECT 1`) across all three databases (`articles`, `users`, `analytics`) and returns HTTP `200` (`healthy`) or `503` (`unhealthy`) with application `version`. |
| `/api/v1/auth` | `api/v1/auth.py` | `POST /api/v1/auth/login` | `AuthService`: Validates credentials against `db_users`, checks `is_active`, and issues signed JWT with `tenant_id`, `branch_id`, `id_usuario`, and primary `role`. |
| `/api/v1/users` | `api/v1/users.py` | `GET /api/v1/users`<br/>`PATCH /api/v1/users/{id}/status`<br/>`PUT /api/v1/users/{id}/roles` | `UserService` (`administrador` only): Tenant-scoped user listing, active status toggle with **self-lockout protection**, and role assignment enforcing a **single-role constraint** and **self-demotion protection**. |
| `/api/v1/articles` | `api/v1/articles.py` | `GET /api/v1/articles`<br/>`GET /api/v1/articles/search`<br/>`GET /api/v1/articles/{id}` | `ArticleSearchService`: Paginated catalog filtering, multi-barcode/SKU lookup, FEFO expiration projection, and role-based output serialization (`ArticuloAdminOut` vs `ArticuloPublicOut`). |
| `/api/v1/stock` | `api/v1/stock.py` | `POST /api/v1/stock/audit`<br/>`POST /api/v1/stock/audit/batch`<br/>`GET /api/v1/stock/position`<br/>`GET /api/v1/stock/kpis` | `AuditService`, `StockLookupService`, `StockKPIService`, `WorkSessionService`: Single and offline-batch physical audit registration, stock position lookup with fallback, and database-aggregated dashboard KPIs (`GET /api/v1/stock/kpis`). |
| `/api/v1/enterprises` | `api/v1/enterprises.py` | `GET`, `POST`, `PUT`, `DELETE` | `EnterpriseService`: CRUD management for tenant enterprises in `db_users`. |
| `/api/v1/branches` | `api/v1/branches.py` | `GET`, `POST`, `PUT`, `DELETE` | `BranchService`: Tenant-scoped branch CRUD operations in `db_users`. |
| `/api/v1/reports` | `api/v1/reports.py` | `GET /api/v1/reports/shrinkage`<br/>`GET /api/v1/reports/goods-received`<br/>`GET /api/v1/reports/inventory-balance` | `ReportService` (`administrador` only): Financial shrinkage (`Baja`), goods received (`Alta`), and daily inventory balance reports with VAT-aware (`0%` pharmaceuticals vs `21%` standard) `Decimal` valuation. |

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` at the repository root before launching containers or backend services:

```bash
cp .env.example .env && chmod 600 .env
```

### Root & Backend Environment Variables (`.env`)

| Variable | Default / Example | Description |
|:---------|:------------------|:------------|
| `COMPOSE_PROJECT_NAME` | `saas-stock` | Compose project prefix so image names resolve consistently |
| `GHCR_OWNER` | `stockdeposit` | GitHub Container Registry owner/organization |
| `IMAGE_TAG` | `latest` (`edge`, `vX.Y.Z`) | Container image tag deployed and managed by `deploy.sh` |
| `SERVER_NAME` | `:8080` | Caddy site address: `:8080` for plain HTTP (LAN/Tunnel) or domain for automatic HTTPS |
| `HTTP_PORT` | `8080` | Host port published by the Caddy proxy in plain-HTTP mode |
| `COMPOSE_FILE` | *(commented by default)* | Set to `docker-compose.yml:docker-compose.public.yml` when `SERVER_NAME` is a public domain requiring ports `80`/`443` |
| `ACME_EMAIL_OPTION` | *(commented by default)* | Optional full Caddy directive (`email ops@example.com`) for Let's Encrypt |
| `ENVIRONMENT` | `production` | Enforces strict `SECRET_KEY` validation at startup when `production` |
| `SECRET_KEY` | *(required, $\ge 32$ chars)* | HMAC signing secret for JWT tokens (`python3 -c "import secrets; print(secrets.token_urlsafe(48))"`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | JWT expiration window in minutes (default 8 hours) |
| `RUN_MIGRATIONS` | `true` | Master toggle to run Alembic migrations on backend container startup |
| `RUN_MIGRATIONS_ARTICLES` | `true` (`false` on pharmacy hybrid) | Per-DB switch for `db_articles` (set `false` when pointing at a read-only pharmacy DB) |
| `RUN_MIGRATIONS_USERS` | `true` | Per-DB switch for `db_users` |
| `RUN_MIGRATIONS_ANALYTICS` | `true` | Per-DB switch for `db_analytics` |
| `UVICORN_WORKERS` | `2` | Number of Uvicorn worker processes in the backend container |
| `CORS_ORIGINS` | `http://localhost:8080` | Comma-separated list of allowed CORS origins (empty default when unset) |
| `DB_HOST` / `DB_PORT` | `mariadb` / `3306` | Database host and port (`mariadb` inside Compose, `127.0.0.1` from host shell) |
| `DB_USER` / `DB_PASSWORD` | `app_user` / *(required)* | Application database credentials |
| `DB_NAME_ARTICLES` / `USERS` / `ANALYTICS` | `db_articles` / `db_users` / `db_analytics` | Logical database names |
| `DB_SSL_MODE` / `DB_SSL_CA` | `disable` / *(optional)* | Database TLS mode (`disable`, `require`, `verify-ca`) and CA bundle path |
| `DATABASE_URL` / `<TARGET>_DATABASE_URL` | *(commented by default)* | Optional full SQLAlchemy URL overrides (`ARTICLES_DATABASE_URL`, `USERS_DATABASE_URL`, `ANALYTICS_DATABASE_URL`) |
| `MARIADB_ROOT_PASSWORD` | *(required for `with-db`)* | MariaDB container `root` superuser password |
| `MARIADB_APP_PASSWORD` | *(required for `with-db`)* | Password granted to `DB_USER` by `01-init-dbs.sh` (must match `DB_PASSWORD`) |
| `MARIADB_PORT` | `3306` | Host port bound to `127.0.0.1` for the bundled MariaDB container |
| `CLOUDFLARE_TUNNEL_TOKEN` | *(required for `tunnel`)* | Cloudflare Zero Trust tunnel token (`--profile tunnel`) |

### Frontend Environment Variables

| Client | Variable | Default | Description |
|:-------|:---------|:--------|:------------|
| `frontend-web` | `NEXT_PUBLIC_API_URL` | `""` (empty) | Relative `/api/v1/*` behind Caddy single-origin proxy (set `http://localhost:8000` only when running Next.js outside Compose without a proxy) |
| `frontend-web` | `NEXT_PUBLIC_DATA_SOURCE` | `api` | Adapter toggle: `api` uses live `ApiDataClient`; `mock` uses in-memory `MockDataProvider` |
| `frontend-mobile` | `EXPO_PUBLIC_API_URL` | `http://localhost:8000` | Fallback backend API URL (overridden at runtime via `ServerSettingsModal` / `@stock_server_url` in `AsyncStorage`) |
| `frontend-mobile` | `EXPO_PUBLIC_USE_MOCK` | `false` | Adapter toggle: `'true'` selects `mockMobileDataClient`; otherwise uses `apiMobileDataClient` |

---

## 🚀 Useful Commands

### 1. Containerized Deployment & Lifecycle (`scripts/devops/deploy.sh`)
```bash
# Start proxy (Caddy), backend, web, and bundled MariaDB, then wait for /api/v1/health
./scripts/devops/deploy.sh up with-db

# Or start with one-shot demo data seeding via Docker Compose
docker compose --profile with-db --profile demo up -d

# Check container status and port bindings
./scripts/devops/deploy.sh status

# Probe /api/v1/health through the proxy (verifies articles, users, and analytics DBs)
./scripts/devops/deploy.sh health

# Run the read-only on-premise package verification probe
./scripts/devops/verify-local-package.sh

# Create an encrypted-permissions (0600) SQL backup of all 3 databases in backups/
./scripts/devops/deploy.sh backup

# Deploy a new image tag with automatic health-gated rollback (.previous_tag)
./scripts/devops/deploy.sh update v1.2.0
./scripts/devops/deploy.sh rollback

# Tail container logs (optional service filter: proxy | backend | web | mariadb)
./scripts/devops/deploy.sh logs backend

# Stop containers gracefully (preserves mariadb_data volume)
./scripts/devops/deploy.sh down
```

### 2. Multi-Database Alembic Migrations (Host Shell)
```bash
alembic -c backend/migrations/alembic.ini upgrade head
alembic -c backend/migrations/alembic_users.ini upgrade head
alembic -c backend/migrations/alembic_analytics.ini upgrade head
```

### 3. Database Seeding (Host Shell)
Populate all three databases (`db_users`, `db_articles`, `db_analytics`) with 500 pharmacy SKUs, FEFO lots, 3 users (`admin@globalmedica.com`, `supervisor@globalmedica.com`, `auditor@globalmedica.com` — password `123456`), and an active work session:
```bash
python -m backend.scripts.seed
```

### 4. Backend Development Server, Tests & Quality Checks (`cd backend`)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Run backend test suite and coverage
pytest
pytest --cov=backend --cov-report=term-missing tests/

# Run linter, formatter check, and dependency vulnerability audit
ruff check . && ruff format --check .
pip-audit -r requirements.txt
```

### 5. Web Frontend (`cd frontend-web`)
```bash
cd frontend-web
npm ci

# Start Next.js development server on http://localhost:3000
npm run dev

# Run Vitest unit/component tests, TypeScript check, linter, and standalone build
npm test
npx tsc --noEmit
npm run lint
npm run build
```

### 6. Mobile Frontend (`cd frontend-mobile`)
```bash
cd frontend-mobile
npm ci

# Verify TypeScript and Expo health, then start Metro bundler
npx tsc --noEmit
npx expo-doctor
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

- **[Manual Testing, Production Readiness & Live Demo Guide (`docs/MANUAL_TESTING_AND_DEMO_GUIDE.md`)](docs/MANUAL_TESTING_AND_DEMO_GUIDE.md)** — Step-by-step startup guide, 12 end-to-end QA use cases (`UC-01`–`UC-12`), and stakeholder live demo recording script
- **[Architecture Reference (`docs/ARCHITECTURE.md`)](docs/ARCHITECTURE.md)** — Full-stack Hexagonal Architecture, multi-DB ownership, Caddy ingress, and client adapter design
- **[REST API Documentation (`docs/API_DOCUMENTATION.md`)](docs/API_DOCUMENTATION.md)** — Complete endpoint contracts, request/response payloads, and RBAC matrix
- **[OpenAPI 3.1.0 Specification (`docs/openapi.json`)](docs/openapi.json)** — Machine-readable OpenAPI schema
- **[Deployment Runbooks (`docs/deploy/README.md`)](docs/deploy/README.md)** — Multi-target deployment guide (Client On-Premise, Oracle Cloud ARM64, Cloudflare Tunnel, `deploy.sh` lifecycle)
- **[Pharmacy Hybrid On-Premise Runbook (`docs/deploy/local-onpremise-runbook.md`)](docs/deploy/local-onpremise-runbook.md)** — Read-only external `db_articles` + bundled `db_users`/`db_analytics` + mobile LAN setup
- **[Client Commercial & Functional Dossier (`docs/cliente/README.md`)](docs/cliente/README.md)** — Executive value proposition, functional dossier, and role guide for pharmacy clients (Spanish)
- **[Domain Glossary (`GLOSSARY.md`)](GLOSSARY.md)** — Canonical ubiquitous language definitions
- **[Backend Guide (`backend/README.md`)](backend/README.md)** — Backend setup, layers ([`backend/api/README.md`](backend/api/README.md), [`backend/app/README.md`](backend/app/README.md), [`backend/adapters/README.md`](backend/adapters/README.md)), and testing
- **[Web Frontend Guide (`frontend-web/README.md`)](frontend-web/README.md)** — Next.js web application setup, camera scanner lifecycle, and scripts
- **[Mobile Frontend Guide (`frontend-mobile/README.md`)](frontend-mobile/README.md)** — Expo SDK 57 / React Native 0.86 mobile audit client, dynamic server URL configuration, and field security guards
