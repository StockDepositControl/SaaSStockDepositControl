# SaaS Stock Deposit Control - Backend

The backend service implements the core application logic for inventory audits, stock reconciliation, branch operations, authentication, and analytics reporting. It is a FastAPI-based service using SQLAlchemy async patterns and a multi-database architecture.

## Prerequisites
- Python 3.12+
- MariaDB/MySQL server
- Access to the environment variables for the three database contexts

## Local Setup

1. Activate the virtual environment:
   ```bash
   cd backend
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables in a `.env` file:
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

4. Run database migrations when needed:
   ```bash
   alembic upgrade head
   ```

5. Start the API:
   ```bash
   uvicorn api.main:app --reload
   ```

The API will be available at `http://localhost:8000` and Swagger docs at `http://localhost:8000/docs`.

## Current Architecture

This backend follows a strict Hexagonal Architecture with concrete implementation boundaries:

- `api/`: HTTP entry points, routers, middleware, auth dependencies, exception handlers
- `app/`: pure domain services, Pydantic models, ports, and business rules
- `adapters/`: SQLAlchemy DB adapters, JWT and password providers, repository implementations

## Current database topology

- `db_users`: users, roles, auth data
- `db_articles`: catalog, stock, branches, enterprises
- `db_analytics`: audit events, work sessions, reporting data

The repository and DI layer binds each database through the connection providers implemented in `backend/adapters/database/connection.py`.

## Main business modules

- `app/articles/`: article and catalog logic
- `app/branches/`: branch and warehouse operations
- `app/enterprises/`: tenant and enterprise data
- `app/movements/`: stock deltas, counts, audit data
- `app/users/`: auth, token, user identity
- `app/reports/`: shrinkage, goods received, and inventory balance reports
- `app/work_sessions/`: audit session lifecycle management

## Key runtime files

- `api/main.py`: app setup and router registration
- `api/middlewares/tenant_auth.py`: tenant extraction from JWT claims
- `api/dependencies/services.py`: wiring between repositories and domain services
- `adapters/database/connection.py`: async engine and session factory creation
- `app/reports/services.py`: report generation and valuation logic

## Development rules

- Keep `backend/app/` free of SQLAlchemy, FastAPI, and infrastructure imports.
- Prefer repository ports and dependency injection over direct DB calls.
- Keep financial values as `Decimal` values and avoid floats for cost computations.
- Ensure tenant-scoped behavior is derived from the authenticated JWT context.
