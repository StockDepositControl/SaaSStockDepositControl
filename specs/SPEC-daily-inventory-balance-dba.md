# Spec: Daily Inventory Balance Report - DBA Agent Task & Verification Specification

## Objective

This specification details the database data modeling, schema migration, indexing optimization, seeding update, and schema test verification tasks that the **DBA Agent** (`dba_agent`) must perform to enable **Balance Diario de Inventario (Daily Inventory Cost Ledger)**.

The Daily Inventory Balance report provides an executive daily closing summary for management, contrasting the total financial investment received via stock additions/goods received against the capital lost to warehouse shrinkage/removals, consolidated by tenant, branch (`branch_id`), and audit date (`report_date`).

---

## Tech Stack

- **Database Engine**: MariaDB 10.6+ / MySQL 8.0+ (SQLite in local testing mode)
- **ORM Layer**: SQLAlchemy 2.0 (Declarative Mapping using `Mapped` and `mapped_column`)
- **Schema Migration**: Alembic (`backend/migrations/alembic_analytics.ini`)
- **Testing Framework**: Pytest (`backend/tests/db/`)
- **Runtime Environment**: Python 3.11+

---

## Commands

Execute the following verification and database management commands within the `/backend` directory context:

```bash
# Apply pending database migrations to the analytics database
alembic -c migrations/alembic_analytics.ini upgrade head

# Test migration rollback stability (Downgrade & Re-upgrade)
alembic -c migrations/alembic_analytics.ini downgrade -1
alembic -c migrations/alembic_analytics.ini upgrade head

# Execute DB schema integrity and multi-tenant isolation tests
pytest tests/db/ -v

# Run mock data seeding script to generate test audit records and daily reports
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

## Data Schema & Indexing Requirements for Daily Inventory Balance

### 1. ORM Model Extension: `DailyReport` (`daily_reports` table)
The DBA Agent must update the `DailyReport` ORM model in `backend/adapters/repositories/models/analytics.py` to support branch-level aggregation and net patrimonial calculation:

| Field Name | Type | Constraint / Default | Purpose in Daily Inventory Balance |
|---|---|---|---|
| `daily_report_id` | `BigInteger` | Primary Key, Autoincrement | Unique report summary record identifier |
| `tenant_id` | `Integer` | Foreign Key (`record_tenants.tenant_id`), Non-nullable | Multi-tenant isolation leading filter |
| `branch_id` | `Integer` | Non-nullable, Default `1` | Branch level consolidation (`sucursal`) |
| `report_date` | `Date` | Non-nullable | Audit consolidation date |
| `total_audit_articles` | `Integer` | Non-nullable | Total unique SKUs/articles audited |
| `total_processed_units` | `Integer` | Non-nullable, Default `0` | Total physical units processed (`Altas + Mermas`) |
| `total_addition_amount` | `Integer` | Non-nullable | Physical units added (`Altas`) |
| `total_shrinkage_amount` | `Integer` | Non-nullable | Physical units lost (`Mermas`) |
| `total_addition_value` | `Numeric(15,4)`| Non-nullable | Financial capital injected ($) |
| `total_shrinkage_value` | `Numeric(15,4)`| Non-nullable | Financial capital lost ($) |
| `net_patrimonial_variation`| `Numeric(15,4)`| Non-nullable, Default `0.0000` | Net stock value variation ($\Delta = \text{Altas} - \text{Mermas}$) |
| `created_at` | `DateTime` | Non-nullable, UTC default | Record creation timestamp |
| `updated_at` | `DateTime` | Non-nullable, UTC default/onupdate | Record update timestamp |

### 2. Composite Index Requirement
Update the unique index on `daily_reports`:
- Replace `idx_daily_reports_tenant_date` on `(tenant_id, report_date)` with **`idx_daily_reports_tenant_branch_date`** on `(tenant_id, branch_id, report_date)` (Unique Index) to enforce branch-level daily consolidation uniqueness.

### 3. `audit_records` Support Verification
Ensure the source `audit_records` table retains valid indexes for dynamic aggregation fallbacks:
- `idx_audit_tenant_scan`: Composite index on `(tenant_id, scan_timestamp)`
- `idx_audit_goods_received`: Composite index on `(tenant_id, action_type, scan_timestamp)`
- `idx_audit_shrinkage`: Composite index on `(tenant_id, action_type, scan_timestamp)`

---

## Migration Plan & Alembic Script

1. **Alembic Revision**: Create a new revision script in `backend/migrations/versions/` (or via `alembic_analytics.ini`).
2. **Schema Upgrade**:
   - Add `branch_id` column (`Integer`, non-nullable, server_default='1').
   - Add `total_processed_units` column (`Integer`, non-nullable, server_default='0').
   - Add `net_patrimonial_variation` column (`DECIMAL(15,4)`, non-nullable, server_default='0.0000').
   - Drop old index `idx_daily_reports_tenant_date` if present.
   - Create unique index `idx_daily_reports_tenant_branch_date` on `(tenant_id, branch_id, report_date)`.
3. **Downgrade Method**:
   - Implement reversible `downgrade()` block dropping new columns and restoring `idx_daily_reports_tenant_date`.

---

## Seeding Script Specification (`backend/scripts/seed.py`)

Update `seed.py` to seed parametric mock data for `DailyReport` records across multiple branches and dates:
- Generate daily balance records for active branches (`branch_id` 1, 2, etc.).
- Ensure mathematical coherence across seeded records:
  $$\text{total\_processed\_units} = \text{total\_addition\_amount} + \text{total\_shrinkage\_amount}$$
  $$\text{net\_patrimonial\_variation} = \text{total\_addition\_value} - \text{total\_shrinkage\_value}$$

---

## Code Style & Conventions

- **SQLAlchemy 2.0**: All models MUST use modern declarative mapping style with `Mapped[T]` and `mapped_column()`.
- **Decimal Precision**: Financial fields MUST use `DECIMAL(15, 4)` via `SQLDecimal(15, 4)` to eliminate floating-point precision loss.
- **Client Database Immutability**: Tables in `db_articles` (`articulos`, `familias`, etc.) remain strictly immutable.

---

## Testing Strategy & Assertions

Create `backend/tests/db/test_daily_inventory_balance_schema.py` to run schema checks:

1. **Table Metadata Integrity**: Assert `daily_reports` has columns `branch_id`, `total_processed_units`, and `net_patrimonial_variation`.
2. **Unique Composite Index**: Assert index `idx_daily_reports_tenant_branch_date` exists on `(tenant_id, branch_id, report_date)` with `unique=True`.
3. **Foreign Keys & Cascade**: Assert `RecordTenant.daily_reports` cascade rules are preserved.
4. **Client DB Protection**: Assert no migration alters `BaseArticles` tables.

---

## Boundaries & Guardrails

- **Always do**:
  - Run database tests (`pytest tests/db/`) before marking work completed.
  - Write explicit, tested `upgrade()` and `downgrade()` methods in Alembic.
  - Ensure `tenant_id` is the leading column in all multi-tenant composite indexes.
- **Ask first**:
  - Modifying existing columns or data types in `audit_records`.
- **Never do**:
  - Edit any `*_repository.py` files under `backend/adapters/repositories/`.
  - Introduce SQL definitions or ORM imports in `backend/app/`.
  - Alter or drop any legacy client tables in `db_articles`.

---

## Success Criteria

- [ ] `DailyReport` model in `backend/adapters/repositories/models/analytics.py` updated with `branch_id`, `total_processed_units`, and `net_patrimonial_variation`.
- [ ] Unique index `idx_daily_reports_tenant_branch_date` on `(tenant_id, branch_id, report_date)` created and verified in ORM metadata.
- [ ] Alembic migration script created with bidirectional `upgrade()` and `downgrade()` support.
- [ ] `pytest tests/db/test_daily_inventory_balance_schema.py` passes 100%.
- [ ] `scripts/seed.py` successfully populates coherent branch-level `DailyReport` mock records.
- [ ] Migration downgrade/upgrade check (`alembic downgrade -1 && alembic upgrade head`) executes without error.
