# 📚 SaaS Stock Deposit Control - REST API Documentation

Comprehensive technical reference for the backend API service of **SaaS Stock Deposit Control**.  
This document specifies all endpoints, authentication mechanisms, request payloads, headers, query parameters, response structures, and HTTP status codes, structured similarly to an interactive Swagger/OpenAPI documentation.

---

## 📑 Table of Contents

1. [Interactive API Explorers (Swagger & ReDoc)](#-interactive-api-explorers)
2. [Base URLs & Versioning](#-base-urls--versioning)
3. [Authentication & Authorization (RBAC)](#-authentication--authorization-rbac)
4. [Multi-Tenancy Context & Data Isolation](#-multi-tenancy-context--data-isolation)
5. [Dynamic Data Masking (Role-Based Field Visibility)](#-dynamic-data-masking)
6. [Centralized Error Handling](#-centralized-error-handling)
7. [API Endpoints Reference](#-api-endpoints-reference)
   - [1. Infrastructure & Health Probes](#1-infrastructure--health-probes)
   - [2. Authentication](#2-authentication)
   - [3. Articles & Catalog](#3-articles--catalog)
   - [4. Stock Management & Audit Flow](#4-stock-management--audit-flow)
   - [5. Enterprises Management](#5-enterprises-management)
   - [6. Branches Management](#6-branches-management)
   - [7. Executive & Analytics Reports (Admin Only)](#7-executive--analytics-reports-admin-only)
   - [8. User Management (Admin Only)](#8-user-management-admin-only)
8. [Machine-Readable Specification](#-machine-readable-specification)

---

## 🚀 Interactive API Explorers

FastAPI provides automated interactive web interfaces powered by OpenAPI:

| Interface | URL | Description |
| :--- | :--- | :--- |
| **Swagger UI** | `http://localhost:8000/docs` | Interactive API explorer where you can execute requests directly with Bearer token authentication. |
| **ReDoc** | `http://localhost:8000/redoc` | Clean, responsive technical reference documentation. |
| **Raw OpenAPI Schema** | `http://localhost:8000/openapi.json` | JSON schema conforming to OpenAPI 3.1.0 standard (exported also to [`docs/openapi.json`](openapi.json)). |

To access the interactive Swagger UI locally:
```bash
cd backend
source .venv/bin/activate
uvicorn api.main:app --reload
# Navigate to: http://localhost:8000/docs
```

---

## 🌐 Base URLs & Versioning

- **Root Host**: `http://localhost:8000` (direct backend dev) / `http://localhost:8080` (behind Caddy reverse proxy) / `https://<domain>` (production)
- **API Version 1 Prefix**: `/api/v1`
- **Default Content-Type**: `application/json`

All production resources are scoped under `/api/v1/*` except top-level health probes (`/health`).

---

## 🔐 Authentication & Authorization (RBAC)

The platform secures endpoints using standard **JSON Web Tokens (JWT)** passed via HTTP Authorization headers.

### Authorization Header
```http
Authorization: Bearer <your_jwt_access_token>
```

### User Roles & Hierarchy
The system enforces strict Role-Based Access Control (RBAC):

| Role | Identifier | Permitted Operations |
| :--- | :--- | :--- |
| **Administrador** | `administrador` | **Full access**: Financial queries, executive reports (`/reports/*`), tenant user administration (`/users/*`), valorized dashboard KPIs (`/stock/kpis`), unmasked purchase prices (`pcio_com_siva`), enterprise/branch CRUD, stock adjustments. |
| **Supervisor** | `supervisor` | **Supervisory access**: Physical counts, stock adjustments, operational dashboard KPIs (`/stock/kpis` with financial fields masked), catalog browsing with financial fields masked, branch stock visibility. |
| **Auditor** | `auditor` | **Field operator**: Physical count capture, batch offline synchronization, operational dashboard KPIs (`/stock/kpis` with financial fields masked), catalog lookup with financial fields masked. |
| **Public / Anonymous** | *None* | Health checks (`/health`, `/api/v1/health`), and user authentication (`/api/v1/auth/login`). |

### JWT Token Claims Structure
Tokens emitted by `/api/v1/auth/login` include the following claims:
```json
{
  "sub": "user@enterprise.com",
  "role": "administrador",
  "tenant_id": 1,
  "branch_id": 1,
  "user_id": 42,
  "id_usuario": 42,
  "exp": 1728777600
}
```

---

## 🏢 Multi-Tenancy Context & Data Isolation

The API implements dynamic multi-tenancy using context variables (`contextvars`) managed by `TenantAuthMiddleware`.

1. **Extraction**: The middleware decodes the incoming `Authorization: Bearer <token>`.
2. **Context Binding**: `tenant_id`, `branch_id`, and `user_id` are bound to the current execution thread context.
3. **Database Routing**: 
   - `db_articles`: Tenant-scoped catalog and stock.
   - `db_users`: Centralized user credentials and roles.
   - `db_analytics`: Partitioned audit logs, work sessions, and financial ledger balances.

---

## 🎭 Dynamic Data Masking

Sensitive financial attributes (such as `pcio_com_siva` — Purchase Cost Without VAT — and valorized discrepancy totals `monto_valorizado_baja` / `monto_valorizado_alta`) are conditionally exposed based on the requesting user's role:
- **`administrador`**: Full schemas are serialized (`ArticuloAdminOut`, `ArticleStockPositionAdminOut`, `DashboardKPIsResponse`), including `pcio_com_siva` and valorized financial totals.
- **`supervisor` / `auditor`**: Responses automatically fall back to public schemas (`ArticuloPublicOut`, `ArticleStockPositionPublicOut`, `DashboardKPIsPublicOut`), excluding financial fields at the serializer boundary.

---

## ⚠️ Centralized Error Handling

The backend returns standardized JSON structures for both validation errors and business domain exceptions.

### Domain Exception Response Format
```json
{
  "detail": "Descriptive message of the business rule violation or missing resource",
  "error_type": "EntityNotFound | BusinessRuleViolation | NoActiveWorkSession | InternalDomainError"
}
```

### Standard HTTP Status Codes

| Code | Status | Meaning |
| :--- | :--- | :--- |
| `200` | OK | Request succeeded. |
| `201` | Created | Resource successfully created. |
| `204` | No Content | Resource deleted or empty successful response. |
| `400` | Bad Request | Business rule failure or invalid query parameters. |
| `401` | Unauthorized | Missing, invalid, or expired JWT bearer token. |
| `403` | Forbidden | User lacks necessary RBAC privileges for the requested endpoint. |
| `404` | Not Found | Requested entity was not found in the current tenant scope. |
| `409` | Conflict | State conflict (e.g. no active work session found for audit). |
| `422` | Unprocessable Entity | Pydantic validation failure on request payload or query parameters. |
| `500` | Internal Server Error | Unhandled internal exception. |
| `503` | Service Unavailable | Database connection probe failure. |

---

## 📡 API Endpoints Reference

---

### 1. Infrastructure & Health Probes

#### `GET /health` & `GET /api/v1/health`
Probes database connectivity across all three logical databases (`db_articles`, `db_users`, `db_analytics`) through `ConnectionProvider.check_databases()`. Returns HTTP `200 OK` only when all three databases respond to `SELECT 1`.

- **Authentication**: None (Public)
- **Query Parameters**: None

##### Response `200 OK` (Healthy)
```json
{
  "status": "healthy",
  "database": "connected",
  "databases": {
    "articles": "connected",
    "users": "connected",
    "analytics": "connected"
  },
  "version": "1.0.0"
}
```

##### Response `503 Service Unavailable` (Unhealthy)
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "databases": {
    "articles": "connected",
    "users": "disconnected",
    "analytics": "connected"
  },
  "version": "1.0.0",
  "detail": "Database connectivity probe failed"
}
```

---

### 2. Authentication

#### `POST /api/v1/auth/login`
Verifies user credentials against `db_users` and issues a signed JWT access token.

- **Authentication**: None (Public)
- **Request Headers**: `Content-Type: application/json`

##### Request Body (`LoginCredentials`)
| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `email` | string | **Yes** | Registered user email address | `"admin@farmaciadelsol.com"` |
| `password` | string | **Yes** | Plaintext user password | `"SecretP@ss123"` |

```json
{
  "email": "admin@farmaciadelsol.com",
  "password": "SecretP@ss123"
}
```

##### Response `200 OK` (`AuthToken`)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

##### Error Responses
- `400 Bad Request`: `{"detail": "Invalid credentials", "error_type": "BusinessRuleViolation"}`
- `400 Bad Request`: `{"detail": "User account is inactive", "error_type": "BusinessRuleViolation"}` (when the user's `is_active` flag is `false`)
- `404 Not Found`: `{"detail": "User not found", "error_type": "EntityNotFound"}`

---

### 3. Articles & Catalog

#### `GET /api/v1/articles`
Retrieves a paginated list of catalog articles enriched with effective stock levels and current audit status for the active work session.

- **Authentication**: Bearer Token (`administrador`, `supervisor`, `auditor`)
- **Query Parameters**:

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `page` | integer | No | `1` | Page number (1-indexed, $\ge 1$) |
| `limit` | integer | No | `50` | Page size ($1 \le \text{limit} \le 200$) |
| `id_deposito` | integer | No | `1` | Warehouse/Deposit ID for stock calculation ($\ge 1$) |
| `search` | string | No | `null` | Substring match on article description or code |
| `id_familia` | string | No | `null` | Filter by Family ID |
| `id_grupo` | string | No | `null` | Filter by Group ID |
| `fue_auditado` | boolean | No | `null` | Filter by audited state (`true` or `false`) |

##### Response `200 OK` (Admin view with `pcio_com_siva`)
```json
{
  "items": [
    {
      "id_articulo": "ART00123",
      "des_articulo": "IBUPROFENO 400MG X 10 COMP",
      "presentacion": "CAJA X 10",
      "id_marca": 14,
      "des_marca": "LABORATORIOS ROEMMERS",
      "id_familia": "FAM01",
      "des_familia": "MEDICAMENTOS",
      "id_grupo": "GRP02",
      "des_grupo": "ANALGESICOS",
      "pcio_com_siva": "450.50",
      "fue_auditado": true,
      "stock_real": 32
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

##### Response `200 OK` (Auditor/Supervisor view - Masked `pcio_com_siva`)
```json
{
  "items": [
    {
      "id_articulo": "ART00123",
      "des_articulo": "IBUPROFENO 400MG X 10 COMP",
      "presentacion": "CAJA X 10",
      "id_marca": 14,
      "des_marca": "LABORATORIOS ROEMMERS",
      "id_familia": "FAM01",
      "des_familia": "MEDICAMENTOS",
      "id_grupo": "GRP02",
      "des_grupo": "ANALGESICOS",
      "fue_auditado": true,
      "stock_real": 32
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

#### `GET /api/v1/articles/search`
Quick lookup by exact Article ID, barcode, or tokenized description. Used primarily by barcode scanners in mobile audit apps.

- **Authentication**: Bearer Token
- **Query Parameters**:

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `query` | string | **Yes** | Article code, EAN barcode, or textual search tokens (min length 1) |

##### Response `200 OK`
```json
[
  {
    "id_articulo": "7791234567890",
    "des_articulo": "PARACETAMOL 500MG X 20 COMP",
    "presentacion": "BLISTER",
    "id_marca": 5,
    "des_marca": "BAYER",
    "id_familia": "FAM01",
    "des_familia": "MEDICAMENTOS",
    "id_grupo": "GRP02",
    "des_grupo": "ANALGESICOS",
    "pcio_com_siva": "320.00",
    "fue_auditado": false,
    "stock_real": 15
  }
]
```

---

#### `GET /api/v1/articles/{id_articulo}`
Retrieves a single article by ID enriched with effective stock in the target deposit.

- **Authentication**: Bearer Token
- **Path Parameters**:
  - `id_articulo` (string, required): Unique article identifier.
- **Query Parameters**:
  - `id_deposito` (integer, optional, default: `1`): Deposit/Warehouse ID ($\ge 1$).

##### Response `200 OK`
```json
{
  "id_articulo": "ART00123",
  "des_articulo": "IBUPROFENO 400MG X 10 COMP",
  "presentacion": "CAJA X 10",
  "id_marca": 14,
  "des_marca": "LABORATORIOS ROEMMERS",
  "id_familia": "FAM01",
  "des_familia": "MEDICAMENTOS",
  "id_grupo": "GRP02",
  "des_grupo": "ANALGESICOS",
  "pcio_com_siva": "450.50",
  "fue_auditado": true,
  "stock_real": 32
}
```

##### Error Responses
- `404 Not Found`: `{"detail": "Article not found", "error_type": "EntityNotFound"}`

---

### 4. Stock Management & Audit Flow

#### `POST /api/v1/stock/audit`
Registers an inventory audit record. Automatically determines the stock discrepancy (delta), assigns the action type (`Alta`, `Baja`, `Sin Acción`), valorizes financial cost, and updates the active work session.

- **Authentication**: Bearer Token (`administrador`, `supervisor`, `auditor`)
- **Status Code**: `201 Created`

##### Input Modes
The endpoint enforces one of two input modes:
1. **Physical Count Mode**: Client passes observed count in `stock_fisico_contado`. Backend computes discrepancy against theoretical stock.
2. **Variance Mode**: Client directly specifies `cantidad_afectada` and `tipo_accion`.

##### Request Body (`AuditEntryRequest`)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `id_articulo` | string | **Yes** | Article code or barcode |
| `stock_fisico_contado` | integer | Mode 1 | Total physical count counted ($\ge 0$) |
| `cantidad_afectada` | integer | Mode 2 | Quantity adjustment ($\ge 0$) |
| `tipo_accion` | string | Mode 2 | `"Alta"`, `"Baja"`, or `"Sin Acción"` |
| `id_sucursal` | integer | No | Branch ID (defaults to JWT claim `branch_id`) |
| `id_deposito` | integer | No | Warehouse ID (defaults to `1`) |
| `observation` | string | No | Operator note (max 500 characters) |

###### Example: Physical Count Mode
```json
{
  "id_articulo": "ART00123",
  "id_sucursal": 1,
  "id_deposito": 1,
  "stock_fisico_contado": 35,
  "observation": "Recuento de estantería central"
}
```

###### Example: Variance Mode
```json
{
  "id_articulo": "ART00123",
  "id_sucursal": 1,
  "id_deposito": 1,
  "cantidad_afectada": 2,
  "tipo_accion": "Baja",
  "observation": "Caja dañada por humedad"
}
```

##### Response `201 Created` (`AuditEntryResult`)
```json
{
  "client_uuid": "e4b52df3-1082-45e0-9ef9-b4cb6dfb9c02",
  "id_articulo": "ART00123",
  "stock_real": 32,
  "stock_fisico_contado": 35,
  "delta_stock": 3,
  "tipo_accion": "Alta",
  "cantidad_afectada": 3,
  "audit_quantity": 35,
  "monto_valorizado": "1351.50",
  "audit_id": 1052
}
```

##### Error Responses
- `400 Bad Request`: Validation failure (neither mode provided).
- `404 Not Found`: Article not found in catalog.
- `409 Conflict`: `{"detail": "No active work session found for tenant and branch", "error_type": "NoActiveWorkSession"}`

---

#### `GET /api/v1/stock/position`
Retrieves the current physical and theoretical stock position of an article in a specified branch and deposit.

- **Authentication**: Bearer Token (`administrador`, `supervisor`, `auditor`)
- **Query Parameters**:

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id_articulo` | string | **Yes** | - | Article code |
| `id_sucursal` | integer | No | `claims.branch_id` | Branch ID |
| `id_deposito` | integer | No | `1` | Warehouse/Deposit ID |

##### Response `200 OK` (Admin role)
```json
{
  "des_articulo": "IBUPROFENO 400MG X 10 COMP",
  "presentacion": "CAJA X 10",
  "des_marca": "LABORATORIOS ROEMMERS",
  "des_familia": "MEDICAMENTOS",
  "des_grupo": "ANALGESICOS",
  "id_sucursal": 1,
  "id_deposito": 1,
  "stock_real": 32,
  "pcio_com_siva": "450.50"
}
```

##### Response `200 OK` (Supervisor/Auditor role)
```json
{
  "des_articulo": "IBUPROFENO 400MG X 10 COMP",
  "presentacion": "CAJA X 10",
  "des_marca": "LABORATORIOS ROEMMERS",
  "des_familia": "MEDICAMENTOS",
  "des_grupo": "ANALGESICOS",
  "id_sucursal": 1,
  "id_deposito": 1,
  "stock_real": 32
}
```

---

#### `POST /api/v1/stock/audit/batch`
Batch processor designed for mobile devices operating in offline mode. When mobile clients regain network connectivity, queued entries are dispatched in a single request. Deduplication prevents re-processing duplicate records.

- **Authentication**: Bearer Token (`administrador`, `supervisor`, `auditor`)
- **Status Code**: `200 OK`

##### Request Body (`AuditBatchInput`)
```json
{
  "items": [
    {
      "id_articulo": "ART00123",
      "stock_fisico_contado": 35,
      "id_sucursal": 1,
      "id_deposito": 1,
      "observation": "Offline capture"
    },
    {
      "id_articulo": "ART00456",
      "cantidad_afectada": 1,
      "tipo_accion": "Baja",
      "id_sucursal": 1,
      "id_deposito": 1,
      "observation": "Vencido"
    }
  ]
}
```

##### Response `200 OK` (`AuditBatchResult`)
```json
{
  "results": [
    {
      "client_uuid": "11a54728-6617-48f8-bce3-f8ad7887d195",
      "id_articulo": "ART00123",
      "stock_real": 32,
      "stock_fisico_contado": 35,
      "delta_stock": 3,
      "tipo_accion": "Alta",
      "cantidad_afectada": 3,
      "audit_quantity": 35,
      "monto_valorizado": "1351.50",
      "audit_id": 1053
    },
    {
      "client_uuid": "7b235e12-32a1-432d-9477-d67b2ff0aa71",
      "id_articulo": "ART00456",
      "stock_real": 10,
      "stock_fisico_contado": null,
      "delta_stock": -1,
      "tipo_accion": "Baja",
      "cantidad_afectada": 1,
      "audit_quantity": 9,
      "monto_valorizado": "180.00",
      "audit_id": 1054
    }
  ],
  "total_processed": 2,
  "duplicates_skipped": 0
}
```

---

#### `GET /api/v1/stock/kpis`
Returns database-aggregated dashboard KPIs for the active work session scoped to the user's tenant and branch. Enforces structural RBAC so valorized financial discrepancy totals are returned only to administrators.

- **Authentication**: Bearer Token (`administrador`, `supervisor`, `auditor`)
- **Status Code**: `200 OK`
- **Query Parameters & Context Scoping**:

| Parameter | Source | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id_deposito` | Query | integer | No | `1` | Warehouse/Deposit ID ($\ge 1$) for stock & out-of-stock resolution |
| `branch_id` (`id_sucursal`) | JWT Claims | integer | Implicit | `1` | Branch ID extracted from `claims.branch_id` to resolve the active work session |
| `tenant_id` | JWT Claims | string | Implicit | `"1"` | Tenant ID extracted from `claims.tenant_id` |

##### Response Schema Fields (`DashboardKPIsResponse` / `DashboardKPIsPublicOut`)
| Field | Type | Visibility | Description |
| :--- | :--- | :--- | :--- |
| `total_articulos` | integer | All audit roles | Total number of catalog articles |
| `auditados` | integer | All audit roles | Distinct articles audited in the active work session |
| `pendientes` | integer | All audit roles | Remaining unaudited articles (`total_articulos - auditados`) |
| `porcentaje_avance` | integer | All audit roles | Audit completion percentage (`0` to `100`) |
| `discrepancias_alta` | integer | All audit roles | Number of positive variance entries (`Alta` / surplus) in the active session |
| `discrepancias_baja` | integer | All audit roles | Number of negative variance entries (`Baja` / shrinkage) in the active session |
| `sin_accion` | integer | All audit roles | Number of zero-variance entries (`Sin Acción`) in the active session |
| `out_of_stock_count` | integer | All audit roles | Number of articles with effective stock $\le 0$ in `id_deposito` |
| `monto_valorizado_baja` | string (Decimal) \| null | `administrador` only | Total valorized financial loss from `Baja` discrepancies |
| `monto_valorizado_alta` | string (Decimal) \| null | `administrador` only | Total valorized capital addition from `Alta` discrepancies |

##### Example `curl` Request
```bash
curl -X GET "http://localhost:8000/api/v1/stock/kpis?id_deposito=1" \
  -H "Authorization: Bearer <your_jwt_access_token>" \
  -H "Accept: application/json"
```

##### Response `200 OK` (Admin role — `DashboardKPIsResponse`)
```json
{
  "total_articulos": 1200,
  "auditados": 450,
  "pendientes": 750,
  "porcentaje_avance": 38,
  "discrepancias_alta": 12,
  "discrepancias_baja": 8,
  "sin_accion": 430,
  "out_of_stock_count": 34,
  "monto_valorizado_baja": "18450.75",
  "monto_valorizado_alta": "9230.00"
}
```

##### Response `200 OK` (Supervisor/Auditor role — `DashboardKPIsPublicOut`)
```json
{
  "total_articulos": 1200,
  "auditados": 450,
  "pendientes": 750,
  "porcentaje_avance": 38,
  "discrepancias_alta": 12,
  "discrepancias_baja": 8,
  "sin_accion": 430,
  "out_of_stock_count": 34
}
```

##### Status Codes & Error Responses
- `200 OK`: Aggregated KPI metrics returned.
- `401 Unauthorized`: Missing or invalid JWT Bearer token.
- `403 Forbidden`: User role is not in `["administrador", "supervisor", "auditor"]`.
- `422 Unprocessable Entity`: Invalid query parameter (e.g., `id_deposito < 1`).

---

### 5. Enterprises Management

#### `GET /api/v1/enterprises`
Retrieves all registered enterprises (tenants).

- **Authentication**: Bearer Token
- **Response `200 OK`**:
```json
[
  {
    "tenant_id": 1,
    "description": "Farmacias del Sol S.A."
  },
  {
    "tenant_id": 2,
    "description": "Droguería Central"
  }
]
```

---

#### `GET /api/v1/enterprises/{tenant_id}`
Retrieves details for a specific enterprise by its `tenant_id`.

- **Path Parameters**: `tenant_id` (integer)
- **Response `200 OK`**:
```json
{
  "tenant_id": 1,
  "description": "Farmacias del Sol S.A."
}
```
- **Error Response**: `404 Not Found` if not found.

---

#### `POST /api/v1/enterprises`
Registers a new tenant enterprise.

- **Status Code**: `201 Created`
- **Request Body**:
```json
{
  "tenant_id": 3,
  "description": "Farmacia Nueva Esperanza"
}
```
- **Response `201 Created`**: Returns created `Enterprise` object.

---

#### `PUT /api/v1/enterprises/{tenant_id}`
Updates enterprise metadata.

- **Path Parameters**: `tenant_id` (integer)
- **Request Body**:
```json
{
  "description": "Farmacia Nueva Esperanza S.R.L."
}
```
- **Response `200 OK`**: Returns updated `Enterprise` object.

---

#### `DELETE /api/v1/enterprises/{tenant_id}`
Removes an enterprise.

- **Path Parameters**: `tenant_id` (integer)
- **Response `204 No Content`**

---

### 6. Branches Management

#### `GET /api/v1/branches/{branch_id}`
Retrieves a branch by its unique ID.

- **Path Parameters**: `branch_id` (integer)
- **Response `200 OK`**:
```json
{
  "id_branch": 1,
  "tenant_id": 1,
  "description": "Sucursal Casa Central"
}
```

---

#### `GET /api/v1/branches/tenant/{tenant_id}`
Lists all physical branches associated with a specific tenant enterprise.

- **Path Parameters**: `tenant_id` (integer)
- **Response `200 OK`**:
```json
[
  {
    "id_branch": 1,
    "tenant_id": 1,
    "description": "Sucursal Casa Central"
  },
  {
    "id_branch": 2,
    "tenant_id": 1,
    "description": "Sucursal Belgrano"
  }
]
```

---

#### `POST /api/v1/branches`
Creates a new physical store or warehouse branch.

- **Status Code**: `201 Created`
- **Request Body**:
```json
{
  "tenant_id": 1,
  "description": "Sucursal Palermo"
}
```
- **Response `201 Created`**: Returns created `Branch` object.

---

#### `PUT /api/v1/branches/{branch_id}`
Updates branch description.

- **Path Parameters**: `branch_id` (integer)
- **Request Body**:
```json
{
  "description": "Sucursal Palermo Soho"
}
```
- **Response `200 OK`**: Returns updated `Branch` object.

---

#### `DELETE /api/v1/branches/{branch_id}`
Deletes a branch.

- **Path Parameters**: `branch_id` (integer)
- **Response `204 No Content`**

---

### 7. Executive & Analytics Reports (Admin Only)

> [!IMPORTANT]
> All endpoints under `/api/v1/reports/*` are strictly restricted to users with the **`administrador`** role. Calls by `supervisor` or `auditor` return `403 Forbidden`.

---

#### `GET /api/v1/reports/shrinkage`
Generates the **Consolidated Shrinkage & Financial Erosion Report** (Mermas / Pérdidas de Stock).  
Applies fiscal VAT classification:
- **Medications** (`MEDICAMENTOS`): Fixed 0% VAT rate.
- **Perfumes / General**: Uses parameterized `default_vat_rate` (default: 21%).

Calculates total financial erosion based on unit cost plus VAT.

- **Authentication**: Bearer Token (`administrador` required)
- **Query Parameters**:

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `start_date` | string (date) | **Yes** | - | Start date in `YYYY-MM-DD` format |
| `end_date` | string (date) | **Yes** | - | End date in `YYYY-MM-DD` format |
| `default_vat_rate` | number (Decimal) | No | `0.21` | Fiscal VAT rate for non-exempt articles ($0.0 \le \text{rate} \le 1.0$) |
| `branch_id` | integer | No | `null` | Optional branch filter |

##### Response `200 OK` (`ShrinkageReportResponse`)
```json
{
  "tenant_id": "1",
  "start_date": "2026-10-01",
  "end_date": "2026-10-12",
  "default_vat_rate": "0.21",
  "total_items": 2,
  "total_shrinkage_units": 5,
  "total_financial_erosion": "2350.25",
  "line_items": [
    {
      "article_code": "ART00123",
      "des_articulo": "IBUPROFENO 400MG X 10 COMP",
      "des_familia": "MEDICAMENTOS",
      "pcio_com_siva": "450.50",
      "vat_rate": "0.00",
      "total_unit_cost": "450.50",
      "total_quantity": 3,
      "total_financial_loss": "1351.50"
    },
    {
      "article_code": "ART00999",
      "des_articulo": "SHAMPOO ANTICASPA 400ML",
      "des_familia": "PERFUMERIA",
      "pcio_com_siva": "685.00",
      "vat_rate": "0.21",
      "total_unit_cost": "828.85",
      "total_quantity": 2,
      "total_financial_loss": "1657.70"
    }
  ]
}
```

---

#### `GET /api/v1/reports/goods-received`
Generates the **Goods Received & Injected Capital Report** (Altas / Ingresos de Stock).  
Consolidates audit additions and calculates injected inventory value.

- **Authentication**: Bearer Token (`administrador` required)
- **Query Parameters**:

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `start_date` | string (date) | **Yes** | - | Start date in `YYYY-MM-DD` format |
| `end_date` | string (date) | **Yes** | - | End date in `YYYY-MM-DD` format |
| `default_vat_rate` | number (Decimal) | No | `0.21` | Fiscal VAT rate for non-exempt articles ($0.0 \le \text{rate} \le 1.0$) |
| `branch_id` | integer | No | `null` | Optional branch filter |

##### Response `200 OK` (`GoodsReceivedReportResponse`)
```json
{
  "tenant_id": "1",
  "start_date": "2026-10-01",
  "end_date": "2026-10-12",
  "default_vat_rate": "0.21",
  "total_items": 1,
  "total_added_units": 10,
  "total_capital_inyectado": "4505.00",
  "line_items": [
    {
      "barcode": "7791234567890",
      "article_code": "ART00123",
      "des_articulo": "IBUPROFENO 400MG X 10 COMP",
      "des_familia": "MEDICAMENTOS",
      "reason": "Sobrante de inventario / Ajuste",
      "quantity_added": 10,
      "pcio_com_siva": "450.50",
      "vat_rate": "0.00",
      "total_unit_cost": "450.50",
      "capital_inyectado": "4505.00"
    }
  ]
}
```

---

#### `GET /api/v1/reports/inventory-balance`
Generates the **Daily Inventory Balance & Cost Ledger Report**.  
Consolidates physical and economic movements per day and calculates **Net Patrimonial Variation**:
$$\Delta \text{Patrimonial} = \text{Total Altas (Valorizadas)} - \text{Total Mermas (Valorizadas)}$$

- **Authentication**: Bearer Token (`administrador` required)
- **Query Parameters**:

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `start_date` | string (date) | **Yes** | - | Start date in `YYYY-MM-DD` format |
| `end_date` | string (date) | **Yes** | - | End date in `YYYY-MM-DD` format |
| `branch_id` | integer | No | `null` | Optional branch filter |

##### Response `200 OK` (`DailyInventoryBalanceResponse`)
```json
{
  "tenant_id": "1",
  "branch_id": null,
  "start_date": "2026-10-10",
  "end_date": "2026-10-12",
  "total_days": 3,
  "total_addition_value": "15400.00",
  "total_shrinkage_value": "3200.50",
  "net_patrimonial_variation": "12199.50",
  "daily_summaries": [
    {
      "report_date": "2026-10-10",
      "total_audit_articles": 45,
      "total_processed_units": 820,
      "total_addition_units": 15,
      "total_shrinkage_units": 4,
      "total_addition_value": "5200.00",
      "total_shrinkage_value": "950.00",
      "net_patrimonial_variation": "4250.00"
    },
    {
      "report_date": "2026-10-11",
      "total_audit_articles": 30,
      "total_processed_units": 610,
      "total_addition_units": 20,
      "total_shrinkage_units": 8,
      "total_addition_value": "10200.00",
      "total_shrinkage_value": "2250.50",
      "net_patrimonial_variation": "7949.50"
    }
  ]
}
```

---

### 8. User Management (Admin Only)

> [!IMPORTANT]
> All endpoints under `/api/v1/users/*` are strictly restricted to users with the **`administrador`** role (`RoleChecker(allowed_roles=["administrador"])`) and are automatically scoped to the administrator's `tenant_id` extracted from the JWT token claims. Calls by `supervisor` or `auditor` return `403 Forbidden`.

---

#### `GET /api/v1/users`
Retrieves all organization users belonging to the authenticated administrator's tenant, with optional inclusion of inactive accounts.

- **Authentication**: Bearer Token (`administrador` required)
- **Status Code**: `200 OK`
- **Query Parameters**:

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `include_inactive` | boolean | No | `true` | Whether to include deactivated user accounts (`is_active: false`) in the result list |

##### Example `curl` Request
```bash
curl -X GET "http://localhost:8000/api/v1/users?include_inactive=true" \
  -H "Authorization: Bearer <your_jwt_access_token>" \
  -H "Accept: application/json"
```

##### Response `200 OK` (`List[UserResponse]`)
```json
[
  {
    "user_id": 1,
    "tenant_id": 1,
    "first_name": "Carlos",
    "last_name": "Gómez",
    "email": "admin@farmaciadelsol.com",
    "branch_id": 1,
    "is_active": true,
    "roles": ["administrador"]
  },
  {
    "user_id": 2,
    "tenant_id": 1,
    "first_name": "Lucía",
    "last_name": "Fernández",
    "email": "auditor@farmaciadelsol.com",
    "branch_id": 1,
    "is_active": true,
    "roles": ["auditor"]
  }
]
```

##### Status Codes & Error Responses
- `200 OK`: Returns array of `UserResponse` objects for the administrator's tenant.
- `401 Unauthorized`: Missing or invalid JWT Bearer token.
- `403 Forbidden`: User does not hold the `administrador` role.
- `422 Unprocessable Entity`: Invalid boolean query parameter.

---

#### `PATCH /api/v1/users/{user_id}/status`
Activates or deactivates a user account within the administrator's tenant. Enforces anti-self-deactivation protection at the domain service layer so an administrator cannot lock themselves out. Deactivated users (`is_active: false`) are immediately blocked from authenticating via `POST /api/v1/auth/login`.

- **Authentication**: Bearer Token (`administrador` required)
- **Status Code**: `200 OK`
- **Path Parameters**:
  - `user_id` (integer, required): Target user identifier within the tenant.

##### Request Body (`UserStatusUpdate`)
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `is_active` | boolean | **Yes** | Target activation state (`true` = active, `false` = inactive) |

```json
{
  "is_active": false
}
```

##### Example `curl` Request
```bash
curl -X PATCH "http://localhost:8000/api/v1/users/2/status" \
  -H "Authorization: Bearer <your_jwt_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

##### Response `200 OK` (`UserResponse`)
```json
{
  "user_id": 2,
  "tenant_id": 1,
  "first_name": "Lucía",
  "last_name": "Fernández",
  "email": "auditor@farmaciadelsol.com",
  "branch_id": 1,
  "is_active": false,
  "roles": ["auditor"]
}
```

##### Error Responses & Domain Protections
- `400 Bad Request` (**Anti-Self-Deactivation Protection** — `BusinessRuleViolationException` / domain validation error when `user_id == claims.user_id` and `is_active == false`):
  ```json
  {
    "detail": "Administrators cannot deactivate their own account",
    "error_type": "BusinessRuleViolation"
  }
  ```
- `404 Not Found` (`EntityNotFoundException` when target `user_id` does not exist in the administrator's tenant):
  ```json
  {
    "detail": "User 999 not found in this tenant",
    "error_type": "EntityNotFound"
  }
  ```
- `401 Unauthorized` / `403 Forbidden`: Missing token or non-admin role.
- `422 Unprocessable Entity`: Invalid payload schema.

---

#### `PUT /api/v1/users/{user_id}/roles`
Assigns operational roles to a user within the administrator's tenant. Enforces a strict **single-role constraint** (exactly one role from `["administrador", "supervisor", "auditor"]`) and **anti-self-demotion protection** so an administrator cannot strip their own `administrador` role.

- **Authentication**: Bearer Token (`administrador` required)
- **Status Code**: `200 OK`
- **Path Parameters**:
  - `user_id` (integer, required): Target user identifier within the tenant.

##### Request Body (`UserRoleAssignment`)
| Field | Type | Required | Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- |
| `roles` | `List[UserRole]` | **Yes** | `"administrador"`, `"supervisor"`, `"auditor"` | Must contain **exactly 1** valid `UserRole` value |

```json
{
  "roles": ["supervisor"]
}
```

##### Example `curl` Request
```bash
curl -X PUT "http://localhost:8000/api/v1/users/2/roles" \
  -H "Authorization: Bearer <your_jwt_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"roles": ["supervisor"]}'
```

##### Response `200 OK` (`UserResponse`)
```json
{
  "user_id": 2,
  "tenant_id": 1,
  "first_name": "Lucía",
  "last_name": "Fernández",
  "email": "auditor@farmaciadelsol.com",
  "branch_id": 1,
  "is_active": true,
  "roles": ["supervisor"]
}
```

##### Error Responses & Domain Protections
- `400 Bad Request` (**Single-Role Constraint** — `BusinessRuleViolationException` when `roles` is empty or contains more than 1 role):
  ```json
  {
    "detail": "A user must have at least one role assigned",
    "error_type": "BusinessRuleViolation"
  }
  ```
  or
  ```json
  {
    "detail": "A user can only have one role at a time",
    "error_type": "BusinessRuleViolation"
  }
  ```
- `400 Bad Request` (**Anti-Self-Demotion Protection** — `BusinessRuleViolationException` when `user_id == claims.user_id` and `"administrador"` is not in `roles`):
  ```json
  {
    "detail": "Administrators cannot remove the administrator role from themselves",
    "error_type": "BusinessRuleViolation"
  }
  ```
- `404 Not Found` (`EntityNotFoundException` when target `user_id` does not exist in the administrator's tenant):
  ```json
  {
    "detail": "User 999 not found in this tenant",
    "error_type": "EntityNotFound"
  }
  ```
- `401 Unauthorized` / `403 Forbidden`: Missing token or non-admin role.
- `422 Unprocessable Entity`: Invalid role enum value in request body.

---

## 📦 Machine-Readable Specification

An automated, version-controlled OpenAPI JSON export is maintained directly in the repository:
- **Location**: [`docs/openapi.json`](openapi.json)
- **Specification Format**: OpenAPI 3.1.0

This specification can be imported directly into:
- **Postman**: *Import $\rightarrow$ File $\rightarrow$ Select `docs/openapi.json`*
- **Insomnia**: *Create $\rightarrow$ Import from File*
- **Swagger Editor / Swagger UI**: Directly loadable into any external Swagger generator or client SDK builder.

To re-export the specification at any time:
```bash
python -c "from backend.api.main import app; import json; open('docs/openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"
```
