# 🔌 Primary Interface & Driving Adapters Layer (`backend/api/`)

This directory implements the **Primary (Driving) Adapters** of the SaaS Stock Deposit Control backend. It exposes the RESTful HTTP interface via **FastAPI**, manages the request lifecycle, enforces JWT authentication and Role-Based Access Control (RBAC), wires domain services to secondary database/security adapters through Dependency Injection, and translates domain exceptions into standardized HTTP responses.

---

## Directory Structure

```text
backend/api/
├── __init__.py
├── main.py                         # FastAPI application entrypoint, lifespan, CORS, middlewares, routers
├── exception_handlers.py           # Centralized DomainException -> HTTP JSON response translation
├── middlewares/
│   ├── __init__.py
│   └── tenant_auth.py              # TenantAuthMiddleware (JWT extraction -> ContextVar binding)
├── dependencies/
│   ├── __init__.py                 # Singleton providers: get_connection_provider, get_token_provider, get_password_hasher
│   ├── auth.py                     # oauth2_scheme, get_current_user_claims, RoleChecker
│   └── services.py                 # DI factories wiring repositories across db_articles, db_users, db_analytics
└── v1/
    ├── __init__.py
    ├── health.py                   # GET /health, GET /api/v1/health
    ├── auth.py                     # POST /api/v1/auth/login
    ├── articles.py                 # GET /api/v1/articles, /search, /{id_articulo}
    ├── stock.py                    # POST /api/v1/stock/audit, /audit/batch, GET /position, /kpis
    ├── enterprises.py              # CRUD /api/v1/enterprises
    ├── branches.py                 # CRUD /api/v1/branches
    ├── reports.py                  # GET /api/v1/reports/shrinkage, /goods-received, /inventory-balance
    ├── users.py                    # GET /api/v1/users, PATCH /{user_id}/status, PUT /{user_id}/roles
    └── schemas/
        ├── __init__.py
        └── stock.py                # ArticleStockPositionPublicOut, ArticleStockPositionAdminOut
```

---

## Core Components

### 1. Application Entrypoint (`backend/api/main.py`)
- **Lifespan Management**: Defines an `@asynccontextmanager` `lifespan` hook that gracefully disposes all active SQLAlchemy async connection pools (`provider.dispose()`) on application shutdown.
- **CORS & Local Network Support**: Configures `CORSMiddleware` using `CORS_ORIGINS` plus a private LAN regular expression (`localhost`, `127.0.0.1`, `192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`) so mobile barcode scanners and tablets on local warehouse Wi-Fi can communicate with the API.
- **Middleware Registration**: Registers `CORSMiddleware` and `TenantAuthMiddleware`.
- **Exception Handling**: Invokes `register_exception_handlers(app)` to bind domain exception handlers globally.
- **Router Mounting**: Mounts `health_router` at root (`/health`) for infrastructure probes and registers all 8 versioned routers under the `/api/v1` prefix.

### 2. Exception Translation (`backend/api/exception_handlers.py`)
Translates pure domain exceptions from `backend/app/exceptions.py` into structured HTTP JSON responses (`{"detail": ..., "error_type": ...}`), keeping HTTP status codes out of `backend/app/`:

| Exception Class / Source | HTTP Status Code | `error_type` / Behavior |
| :--- | :--- | :--- |
| `BusinessRuleViolationException` (domain validation / rule violation) | `400 Bad Request` | `"BusinessRuleViolation"` |
| `EntityNotFoundException` (missing domain entity) | `404 Not Found` | `"EntityNotFound"` |
| `NoActiveWorkSessionError` (audit without open branch session) | `409 Conflict` | `"NoActiveWorkSession"` |
| `DomainException` (fallback base domain error) | `500 Internal Server Error` | `"InternalDomainError"` |
| Invalid / Expired JWT (`get_current_user_claims`) | `401 Unauthorized` | `WWW-Authenticate: Bearer` |
| Insufficient Role (`RoleChecker`) | `403 Forbidden` | `"Operation not permitted for this role"` |

### 3. Multi-Tenant JWT Middleware (`backend/api/middlewares/tenant_auth.py`)
- **`TenantAuthMiddleware`**: Intercepts every incoming HTTP request, inspects the `Authorization: Bearer <token>` header, decodes and verifies the JWT via `get_token_provider()`, and binds the extracted claims into the request-scoped `ContextVar` state defined in `backend/adapters/database/multi_tenant.py`:
  - `set_tenant_id(int(tenant_id))` -> `tenant_id_context`
  - `set_sucursal_id(int(branch_id))` -> `sucursal_id_context` (falls back to `tenant_id` if `branch_id` is omitted)
  - `set_user_id(int(user_id))` -> `user_id_context`
- If a token is missing, invalid, or expired during middleware execution, the middleware passes the request downstream so protected routes can reject it with `401 Unauthorized` via `get_current_user_claims`.

### 4. Authentication & Dependency Injection (`backend/api/dependencies/`)

#### `dependencies/__init__.py`
Provides singleton infrastructure adapters:
- `get_connection_provider()` -> `SQLAlchemyConnectionProvider`
- `get_token_provider()` -> `PyJWTTokenProvider` (configured with `SECRET_KEY`)
- `get_password_hasher()` -> `BcryptPasswordHasher`

#### `dependencies/auth.py`
- **`oauth2_scheme`**: `OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`.
- **`get_current_user_claims`**: Decodes and validates the Bearer JWT via `TokenProvider`, returning the verified claims dictionary or raising `HTTPException(401)`.
- **`RoleChecker(allowed_roles: List[str])`**: Callable FastAPI dependency that verifies `claims.get("role") in allowed_roles` or raises `HTTPException(403)`.

