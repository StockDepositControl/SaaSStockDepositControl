# TASK: Implement US-06 (DBA) — Database Schema Updates, Alembic Migrations & Data Seeding

> **IMPORTANT DIRECTIVE FOR AI AGENTS**: Before planning or executing any database schema or seeding changes for this task, you MUST read and cross-reference `docs/functional_specs.md` (specifically Sections 3.1, 4.1, 5.2, and 6.2). `functional_specs.md` is the Single Source of Truth (SSoT) for financial rules, VAT calculations, and domain requirements.

---

## 1. Context & Objectives

Following the implementation of our security foundation (US-05), we need a robust, realistic data ecosystem to thoroughly validate multi-tenancy boundaries (`tenant_id`, `id_sucursal`), Role-Based Access Control (RBAC) rules, and accurate stock valuation at purchase cost.

Your task as the **DBA Agent** is to prepare the database schema and implement a smart, parameter-driven data seeding script for **Global Medica (Phase 1)** using the `Faker` library.

The database and seeding script must support:
1. **Security & Authentication**: Generate users assigned to proper roles (`administrador`, `supervisor`, `auditor`) and branches (`id_sucursal`) to validate logical isolation. Seed `is_active` flags for user status checks.
2. **Fiscal & Cost Engine Integration**: Seed product families and inventory items adhering strictly to the purchase cost model (`pcio_com_siva`) and dynamic family-based VAT logic.
3. **Data Degradation & Edge Cases**: Inject specific inventory anomalies (theoretical vs. real stock mismatches, expired batches) to stress-test downstream analytical reports.

---

## 2. Technical Constraints & Business Guardrails

You must strictly adhere to the following guardrails during implementation:

* **Ownership Boundaries**: You own and operate strictly within:
  * `backend/migrations/` (Alembic migration scripts)
  * `backend/scripts/` (Seeding scripts, e.g., `seed.py`)
  * `backend/tests/db/` (Schema integrity and isolation tests)
  * `backend/adapters/repositories/models.py` (SQLAlchemy Declarative Models)
  * **PROHIBITED**: You must never create or edit any files in `backend/app/` or `backend/api/`.
* **Single Source of Truth (SSoT)**: All domain rules regarding cost valuation and taxation must match `docs/functional_specs.md`.
* **Cost-Only Pricing Model**: The system strictly operates on purchase cost prices (`pcio_com_siva`). **Do NOT seed, calculate, or expose sales prices (`pcio_venta`) or profit margin metrics.**
* **Financial Precision (`decimal.Decimal`)**: Absolutely no `float` primitive types are allowed for monetary or financial values. All price, cost, and VAT percentage values generated via `Faker` must be explicitly converted to `decimal.Decimal`.
* **Database Target**: MariaDB. The script must use SQLAlchemy declarative constructs compatible with MariaDB. Do not write PostgreSQL-specific syntax.
* **Determinism & Reproducibility**: The seeding script must accept an optional `--seed` integer parameter for the `Faker` generator to produce identical datasets across testing cycles.

---

## 3. Explicit Acceptance Criteria to Implement

### A. Database Schema Updates
In [models.py](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/adapters/repositories/models.py):
* **Usuario Model**: Add `is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)`.
* **StockPorDeposito Model**: Add `stock_teorico: Mapped[int] = mapped_column(Integer, default=0, nullable=False)`.

### B. Alembic Migrations
* Generate a new reversible Alembic migration under `backend/migrations/versions/` reflecting the new columns.
* Ensure a fully functioning `downgrade()` block is implemented.

### C. Parameterized Seeding Engine Configuration
* Implement the CLI seeding script in `backend/scripts/seed.py`.
* Support CLI arguments via `argparse` allowing execution such as:
  `python backend/scripts/seed.py --count 500 --seed 42`
* Evenly distribute 500 generated articles across multiple warehouses (`depósitos`) and branches (`sucursales`).
* Ensure all user passwords seeded are hashed properly to allow authentication.

### D. Product Families & Dynamic Fiscal Rules (VAT / IVA)
Seed product classifications and items adhering strictly to Section 3.1 of `docs/functional_specs.md`:
1. **Family "Medicamentos"**: Exempt / 0% VAT.
2. **Alternative Families (Perfumería, Cosmética, Accesorios, etc.)**: Taxable with configurable/manual VAT rate (Default 21% / `Decimal('0.21')`, but also seed edge cases with 10.5% / `Decimal('0.105')`).

### E. Analytical Edge Cases & Data Anomaly Injection
* **Inventory Anomaly (Ghost Items)**: Inject a distinct subset of articles featuring a positive theoretical stock (`stock_teorico > 0`) but a real physical stock of exactly zero (`stock_real == 0`).
* **Batch Expiration Stress**: Generate expired inventory lots (`LotePorDeposito` records with `vencimiento` in the past) distributed unevenly across warehouses.

---

## 4. Required Execution Workflow

To successfully resolve this story, you must perform the following steps:

1. **Verify Current State**: Inspect `backend/adapters/repositories/models.py` and query Alembic configuration.
2. **Update Models**: Modify `backend/adapters/repositories/models.py` to add `is_active` to `Usuario` and `stock_teorico` to `StockPorDeposito`.
3. **Generate & Test Migrations**:
   * Generate migration script: `alembic revision --autogenerate -m "add_user_is_active_and_stock_teorico"`
   * Verify upgrade and downgrade commands:
     `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`
4. **Implement Seeder**: Code the seeder at `backend/scripts/seed.py` mapping columns cleanly.
5. **DB Integrity Tests**: Write database schema-level and constraints integrity tests inside `backend/tests/db/`.
6. **Verify Seeding Execution**: Run the seeding command:
   `python backend/scripts/seed.py --count 500 --seed 42`