# 📑 Backend Implementation Plan: Coverage of User Stories (US 1 to US 6)

This document defines the **requirements analysis, gap diagnosis, and phased roadmap for the Backend**, incorporating the business confirmations for the **SaaSStockDepositControl** platform.

---

## 1. Project Analysis and Current State

### 1.1 Repository Structure
```
SaaSStockDepositControl/
├── backend/                  # FastAPI REST API + SQLAlchemy 2.0 Async + MySQL (Hexagonal Architecture)
├── frontend-web/             # Web Management Panel (Next.js 14+ / React)
├── frontend-mobile/          # Field Audit Mobile App (React Native / Expo)
├── docs/                     # Functional specs and plans (SSoT)
└── .agents/                  # AI agent rules and skills
```

### 1.2 Current Backend State (`/backend`)
At present, the backend has the **base infrastructure** and a **Hexagonal Architecture** design:
* **`adapters/repositories/models.py`**: SQLAlchemy ORM models (`Usuario`, `Familia`, `Grupo`, `Marca`, `Articulo`, `StockPorDeposito`, `LotePorDeposito`, `AuditoriaRegistro`).
* **`app/`**: Domain split into modules (`articles`, `movements`, `users`, `ports`).
  * `articles/models.py` and `movements/models.py`: Base Pydantic schemas.
  * `ports/database.py` and `ports/security.py`: Abstract connection and identity interfaces.
* **`api/`**: FastAPI server.
  * `api/v1/auth.py`: Dummy JWT skeleton authentication.
  * `api/v1/health.py`: System health probe.
* **Database**: Alembic scripts for initial migrations (`migrations/`).

---

## 2. Business Definitions and Confirmed Clarifications

Based on the clarifications provided for the User Stories:

1. **Financial Valuation (US 6)**:
   * It is confirmed that **only the purchase cost (`pcio_com_siva`) is used**.
   * The commercial sale price does not exist in the source systems and is not calculated.
   * The "Profit and Loss" report measures the **financial valuation of Increases (inventory gains/surpluses)** against **Decreases (inventory losses/shrinkage)**.
2. **Barcode vs. Identifier (US 1 and US 2)**:
   * The exact relationship between the scanned barcode and `id_articulo` is still **pending definition/confirmation**.
   * The backend should be designed modularly (with a search abstraction layer), using `id_articulo` for now as the key identifier, and prepared to support direct lookup by an alias field or mapping table if needed later.
3. **Parameterized VAT Rate**:
   * The VAT rate **must not be hardcoded**. It must be received as a **transaction-configurable parameter** (with a default fallback of 21% if not specified), since it may vary over time or by receipt type.
   * The "Medicamentos" family is always **exempt (0% VAT)**.

---

## 3. Backend Gap Matrix by User Story

| User Story | Functional Requirement | Current State | Backend Gap |
| :--- | :--- | :--- | :--- |
| **US 1 & 2** | Barcode scanning and manual item registration. | ORM and Pydantic models for `Articulo` are defined. | • `GET /api/v1/articulos/scan/{code}` and `GET /api/v1/articulos/{id_articulo}` endpoints.<br>• An abstracted query repository that returns product details together with theoretical stock and audit status in the active branch/deposit. |
| **US 3 & 4** | Register quantity in increases (surplus) and decreases (missing/loss). | `auditorias_registro` and `stock_por_deposito` tables in DB. | • Domain service / repository to process an audit record (`ALTA`, `BAJA`, `SIN_ACCION`).<br>• Discrepancy calculation ($\Delta = \text{Real} - \text{Theoretical}$).<br>• **Fiscal Engine (`FiscalCalculator`)**: Calculation of `monto_valorizado` at purchase cost (`pcio_com_siva`) applying 0% VAT to Medicamentos and the transaction-supplied VAT rate (or 21% by default).<br>• `POST /api/v1/auditorias/registro` and `POST /api/v1/auditorias/sync` endpoints (offline batch). |
| **US 5** | Filter items (Name, Family, Brand, Audited Y/N). | DB models with relationships between `Articulo`, `Familia`, `Marca`, and `StockPorDeposito`. | • `GET /api/v1/articulos` endpoint with dynamic query params: `q`, `id_familia`, `id_marca`, `fue_auditado` (boolean), `id_deposito`, and pagination.<br>• Auxiliary endpoints: `GET /api/v1/familias` and `GET /api/v1/marcas`. |
| **US 6** | Query statistical profit and loss reports. | Mathematical definition in `docs/functional_specs.md`. | • Analytics and Financial Aggregation service.<br>• `GET /api/v1/reportes/balance` endpoint that aggregates totals for Increases ($), Decreases ($), and Net Balance ($), valued strictly at purchase cost (`pcio_com_siva` + parameterized VAT). |
| **Cross-cutting** | Multi-Tenancy & Real Authentication. | Multi-tenancy in models; dummy auth in `auth.py`. | • Real Users repository and service connected to the `usuarios` table.<br>• Automatic injection of `tenant_id`, `id_sucursal`, and `id_usuario` through the JWT token in all queries. |
| **Cross-cutting** | Simulation Data (Seeding). | No bulk test data loading script. | • `seed.py` script to populate 500 articles, deposits, lots with expiry dates, and fiscal families to validate the user stories and test protocols. |

