# 🏛️ System Architecture & Technology Stack Specification

This document serves as the Single Source of Truth (SSoT) for the global architecture, technical constraints, data schemas, and role isolation strategies of the Inventory Audit & Stock Control Platform. All Antigravity AI Sub-Agents must strictly adhere to these definitions.

---

# 1. Global Project Layout (Monorepo)

The project is organized under a **Monorepo** structure to ensure absolute synchronization, unified type definition, and simplified simulation pipelines across all layers:

```text
/ (Root)
├── docs/                      # Global technical and business documentation
├── backend/                   # Python FastAPI core, migrations, and seed scripts
├── frontend-mobile/           # Expo / React Native mobile field application
└── frontend-web/              # Next.js analytical management dashboard
```

# 2. Backend Architecture (Python Core)

## 2.1 Layer Design: Hexagonal Architecture (Ports & Adapters)

The backend service must decouple pure core business logic from transport protocols, external libraries, and database frameworks. It is structured into distinct isolation zones.

### api/ (Primary/Driving Adapters)

Contains the application entrypoints. Powered by FastAPI running over Uvicorn. Responsible for route definitions (v1/), CORS configuration, and request lifecycle management.

#### Critical Component

`api/middlewares/tenant_auth.py`

An authentication interceptor that decodes incoming PyJWT tokens, validates user permissions, extracts the routing metadata (`tenant_id` / `id_sucursal`), and injects it into the database context.

### app/ (Core Domain Layer)

The heart of the application, completely isolated from SQL or external HTTP utilities.

#### app/[modulo]/models.py

Pure domain structures and data validation schemas managed via Pydantic V2.

#### app/[modulo]/services.py

Implements pure business logic, calculations, and use cases.

### adapters/repositories/ (Secondary/Driven Adapters)

Implements the data access layer interfaces defined by the core domain.

> Writing raw SQL queries inside any service or route is strictly prohibited.

---

## 2.2 Database Ecosystem & Infrastructure

### Engine

MariaDB (matching the production infrastructure of the corporate client).

### Data Access Layer (ORM)

SQLAlchemy 2.0 utilizing declarative mapping and fully asynchronous execution wrappers via AIOMySQL.

### Database Versioning (Migrations)

Managed programmatically via Alembic.

#### Strict Guardrail

Every Alembic migration script generated **must** explicitly include a valid `downgrade()` implementation.

---

## 2.3 Data Seeding Factory (backend/scripts/)

### Tooling

Faker library.

### Parameters

Parametric and configurable script (`seed.py`) defaulting to **500 articles**.

### Edge-case Injections

The seed factory intentionally generates inconsistent real-world scenarios such as:

- Positive theoretical stock but zero physical stock
- Valid lot distributions
- Large volumes of expired lots

---

# 3. Relational Database Schema & Data Type Specifications (MariaDB Core)

Financial values must always use **DECIMAL** to avoid floating-point inaccuracies.

## 3.1 Master Data Catalogs

### Table: familias (Product Families)

Defines high-level product categories.

| Column | Type | Description |
|--------|------|-------------|
| id_familia | INT PK AI | Internal identifier |
| des_familia | VARCHAR(255) NOT NULL | Family description |

---

### Table: grupos (Product Groups Hierarchy)

Sub-categories mapped to families.

| Column | Type |
|--------|------|
| id_familia | INT PK FK |
| id_grupo | INT PK |
| des_grupo | VARCHAR(255) |

---

### Table: marcas (Laboratories / Brands)

| Column | Type |
|--------|------|
| id_marca | INT PK AI |
| des_marca | VARCHAR(255) |

---

### Table: articulos (Articles Master Catalog)

| Column | Type |
|--------|------|
| id_articulo | VARCHAR(50) PK |
| presentacion | VARCHAR(255) |
| des_articulo | VARCHAR(255) |
| id_marca | INT FK |
| id_familia | INT FK |
| id_grupo | INT FK |
| pcio_com_siva | DECIMAL(15,4) |

---

### Table: usuarios (Platform Users & Credentials)

