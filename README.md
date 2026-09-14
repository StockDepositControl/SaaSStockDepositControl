# 🏛️ SaaS Stock Deposit Control - Enterprise Platform

A multi-tenant inventory intelligence platform for warehouse auditing, stock reconciliation, branch operations, and finance-oriented reporting. The current implementation follows a strict Hexagonal Architecture, multi-database tenancy model, and RBAC-aware API layer built for operational and analytical workloads.

---

## 📖 Executive Summary

The platform connects warehouse operators, branch managers, and administrators through a single backend service that keeps operational data, authentication, and analytics separated by database and tenant context.

- Field auditing and stock movements are handled through the inventory and audit flow.
- User authentication and tenant-scoped access are resolved in the users database.
- Articles, branches, and enterprises are managed through the operational catalog database.
- Reports are generated from the analytics database and exposed through dedicated, role-protected endpoints.
- Tenant-scoped access is enforced via JWT claims and a request context bound by middleware.

---

## 🛠️ Architecture & Technology Stack

### Backend
- Python 3.12+
- FastAPI for the HTTP API
- SQLAlchemy 2.0 async ORM
- MariaDB/MySQL as the persistence layer
- Alembic for migration lifecycle
- Pydantic V2 schemas and domain models
- JWT-based authentication and tenant binding

### Frontend Web
- Next.js App Router
- React + TypeScript
- Role-aware dashboard experiences and reporting views

### Frontend Mobile
- React Native + Expo
- Mobile audit flows and field data capture

### Architectural pattern
The application is organized around Hexagonal Architecture with a clear separation of concerns:

- API layer: request parsing, auth, routing, validation, HTTP responses
- Domain layer: pure business logic, ports, and Pydantic schemas
- Adapters layer: repository implementations, DB session factories, JWT provider, password hashing

---

## 📁 Monorepo Map

```text
SaaSStockDepositControl/
├── backend/
│   ├── api/
│   │   ├── dependencies/
│   │   ├── middlewares/
│   │   ├── v1/
│   │   ├── exception_handlers.py
│   │   └── main.py
│   ├── app/
│   │   ├── articles/
│   │   ├── branches/
│   │   ├── enterprises/
│   │   ├── movements/
│   │   ├── ports/
│   │   ├── reports/
│   │   ├── users/
│   │   ├── work_sessions/
│   │   ├── exceptions.py
│   │   └── README.md
│   ├── adapters/
│   │   ├── database/
│   │   ├── repositories/
│   │   ├── security/
│   │   └── README.md
│   ├── migrations/
│   ├── scripts/
│   ├── tests/
│   ├── README.md
│   ├── requirements.txt
│   └── pytest.ini
├── docs/
│   ├── ARCHITECTURE.md
│   ├── Plan.md
│   └── deploy/
├── frontend-web/
├── frontend-mobile/
├── specs/
├── shared/
├── README.md
├── docker-compose.yml
├── antigravity.yaml
└── .gitignore
```

---

## 🔐 Multi-Database & Tenant Model

The architecture currently uses three database contexts:

- db_users: authentication, users, roles, tenant-linked identity
- db_articles: catalog, stock, branches, enterprises
- db_analytics: audit records, session tracking, report data

This is implemented through:

- `backend/adapters/database/connection.py`
- `backend/adapters/database/multi_tenant.py`
- `backend/api/middlewares/tenant_auth.py`

The tenant middleware reads the JWT, extracts `tenant_id`, `branch_id`, and `user_id`, and stores them in a request-scoped ContextVar so repositories can filter by tenant safely.

---

## 🧩 Domain & API Boundaries

The backend domain remains insulated from HTTP and SQL infrastructure.

- `backend/app/` contains pure domain logic and Pydantic models.
- `backend/api/` contains routes, auth dependencies, and HTTP middleware.
- `backend/adapters/` implements repository adapters and infrastructure providers.

Important rules currently in force:

1. Domain code should not import `fastapi`, `sqlalchemy`, or other infrastructure libraries.
2. Repository implementations must align to the abstract port contracts in `backend/app/*/ports.py`.
3. JWT claims are decoded and verified; they are not encrypted payloads.
4. Financial calculations use `Decimal` for monetary values.

---

## 📊 Reporting & Business Modules

The current codebase includes report-oriented domain services beyond the base CRUD flow:

- `backend/app/reports/` for shrinkage, goods-received, and daily inventory balance calculations
- `backend/app/movements/` for audit and stock delta logic
- `backend/app/work_sessions/` for session lifecycle and audit state
- `backend/api/v1/reports.py` for administrator-only report endpoints

These modules are wired through dependency providers in `backend/api/dependencies/services.py` and consumed by the FastAPI routes.

---

## ⚙️ Environment Configuration

Example backend environment settings:

```env
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

ARTICLES_DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/db_articles
USERS_DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/db_users
ANALYTICS_DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/db_analytics

SECRET_KEY=your_jwt_signing_key_here
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## 🚀 Useful Commands

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Run tests:

```bash
cd backend
pytest
```

Run migrations from the backend directory:

```bash
alembic upgrade head
```

---

## ✅ Development Rules

1. Keep domain logic pure and infrastructure-independent.
2. Route all persistence through repository ports and adapters.
3. Filter tenant-bound queries using JWT-derived context.
4. Use distinct output schemas for role-based data masking when necessary.
5. Preserve the ownership boundaries between domain code and DBA-managed ORM/migration files.
6. Review architecture changes against this repo state before making new additions.

---

## 📚 Key Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [backend/README.md](backend/README.md)
- [backend/app/README.md](backend/app/README.md)
- [backend/adapters/README.md](backend/adapters/README.md)