#### `dependencies/services.py`
Wires concrete SQLAlchemy repositories across the three database session factories (`get_articles_session_factory()`, `get_users_session_factory()`, `get_analytics_session_factory()`) into domain services:
- **Users & Auth (`db_users`)**: `get_auth_service()` -> `AuthService`, `get_user_service()` -> `UserService`.
- **Enterprises & Branches (`db_users`)**: `get_enterprise_service()` -> `EnterpriseService`, `get_branch_service()` -> `BranchService`.
- **Articles & Catalog (`db_articles` + `db_analytics`)**: `get_article_search_service()` -> `ArticleSearchService`, `get_article_catalog_orchestrator()` -> `ArticleCatalogOrchestrator`.
- **Stock, Audits & KPIs (`db_articles` + `db_analytics`)**: `get_stock_lookup_service()` -> `StockLookupService`, `get_audit_service()` -> `AuditService`, `get_stock_kpi_service()` -> `StockKPIService`.
- **Work Sessions (`db_analytics`)**: `get_work_session_service()` -> `WorkSessionService`.
- **Financial Reports (`db_analytics` + `db_articles`)**: `get_shrinkage_report_service()` -> `ShrinkageReportService`, `get_goods_received_report_service()` -> `GoodsReceivedReportService`, `get_daily_inventory_balance_repository()`, and `get_daily_inventory_balance_report_service()` -> `DailyInventoryBalanceReportService`.

---

## Versioned Routers (`backend/api/v1/`)

| Router File | Prefix | Endpoints | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| `health.py` | `/health`<br>`/api/v1/health` | `GET /health` | Executes `ConnectionProvider.check_connectivity()` (`SELECT 1`), returning `200 OK` (`healthy`) or `503 Service Unavailable` (`unhealthy`). |
| `auth.py` | `/api/v1/auth` | `POST /login` | Authenticates `LoginCredentials` via `AuthService.authenticate` and returns a signed `AuthToken` (`bearer`). |
| `articles.py` | `/api/v1/articles` | `GET /`<br>`GET /search`<br>`GET /{id_articulo}` | Ensures an active branch `WorkSession` exists, queries `ArticleSearchService` or `ArticleCatalogOrchestrator`, and serializes responses via `ArticuloAdminOut` (admin) or `ArticuloPublicOut` (non-admin). |
| `stock.py` | `/api/v1/stock` | `POST /audit`<br>`POST /audit/batch`<br>`GET /position`<br>`GET /kpis` | Enforces `RoleChecker(["administrador", "supervisor", "auditor"])`. Registers single/batch audits via `AuditService`, looks up deposit stock positions (`ArticleStockPositionAdminOut` vs. `ArticleStockPositionPublicOut`), and serves real-time session KPIs via `StockKPIService` (`DashboardKPIsResponse` vs. `DashboardKPIsPublicOut`). |
| `users.py` | `/api/v1/users` | `GET /`<br>`PATCH /{user_id}/status`<br>`PUT /{user_id}/roles` | Enforces `RoleChecker(["administrador"])`. Lists tenant users (`include_inactive`), toggles active status, and assigns roles via `UserService` (enforcing self-deactivation and self-demotion guards). |
| `reports.py` | `/api/v1/reports` | `GET /shrinkage`<br>`GET /goods-received`<br>`GET /inventory-balance` | Enforces `RoleChecker(["administrador"])`. Validates date ranges (`start_date <= end_date`) and delegates financial report generation to `ShrinkageReportService`, `GoodsReceivedReportService`, and `DailyInventoryBalanceReportService`. |
| `enterprises.py` | `/api/v1/enterprises` | `GET /`, `GET /{tenant_id}`, `POST /`, `PUT /{tenant_id}`, `DELETE /{tenant_id}` | Exposes multi-tenant enterprise CRUD via `EnterpriseService`. |
| `branches.py` | `/api/v1/branches` | `GET /{branch_id}`, `GET /tenant/{tenant_id}`, `POST /`, `PUT /{branch_id}`, `DELETE /{branch_id}` | Exposes tenant branch CRUD via `BranchService`. |

---

## Strict Layer Boundaries (What Must Never Live in `backend/api/`)

1. **No Business Logic or Tax/Delta Calculations**: Routers act strictly as HTTP coordinators. VAT classification (`VatClassifier`), stock discrepancy math (`DeltaCalculator`), and report aggregations must reside in `backend/app/`.
2. **No Direct SQL or ORM Queries**: Routers must never instantiate SQLAlchemy sessions or execute `select()` / `insert()` statements directly. All persistence is delegated through injected domain services and repository ports.
3. **No Raw ORM Model Serialization**: Endpoints must never return SQLAlchemy declarative instances directly. All responses are validated and serialized through explicit Pydantic V2 schemas.
4. **Structural Financial Privacy (`pcio_com_siva` & Valorized KPIs)**:
   - Under no circumstances may wholesale purchase costs (`pcio_com_siva`) or valorized discrepancy totals (`monto_valorizado_baja`, `monto_valorizado_alta`) be returned to `supervisor` or `auditor` roles.
   - Routers enforce structural RBAC by validating responses through separate Pydantic schemas based on the caller's verified JWT role (`ArticuloPublicOut` vs. `ArticuloAdminOut`, `ArticleStockPositionPublicOut` vs. `ArticleStockPositionAdminOut`, and `DashboardKPIsPublicOut` vs. `DashboardKPIsResponse`).