| Column | Type |
|--------|------|
| id_usuario | INT PK AI |
| nombre_completo | VARCHAR(255) |
| email | VARCHAR(255) UNIQUE |
| password_hash | VARCHAR(255) |
| rol | ENUM |
| id_sucursal | INT FK |

---

## 3.2 Inventory Ledger & Real-Time Operational Data

### Table: stock_por_deposito

Core operational inventory table.

| Column | Type |
|--------|------|
| id_sucursal | INT PK |
| id_deposito | INT PK |
| id_articulo | VARCHAR(50) PK FK |
| stock_real | INT |
| fue_auditado | BOOLEAN |
| fecha_hora_auditación | DATETIME |

---

### Table: lotes_por_deposito

Tracks production lots.

| Column | Type |
|--------|------|
| id_deposito | INT PK |
| id_articulo | VARCHAR(50) PK FK |
| lote | VARCHAR(50) PK |
| vencimiento | DATE |
| stock_real | INT |

---

## 3.3 Financial Transaction History

### Table: auditorias_registro

Historical audit ledger.

| Column | Type |
|--------|------|
| id_auditoria | BIGINT PK AI |
| id_sucursal | INT |
| id_deposito | INT |
| id_articulo | VARCHAR(50) FK |
| tipo_accion | ENUM |
| cantidad_afectada | INT |
| monto_valorizado | DECIMAL(15,4) |
| id_usuario | INT FK |
| fecha_hora | DATETIME |

---

## 3.4 Role-Based Access Control (RBAC)

### administrador (System Administrator)

#### Scope

Cross-platform governance.

#### Permissions

- Full system access
- User management
- Tenant management
- Financial dashboards
- Security configuration

---

### supervisor (Audit Supervisor)

#### Scope

Operational supervision.

#### Permissions

- Audit monitoring
- Inventory discrepancy resolution
- Operational reports

#### Restriction

Cannot access financial dashboards or `pcio_com_siva`.

---

### auditor (Field Auditor)

#### Scope

Field auditing.

#### Permissions

- Barcode scanning
- Inventory counting
- Manual stock updates

#### Restriction

No administration or financial access.

---

# 4. Scalable Multi-Tenancy Strategy

## Phase 1 — Global Medica (Current MVP)

Logical tenant isolation using `tenant_id` / `id_sucursal`.

## Phase 2 — Farmanor

Database-per-Tenant architecture with dynamic SQLAlchemy connection switching.

---

# 5. Business Core Rules & Math Engines

## Conditional Fiscal Calculation (VAT / IVA)

Tax rules based on `id_familia` and `id_grupo`.

---

## Financial Auditing Foundations (ACID)

Ledger balance entries represent monetary gains or losses.

---

## FEFO Expiration Engine

Implements **First Expired, First Out** scheduling.

Expiration alerts:

- 30 days
- 60 days
- 90 days

---

# 6. Client Frontend Specifications

## 6.1 Mobile Field Application (frontend-mobile/)

### Core Stack

- React Native
- Expo
- TypeScript

### UI/UX

NativeWind (Tailwind CSS)

### Scanning Layer

Hardware-accelerated barcode scanning.

### Offline-First Architecture

Uses SQLite / WatermelonDB with background synchronization.

---

## 6.2 Web Portal (frontend-web/)

### Core Stack

- Next.js
- TypeScript
- Tailwind CSS

### UI Components

- Tremor
- Interactive dashboards
- Data grids

### Operational Purpose

Supports reporting and inventory management.

### Dynamic Client-Side RBAC

#### Administrador Workspace

- User management
- Financial metrics
- Audit logs

#### Supervisor Workspace

- FEFO alerts
- Audit monitoring
- Operational dashboard

#### Auditor Workspace

- Simplified Quick Audit interface
- Manual inventory updates

---

# 7. Security and Configuration Boundaries

## Isolation of Environment Parameters

Configuration values must be loaded from `.env`.

---

## Data Masking

Presentation layers must never expose raw database entities or sensitive information.