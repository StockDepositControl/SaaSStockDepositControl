# Phase 3: Technical Execution Plan (Approved)

## 1. Architecture & Schema Design
- **Usuario Model**: Add `is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)`
- **StockPorDeposito Model**: Add `stock_teorico: Mapped[int] = mapped_column(Integer, default=0, nullable=False)`

## 2. SQLAlchemy Declarative Models
- Edit `/home/fede/Proyectos/SaaSStockDepositControl/backend/adapters/repositories/models.py` to include the fields mentioned above.

## 3. Alembic Migration Code
- Execute Alembic revision autogeneration to create the migration schema.
- Validate `upgrade()` and `downgrade()` functionality locally.

## 4. Seeding Script (`seed.py`)
- **Scale**: Default 500 items, distributed across 5 deposits and 2 branches (`sucursales`).
- **Security Context**: Generate mock users spanning multiple `tenant_id` boundaries with roles. Passwords hashed using `BcryptPasswordHasher`.
- **Fiscal Mix**: 50% "Medicamentos" (0% VAT), 50% alternative taxable families. Prices generated as `decimal.Decimal` representing pure `pcio_com_siva`.
- **Data Anomalies Injection**:
  - **State A (Ghost Items)**: Subset of `StockPorDeposito` records with `stock_teorico > 0` and `stock_real = 0`.
  - **State B (Batch Expiration Stress)**: 25% of `LotePorDeposito` records allocated `vencimiento` dates placed historically in the past.
  - **State C (Fiscal Mix)**: Addressed by the 50/50 family split.

## 5. Schema Tests
- Write database schema integrity suite (`backend/tests/db/test_schema_integrity.py`) utilizing SQLAlchemy metadata reflection.

## 6. Reconciliation & Verification Guide
- Commands to execute:
  1. `cd backend && PYTHONPATH=.. venv/bin/alembic revision --autogenerate -m "add_user_is_active_and_stock_teorico"`
  2. `cd backend && PYTHONPATH=.. venv/bin/alembic upgrade head`
  3. `cd backend && PYTHONPATH=.. venv/bin/alembic downgrade -1`
  4. `cd backend && PYTHONPATH=.. venv/bin/alembic upgrade head`
  5. `PYTHONPATH=. backend/venv/bin/python backend/scripts/seed.py --count 500 --seed 42`
  6. `cd backend && PYTHONPATH=.. venv/bin/pytest tests/db/`