---

## 4. Phased Roadmap (Backend Development Roadmap)

### Stage 1: Real Authentication, Multi-Tenant Context, and Seeding
1. **UserRepository & AuthService**: Replace dummy authentication in `api/v1/auth.py` by connecting to the `usuarios` table (with secure `passlib/bcrypt` password hashing).
2. **Context Dependencies**: Extract `tenant_id`, `id_usuario`, `rol`, and `id_sucursal` from the JWT token across all routes.
3. **Seeding Script (`scripts/seed.py`)**: Generate 500 articles, families (including "Medicamentos"), brands, deposits, theoretical/real stock, and lots with expiration dates according to section 5 of `functional_specs.md`.

### Stage 2: Articles Module, Search, and Filters (US 1, US 2, and US 5)
1. **ArticleRepository & ArticleService**:
   * Implement `get_by_id_or_barcode(tenant_id, id_articulo, id_deposito)`.
   * Implement `search_articles(tenant_id, id_deposito, query, id_familia, id_marca, fue_auditado, page, page_size)`.
2. **Article REST Endpoints (`api/v1/articulos.py`)**:
   * `GET /api/v1/articulos/scan/{code}`: Response optimized for the mobile app in <1 second.
   * `GET /api/v1/articulos/{id_articulo}`: Direct query for manual registration.
   * `GET /api/v1/articulos`: Paginated listing with dynamic filter support (US 5).
3. **Master Data Endpoints (`api/v1/familias.py`, `api/v1/marcas.py`)**:
   * `GET /api/v1/familias` and `GET /api/v1/marcas` to populate selectors in the web/mobile frontend.

### Stage 3: Movements Module, Audit Registration, and Fiscal Engine (US 3 and US 4)
1. **Parameterized Fiscal Engine (`FiscalCalculator`)**:
   * Total unit cost calculation from purchase cost:
     $$\text{Total Unit Cost} = \begin{cases} \text{pcio\_com\_siva} & \text{if Family = "Medicamentos"} \\ \text{pcio\_com\_siva} \times (1 + \text{VAT Rate}) & \text{for other families} \end{cases}$$
   * `VAT_Rate` is configurable per transaction (with a default fallback of 21%). Strict use of `decimal.Decimal`.
2. **AuditRepository & AuditService**:
   * Update `StockPorDeposito` (`stock_real`, `fue_auditado = True`, `fecha_hora_auditacion`).
   * Insert a row in `AuditoriaRegistro` (`tipo_accion`, `cantidad_afectada`, `monto_valorizado`).
3. **Movement Endpoints (`api/v1/auditorias.py`)**:
   * `POST /api/v1/auditorias/registro`: Real-time unit registration.
   * `POST /api/v1/auditorias/sync`: Batch synchronization for mass/offline loads processed in the mobile app.

### Stage 4: Statistical Reports and Analytics Module (US 6)
1. **Analytics Engine & ReportsRepository**:
   * Aggregated query of `auditorias_registro` filtered by `tenant_id`, `id_sucursal`, `id_deposito`, and date range.
   * Calculation of `total_inflow_cost` (valued Increases), `total_loss_cost` (valued Decreases), and `net_inventory_movement` ($).
   * Aggregation by Family, Brand, and audit status (% audited vs pending).
2. **Reports Endpoints (`api/v1/reportes.py`)**:
   * `GET /api/v1/reportes/balance`: Overall totals and financial balance at purchase cost.
   * `GET /api/v1/reportes/discrepancias`: Details of items with the largest shortages/surpluses.
   * `GET /api/v1/reportes/vencimientos`: FEFO traffic-light alert report (30, 60, 90 days).

---

## 5. Verification Plan and Quality Tests

* **Automated Tests (`pytest`)**:
  * Parameterized fiscal engine test (verifying exact calculation with `decimal.Decimal` for Medicamentos at 0% and configurable VAT).
  * Multi-tenant isolation test (Protocol C).
  * REST endpoint integration tests with an `httpx` async client.
* **E2E Acceptance Tests**:
  * Run `scripts/seed.py` to load 500 test articles.
  * Verify financial balance reconciliation in reports with no floating-point rounding differences (Protocol B).
