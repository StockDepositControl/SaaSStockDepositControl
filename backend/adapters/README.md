# 💾 Secondary Adapter Layer (`backend/adapters/`)

This layer contains the **Secondary (Driven) Adapters** of the application. It provides the concrete infrastructure implementations that satisfy the abstract ports declared in `backend/app/*/ports.py` and `backend/app/ports/`, including **SQLAlchemy 2.0 Async** database connection factories, request-scoped multi-tenant `ContextVar` primitives, repository implementations, declarative ORM models across the three database schemas, and JWT/Bcrypt security providers.

---

## Directory Structure

```text
backend/adapters/
├── __init__.py
├── database/
│   ├── __init__.py
│   ├── connection.py               # SQLAlchemyDatabaseSession, SQLAlchemyConnectionProvider,
│   │                               # and session factories for db_articles, db_users, db_analytics
│   └── multi_tenant.py             # Request-scoped ContextVar primitives & getters/setters
├── security/
│   ├── __init__.py
│   ├── jwt_provider.py             # PyJWTTokenProvider (implements TokenProvider)
│   └── password_hasher.py          # BcryptPasswordHasher (implements PasswordHasher)
└── repositories/
    ├── __init__.py
    ├── article_repository.py       # SQLAlchemyArticleRepository
    ├── stock_repository.py         # SQLAlchemyStockRepository
    ├── audit_repository.py         # SQLAlchemyAuditRepository
    ├── user_repository.py          # SQLAlchemyUserRepository
    ├── branch_repository.py        # SQLAlchemyBranchRepository
    ├── enterprise_repository.py    # SQLAlchemyEnterpriseRepository
    ├── work_session_repository.py  # SQLAlchemyWorkSessionRepository
    ├── report_repository.py        # SQLAlchemyShrinkageReportRepository,
    │                               # SQLAlchemyGoodsReceivedReportRepository,
    │                               # SQLAlchemyDailyInventoryBalanceReportRepository
    └── models/
        ├── __init__.py             # Re-exports all declarative bases and ORM models
        ├── articles.py             # BaseArticles (db_articles ORM models)
        ├── users.py                # BaseUsers (db_users ORM models)
        └── analytics.py            # BaseAnalytics (db_analytics ORM models)
```

---

## Detailed Adapter Breakdown

### 1. Database Infrastructure (`backend/adapters/database/`)

#### `connection.py`
Implements the cross-cutting database ports defined in `backend/app/ports/database.py` and manages connection pooling across the three databases:
- **`SQLAlchemyDatabaseSession`**: Wraps `sqlalchemy.ext.asyncio.AsyncSession` to satisfy the `DatabaseSession` port (`commit()`, `rollback()`, `raw_session`).
- **`SQLAlchemyConnectionProvider`**: Implements `ConnectionProvider` (`session()`, `check_connectivity()`, `dispose()`). Executes a lightweight `SELECT 1` probe for `/health` and `/api/v1/health` checks and cleanly disposes all active engines during FastAPI lifespan shutdown.
- **Multi-Database Session Factories**: Lazily initializes and caches singleton `async_sessionmaker[AsyncSession]` instances (with `pool_pre_ping=True` and `expire_on_commit=False`) for each isolated schema:
  - `get_articles_session_factory()` -> `db_articles` (`ARTICLES_DATABASE_URL` / `DB_NAME_ARTICLES`)
  - `get_users_session_factory()` -> `db_users` (`USERS_DATABASE_URL` / `DB_NAME_USERS`)
  - `get_analytics_session_factory()` -> `db_analytics` (`ANALYTICS_DATABASE_URL` / `DB_NAME_ANALYTICS`)

#### `multi_tenant.py` (vs. `backend/api/middlewares/tenant_auth.py`)
Defines the async-safe `contextvars.ContextVar` primitives and accessor functions used by repositories to enforce request-scoped tenant and branch isolation:
- **ContextVar Primitives**:
  - `tenant_id_context: ContextVar[Optional[int]]`
  - `sucursal_id_context: ContextVar[Optional[int]]`
  - `user_id_context: ContextVar[Optional[int]]`
- **Getters & Setters**:
  - `get_tenant_id()` / `set_tenant_id(tenant_id)`
  - `get_sucursal_id()` / `set_sucursal_id(sucursal_id)`
  - `get_user_id()` / `set_user_id(user_id)`
- **Separation from HTTP Middleware**: `backend/adapters/database/multi_tenant.py` only holds the framework-agnostic `ContextVar` state and helpers. The HTTP middleware that extracts Bearer JWT claims on each incoming request and calls `set_tenant_id`, `set_sucursal_id`, and `set_user_id` lives in the primary adapter layer at **`backend/api/middlewares/tenant_auth.py`** (`TenantAuthMiddleware`).

---

### 2. Security Adapters (`backend/adapters/security/`)

