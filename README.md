# 🏛️ SaaS Stock Deposit Control - Enterprise Platform

A state-of-the-art Software as a Service (SaaS) platform designed for high-precision warehouse audits, real-time inventory reconciliation, and intelligent shelf-life tracking. The platform bridges physical reality on the warehouse floor with accounting ledgers, computing immediate financial discrepancy valuations and sorting expiration risks via a strict FIFO/FEFO scheduling engine.

---

## 📖 Executive Summary

The **SaaS Stock Deposit Control** platform provides a robust, multi-tenant solution for businesses managing complex inventory across multiple deposits or warehouses. 

*   **Field Auditing:** Physical operators utilize the camera modules of mobile devices to perform **blind/semi-blind audits** of items, ensuring data accuracy by removing confirmation bias.
*   **Operational Sync:** An offline-first local database architecture queue synchronizes batch payloads automatically once connectivity is re-established.
*   **Analytical Governance:** Supervisors and managers use analytical dashboards to track the **Net Day Balance**, analyze tax-adjusted shrinkage values (VAT/IVA exception matrix), and visualize semaphoric expiration risk distributions across five warehouses.

---

## 🛠️ Architecture & Technology Stack

The platform is designed to scale from a single tenant (**Phase 1: Global Medica**) to a dynamic, database-per-tenant architecture (**Phase 2: Farmanor Network**).

```
                      +-----------------------------+
                      |       Primary Adapters      |
                      |   - FastAPI (Web API)       |
                      |   - Next.js (Dashboard)     |
                      |   - React Native (Mobile)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |         Domain Ports        |
                      |   - ConnectionProvider      |
                      |   - Repositories Interfaces |
                      +--------------+--------------+
                                     ^
                                     |
                      +--------------+--------------+
                      |      Secondary Adapters     |
                      |   - SQLAlchemy 2.0 Async    |
                      |   - MariaDB/MySQL Backend   |
                      +-----------------------------+
```

### Backend (Python Service)
*   **Paradigm:** Strict **Hexagonal Architecture (Ports and Adapters)**.
*   **Core Framework:** FastAPI (Asynchronous delivery layer running on Uvicorn).
*   **Database ORM:** SQLAlchemy 2.0 (Declarative mapping with fully async execution wrappers).
*   **Database Driver:** AIOMySQL (Asynchronous MySQL/MariaDB driver).
*   **Migration Engine:** Alembic (Relational database schema evolution management).

### Frontend Mobile (Auditor Client)
*   **Core Stack:** React Native, Expo, TypeScript.
*   **Styling:** NativeWind (Tailwind CSS for React Native).
*   **Persistence:** SQLite & WatermelonDB (Offline-first transactional engine with async batch synchronization queue).
*   **Scanning Engine:** Camera interface bound with auto-focus loops targeting EAN-13, QR, and DataMatrix symbologies.

### Frontend Web (Analytical Dashboard)
*   **Core Stack:** Next.js (App Router), React, TypeScript.
*   **Styling:** Tailwind CSS & Tremor (Optimized analytical visualization components).
*   **Features:** Role-Based Access Control (RBAC) with secure field-level masking for supervisors and auditors.

---

## 📁 Monorepo Map

```text
SaaSStockDepositControl/
├── docs/                           # Central Documentation
│   ├── architecture.md             # System Architecture, Database Schema, and RBAC
│   └── functional_specs.md         # Business Logic, FEFO engines, and Testing Protocols
├── backend/                        # FastAPI core backend service
│   ├── api/                        # Presentation Layer (FastAPI Routers, Middlewares, Deps)
│   │   ├── middlewares/            # JWT Token validation and context tenant binding
│   │   └── v1/                     # Versioned API routes (health, stock, articles)
│   ├── app/                        # Domain Core Layer (Business logic, ports, pure models)
│   │   ├── articles/               # Article Pydantic schemas and metadata catalogs
│   │   ├── movements/              # Inventory transaction ledger Pydantic models
│   │   └── ports/                  # Abstract port definitions (Database, clients)
│   ├── adapters/                   # Infrastructure Adapters (SQLAlchemy repositories)
│   │   └── database/               # Asynchronous connection pools and session states
│   ├── migrations/                 # Alembic schema versioning scripts
│   ├── scripts/                    # Parametric Faker seeding scripts
│   └── tests/                      # Pytest unit and integration suites
├── frontend-mobile/                # Expo / React Native Field Auditing Client
└── frontend-web/                   # Next.js Analytics & Supervision Dashboard
```

---

## ⚙️ Requirements and Initial Configuration

