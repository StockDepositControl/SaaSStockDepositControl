# Spec: Goods Received Report - DBA Agent Task & Verification Specification

## Objective

This specification details the database data modeling, indexing optimization, integrity checks, and validation tasks that the **DBA Agent** (`dba_agent`) must perform to enable **Use Case 1: Administrator Generation of the Goods Received Report (Reporte de Valorización de Ingresos y Altas)**.

The Goods Received Report allows administrative users to audit capital physically injected into warehouse shelves through purchase receipts, stock transfers, or supplier returns, for direct reconciliation against supplier delivery notes or invoices.

---

## Tech Stack

- **Database Engine**: MariaDB 10.6+ / MySQL 8.0+
- **ORM Layer**: SQLAlchemy 2.0 (Declarative Mapping using `Mapped` and `mapped_column`)
- **Schema Migration**: Alembic (`backend/migrations/alembic_analytics.ini`)
- **Testing Framework**: Pytest (`backend/tests/db/`)
- **Runtime Environment**: Python 3.11+

---

## Commands

Execute the following verification and management commands within the `/backend` directory context:

```bash
# Apply pending database migrations to the analytics database
alembic -c migrations/alembic_analytics.ini upgrade head

# Test migration rollback stability (Downgrade & Re-upgrade)
alembic -c migrations/alembic_analytics.ini downgrade -1
alembic -c migrations/alembic_analytics.ini upgrade head

# Execute DB schema integrity and multi-tenant isolation tests
pytest tests/db/ -v

# Run mock data seeding script to generate test audit records
python scripts/seed.py
```

---

## Project Structure & Ownership Boundaries

```
backend/
├── adapters/
│   └── repositories/
│       └── models/                → [DBA OWNED] ORM Models (analytics.py, articles.py, users.py)
├── migrations/                    → [DBA OWNED] Alembic migration scripts and config
├── scripts/                       → [DBA OWNED] Data seeding scripts (seed.py)
└── tests/
    └── db/                        → [DBA OWNED] Schema integrity and multi-tenant tests
```

### Strict DBA Boundaries:
- **OWNED PATHS**: `backend/adapters/repositories/models/*`, `backend/migrations/*`, `backend/scripts/*`, `backend/tests/db/*`.
- **PROHIBITED PATHS**: The DBA agent MUST NEVER create or modify repository implementation files (`*_repository.py` inside `backend/adapters/repositories/`), domain models/services (`backend/app/*`), or API endpoints (`backend/api/*`).

---

## Data Schema & Indexing Requirements for Use Case 1

### 1. `audit_records` Analytics Schema Verification
The `audit_records` table in `db_analytics` stores stock movement logs. The DBA Agent must verify that `AuditRecord` ORM model in `backend/adapters/repositories/models/analytics.py` satisfies:

| Field Name | Type | Constraint / Default | Purpose in Goods Received Report |
|---|---|---|---|
| `audit_id` | `BigInteger` | Primary Key, Autoincrement | Unique audit movement identifier |
| `tenant_id` | `Integer` | Foreign Key (`record_tenants.tenant_id`), Non-nullable | Multi-tenant isolation leading filter |
| `session_id` | `BigInteger` | Foreign Key (`work_sessions.session_id`), Non-nullable | Audit work session tracking |
| `branch_id` | `Integer` | Non-nullable | Branch level filtering |
| `warehouse_id` | `Integer` | Nullable | Specific warehouse location |
| `article_code` | `String(100)` | Non-nullable | Foreign identifier joining `articulos.id_articulo` |
| `user_id` | `Integer` | Non-nullable | Operator who executed the reception |
| `action_type` | `String(50)` | Non-nullable | Movement classification (`ADDITION`, `Alta`, `Ingreso`) |
| `affected_amount` | `Integer` | Non-nullable | Physical units added to stock ($\ge 0$) |
| `applied_unit_cost`| `Numeric(15,4)`| Non-nullable | Purchase unit cost excl. VAT (`pcio_com_siva`) |
| `applied_vat_rate` | `Numeric(5,4)` | Non-nullable | Applied VAT percentage (e.g., 0.21, 0.105, 0.0) |
| `valorized_amount` | `Numeric(15,4)`| Non-nullable | Calculated gross capital injected ($) |
| `scan_timestamp` | `DateTime` | Non-nullable | Date range filter (`start_date` to `end_date`) |
| `observation` | `String(255)` | Nullable | Operational reason (e.g. "Ingreso mercadería", "Ajuste por sobrante") |

### 2. Composite Index Verification
The DBA Agent must ensure that query performance for Goods Received auditing is optimized using composite indexes:
- `idx_audit_goods_received`: Composite index on `(tenant_id, action_type, scan_timestamp)` to guarantee immediate lookup of `ADDITION`/`Alta` records by tenant and date range.
- `idx_audit_article`: Index on `(article_code)` to optimize JOINs against `articulos`.

---

## Code Style & Conventions

- **SQLAlchemy 2.0**: All models MUST use modern declarative mapping style with `Mapped[T]` and `mapped_column()`.
- **Decimal Precision**: Financial fields MUST use `DECIMAL(15, 4)` via `SQLDecimal(15, 4)` to avoid floating-point rounding discrepancies in financial auditing.
- **Client Database Immutability**: Legacy tables (`articulos`, `familias`, `grupos`, `marcas`, `codigos_barra_articulo`) inside `db_articles` are strictly immutable. No Alembic migrations or schema modifications are allowed against `db_articles`.

---

## Testing Strategy & Assertions

The DBA Agent must create/update `backend/tests/db/test_goods_received_schema.py` to run automated schema checks verifying:

1. **Table Metadata Integrity**: Confirm `audit_records` table exists with all required columns.
2. **Multi-Tenant Isolation Constraint**: Verify `tenant_id` is present and indexed as the leading column on `idx_audit_goods_received`.
3. **Cascade Rules**: Confirm explicit cascade rules on `RecordTenant.audit_records` and `WorkSession.audit_records`.
4. **Client Database Immutability**: Assert no schema migration scripts alter tables in `BaseArticles`.

---

## Boundaries & Guardrails

- **Always do**:
  - Run database tests (`pytest tests/db/`) before declaring tasks complete.
  - Include both `upgrade()` and `downgrade()` in Alembic scripts.
  - Verify composite indexes start with `tenant_id`.
- **Ask first**:
  - Adding new fields to `audit_records` or modifying session relationships.
- **Never do**:
  - Edit any `*_repository.py` files under `backend/adapters/repositories/`.
  - Execute or define raw SQL string queries in models or repositories.
  - Alter, rename, or drop columns in `articulos` or `codigos_barra_articulo`.

---

## Success Criteria

1. [ ] `AuditRecord` model in `backend/adapters/repositories/models/analytics.py` fully supports filtering by `action_type` in `('ADDITION', 'Alta', 'Ingreso')`.
2. [ ] Index `idx_audit_goods_received` on `(tenant_id, action_type, scan_timestamp)` is declared and verified in ORM metadata.
3. [ ] Database schema test suite `backend/tests/db/test_goods_received_schema.py` passes 100%.
4. [ ] `scripts/seed.py` successfully injects realistic Goods Received (`ADDITION`) audit records with valid purchase costs, VAT rates, and operational observations.
5. [ ] Migration downgrade test (`alembic downgrade -1 && alembic upgrade head`) executes cleanly without error.