Implements the contracts declared in `backend/app/ports/security.py`:
- **`jwt_provider.py` (`PyJWTTokenProvider`)**: Implements `TokenProvider` using `PyJWT` (`HS256` by default) to sign access tokens with expiration (`exp`) claims and decode/verify incoming Bearer tokens (raising `ValueError` on expired or invalid signatures).
- **`password_hasher.py` (`BcryptPasswordHasher`)**: Implements `PasswordHasher` using `bcrypt` (`gensalt()`, `hashpw()`, `checkpw()`) for salted password hashing and verification.

---

### 3. Repositories (`backend/adapters/repositories/`)

Each repository implements a domain port from `backend/app/*/ports.py`, translates between SQLAlchemy ORM rows and Pydantic V2 domain models, and binds to its target database session factory:

| File | Repository Class(es) | Implemented Port(s) | Target Database(s) |
| :--- | :--- | :--- | :--- |
| `article_repository.py` | `SQLAlchemyArticleRepository` | `ArticleRepositoryPort` | `db_articles` (catalog & barcode queries) + `db_analytics` (checks `AuditRecord` to compute `fue_auditado` per active session) |
| `stock_repository.py` | `SQLAlchemyStockRepository` | `StockRepositoryPort` | `db_articles` (**strictly read-only** queries on `stock_por_deposito` and `articulos` count/out-of-stock metrics) |
| `audit_repository.py` | `SQLAlchemyAuditRepository` | `AuditRepositoryPort` | `db_analytics` (persists `AuditRecord`, checks `client_uuid` idempotency, resolves latest session audits, and computes SQL-level `SessionAuditAggregates`) |
| `user_repository.py` | `SQLAlchemyUserRepository` | `UserRepositoryPort` | `db_users` (tenant-isolated user lookups, password hash retrieval, status updates, and `user_roles` synchronization) |
| `branch_repository.py` | `SQLAlchemyBranchRepository` | `BranchRepositoryPort` | `db_users` (`branches` table CRUD) |
| `enterprise_repository.py` | `SQLAlchemyEnterpriseRepository` | `EnterpriseRepositoryPort` | `db_users` (`enterprises` table CRUD) |
| `work_session_repository.py` | `SQLAlchemyWorkSessionRepository` | `WorkSessionRepositoryPort` | `db_analytics` (`work_sessions` lookup and creation) |
| `report_repository.py` | `SQLAlchemyShrinkageReportRepository`<br>`SQLAlchemyGoodsReceivedReportRepository`<br>`SQLAlchemyDailyInventoryBalanceReportRepository` | `ShrinkageReportRepositoryPort`<br>`GoodsReceivedReportRepositoryPort`<br>`DailyInventoryBalanceReportRepositoryPort` | `db_analytics` (queries `audit_records` for removals/additions and `daily_reports` with dynamic fallback aggregation from `audit_records`) |

---

### 4. Declarative ORM Models (`backend/adapters/repositories/models/`)

Each database schema has its own isolated SQLAlchemy 2.0 `DeclarativeBase` so Alembic migrations and table metadata never collide across databases:

- **`models/articles.py` (`BaseArticles` — `db_articles`)**:
  - `Familia` (`familias`), `Grupo` (`grupos`), `Marca` (`marcas`), `Articulo` (`articulos` with `Numeric(15, 4)` `pcio_com_siva` and FULLTEXT index on `des_articulo`), `CodigoBarraArticulo` (`codigos_barra_articulo`), `StockPorDeposito` (`stock_por_deposito`), `LotePorDeposito` (`lotes_por_deposito`), `Empresa` (`empresas`), `Sucursal` (`sucursales`), `Deposito` (`depositos`).
- **`models/users.py` (`BaseUsers` — `db_users`)**:
  - `Enterprise` (`enterprises`), `Branch` (`branches`), `User` (`users` with unique `(tenant_id, email)` index and `is_active` flag), `Role` (`roles`), `UserRoleAssociation` (`user_roles`).
- **`models/analytics.py` (`BaseAnalytics` — `db_analytics`)**:
  - Enums: `ActionType` (`ADDITION`, `REMOVAL`, `NO_ACTION`), `RiskLevel` (`RED`, `YELLOW`, `GREEN`), `SessionStatus` (`OPEN`, `CLOSED`).
  - Models: `RecordTenant` (`record_tenants`), `WorkSession` (`work_sessions`), `AuditRecord` (`audit_records`), `DailyReport` (`daily_reports`), `CriticalShrinkageAlert` (`critical_shrinkage_alerts`).

---

## Strict Architectural Rules

1. **Port Contract Fidelity**: Every repository must implement its corresponding `backend/app/*/ports.py` interface and return pure domain models (never leak SQLAlchemy ORM instances to `app/` or `api/`).
2. **Zero Business Logic in Repositories**: Tax classification (`VatClassifier`), stock discrepancy math (`DeltaCalculator`), and RBAC guards belong in `backend/app/`, not in SQL repositories.
3. **Read-Only Legacy Catalog (`db_articles`)**: Audit operations must never mutate `stock_por_deposito` or `articulos` in `db_articles`; all audit counts and stock adjustments are recorded immutably in `db_analytics.audit_records`.
4. **Tenant Isolation**: Queries against tenant-scoped tables must always filter by the active `tenant_id` (passed explicitly or resolved via `multi_tenant.py`).