### System Prerequisites
*   Python 3.12+
*   Node.js 18+ (npm or yarn)
*   MySQL 8.0+ or MariaDB 10.5+

### 1. Backend Setup
1.  Navigate to the backend directory and create a virtual environment:
    ```bash
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  Install all Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure your environment variables. Create a `.env` file in `backend/`:
    ```env
    DB_USER=root
    DB_PASSWORD=your_secure_password
    DB_HOST=127.0.0.1
    DB_PORT=3306
    DB_NAME=stock_deposit_control
    DATABASE_URL=mysql+aiomysql://root:your_secure_password@127.0.0.1:3306/stock_deposit_control
    CORS_ORIGINS=http://localhost:3000,http://localhost:3001
    JWT_SECRET=your_jwt_signing_key_here
    ```

### 2. Frontend Web Setup
1.  Navigate to the web directory and install Node modules:
    ```bash
    cd ../frontend-web
    npm install
    ```
2.  Configure environment variables in a `.env.local` file:
    ```env
    NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    ```

### 3. Frontend Mobile Setup
1.  Navigate to the mobile directory and install Node modules:
    ```bash
    cd ../frontend-mobile
    npm install
    ```

---

## 🗄️ Database, Migrations, and Seeding

### Schema Design & Composite Keys
Every multi-tenant transaction table (`articulos`, `stock_por_deposito`, `lotes_por_deposito`, `auditorias_registro`) features a non-nullable `tenant_id` column. Primary keys and index constraints are built as composite structures starting with `tenant_id` to guarantee logical isolation and high query performance.

### Running Schema Migrations
Alembic manages all schema updates. Make sure you apply migrations to bring the database structure up to the latest revision:
```bash
# Run inside backend/ directory
alembic -c migrations/alembic.ini upgrade head
```
To rollback the latest migration:
```bash
alembic -c migrations/alembic.ini downgrade -1
```

### Seeding Mock Data
A parametric seed script uses the `Faker` library to populate the database tables with 500 distinct items across 5 deposits. It injects three real-world failure anomalies to test calculation accuracy:
1.  **Ghost Items:** Theoretical stock > 0, physical stock = 0 (simulating inventory shrinkage).
2.  **Expired Lots:** 25% of expiration lot entries (`vencimiento`) are preset to previous months (testing FEFO warnings).
3.  **Fiscal Splits:** A 50/50 split between tax-exempt medicine families and taxable standard VAT items.

To run the seeding script:
```bash
python scripts/seed.py
```

---

## 🚀 Useful Commands

Here is a quick reference guide of commands for local development:

| Command | Directory | Description |
| :--- | :--- | :--- |
| `source venv/bin/activate` | `backend/` | Activate Python virtual environment |
| `uvicorn api.main:app --reload` | `backend/` | Start backend development server (API at port 8000) |
| `PYTHONPATH=. ./backend/venv/bin/pytest` | Root `/` | Run the Python test suite |
| `alembic -c migrations/alembic.ini upgrade head` | `backend/` | Run all outstanding database migrations |
| `npm run dev` | `frontend-web/` | Start Next.js Analytical Web Dashboard |
| `npx expo start` | `frontend-mobile/` | Start React Native Expo server |

---

## ⚠️ Core Development Rules & Guidelines

To maintain clean, safe code across our multi-agent pipeline, all developers and sub-agents must adhere to these policies:

1.  **The Domain is Pure:** Never import `fastapi`, `sqlalchemy`, `alembic`, or `requests` inside `backend/app/`. The domain core must remain 100% pure Python and Pydantic.
2.  **Strict File Ownership boundaries:**
    *   **Backend Core (Jules):** Owns `backend/app/`, `backend/api/`, and repositories (`backend/adapters/repositories/*_repository.py`).
    *   **DBA Specialist:** Sole owner of `backend/adapters/repositories/models/`, `backend/migrations/`, and `backend/scripts/`. Core backend agents must NEVER edit models or create migrations directly.
3.  **Decimal Precision:** All financial calculations, item costs (`pcio_com_siva`), and calculated balances must strictly use Python's `decimal.Decimal` library. Floating-point operations are banned for cost/margin valuations.
4.  **No Raw SQL:** Writing raw SQL string queries inside services, API routers, or adapters is prohibited. Use SQLAlchemy async ORM models and mapping objects to maintain query isolation.
5.  **Role-Based Security:** Product purchase prices (`pcio_com_siva`) must be structurally stripped from API schemas returned to the `supervisor` and `auditor` roles. Always use distinct Pydantic Output models (e.g., public vs admin) to enforce this.
6.  **Migration Safeguards:** Every Alembic script generated must feature a fully functioning `downgrade()` implementation block.
