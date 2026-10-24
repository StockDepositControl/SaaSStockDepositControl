# Spec: Frontend Web to Backend Integration

> [!NOTE]
> **Implementation Status: Implemented** — `frontend-web` is connected to the live FastAPI backend via [`ApiDataClient.ts`](file:///home/fede/Proyectos/SaaSStockDepositControl/frontend-web/lib/adapters/ApiDataClient.ts) and [`httpClient.ts`](file:///home/fede/Proyectos/SaaSStockDepositControl/frontend-web/lib/adapters/httpClient.ts), including `/api/v1/stock/kpis` and `/api/v1/users` (`GET`, `PATCH /{user_id}/status`, `PUT /{user_id}/roles`).

## Phase 0: Scope Check & Capability Map

Connecting `frontend-web` to the live `backend` replaces in-memory mock stores (`MockDataContext`, `seed-data.ts`) with real HTTP requests against the FastAPI backend (`/api/v1/*`). Because this spans distinct operational domains (authentication, catalog queries, audit transactions, financial reports, user management), we establish the following capability map:

| Module ID | Responsibility | Depends On |
|---|---|---|
| `http-client` | Base HTTP client with error formatting, JSON serialization, and dynamic JWT Bearer token injection | — |
| `auth-integration` | JWT login (`POST /api/v1/auth/login`), claims decoding (`sub`, `role`, `tenant_id`, `branch_id`, `user_id`), session persistence (`localStorage`), logout | `http-client` |
| `articles-catalog` | Enriched article queries (`GET /api/v1/articles`), tokenized search (`GET /api/v1/articles/search`), barcode lookup (`GET /api/v1/articles/{id}`), role-aware masking | `http-client`, `auth-integration` |
| `stock-audit` | Single audit mutation (`POST /api/v1/stock/audit`), batch audit (`POST /api/v1/stock/audit/batch`), position lookup (`GET /api/v1/stock/position`), KPI aggregation (`GET /api/v1/stock/kpis`) | `http-client`, `auth-integration` |
| `reports-dashboard` | Administrative financial reports (`shrinkage`, `goods-received`, `inventory-balance`) and KPI metrics derivation | `http-client`, `auth-integration` |
| `users-management` | Administrator user listing (`GET /api/v1/users`), status toggle (`PATCH /api/v1/users/{id}/status`), and role assignment (`PUT /api/v1/users/{id}/roles`) | `http-client`, `auth-integration` |
| `provider-switch` | Adapter implementation of `DataClientPort` (`ApiDataClient`) and environment switch (`NEXT_PUBLIC_DATA_SOURCE`) | All modules |

**Build Order:** `http-client` → `auth-integration` → `articles-catalog` → `stock-audit` → `reports-dashboard` → `users-management` → `provider-switch`.

---

## 1. Objective

Connect the Next.js `frontend-web` application directly to the FastAPI `backend` API to enable end-to-end integration testing. 
- Eliminate reliance on static in-memory seed data (`frontend-web/lib/mocks/seed-data.ts`).
- Respect Hexagonal Architecture: Implement `ApiDataClient` satisfying `DataClientPort` without rewriting UI components or pages.
- Enforce Role-Based Access Control (RBAC): Maintain structural field stripping (e.g. `pcio_com_siva` cost hiding) both on the server response handling and in client state.
- Ensure seamless local developer experience with environment configuration and automated fallback/diagnostics.

---

## 2. Tech Stack

- **Frontend:** Next.js 16 (App Router), React 19, TypeScript 5, Tailwind CSS v4.
- **Backend:** FastAPI, Python 3.12, SQLAlchemy 2.0 (async), MariaDB / SQLite, PyJWT.
- **Protocol:** REST JSON over HTTP, Bearer JWT Authentication (`HS256`).
- **Storage:** Browser `localStorage` for JWT tokens and active tenant session caching.

---

## 3. Commands

- **Backend Development Server:**
  ```bash
  backend/venv/bin/uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Backend Test Suite:**
  ```bash
  backend/venv/bin/pytest backend/tests/api -q
  ```
- **Frontend Development Server:**
  ```bash
  cd frontend-web && npm run dev
  ```
- **Frontend Build & Typecheck:**
  ```bash
  cd frontend-web && npm run build
  ```
- **Database Seed (Idempotent Test Data):**
  ```bash
  backend/venv/bin/python -m backend.scripts.seed
  ```

---

## 4. Project Structure

```
frontend-web/
├── lib/
│   ├── ports/
│   │   └── DataClientPort.ts          # Core interface contract
│   ├── adapters/
│   │   ├── ApiDataClient.ts          # Concrete HTTP implementation of DataClientPort
│   │   ├── httpClient.ts             # Shared fetch wrapper with auth header injection
│   │   └── __tests__/
│   │       └── ApiDataClient.test.ts # Contract & adapter unit tests
│   ├── context/
│   │   └── ApiDataContext.tsx        # Real React Context provider for backend data
│   ├── hooks/
│   │   └── useDataClient.ts          # Consumes current active data provider
│   ├── mocks/
│   │   ├── MockDataContext.tsx       # Preserved for offline unit testing/demo mode
│   │   └── seed-data.ts
│   └── types/
│       ├── domain.ts                 # Domain models
│       └── api.ts                    # Backend DTO response definitions
├── app/
│   ├── providers.tsx                 # Instantiates ApiDataProvider or MockDataProvider
│   ├── login/page.tsx
│   ├── catalog/page.tsx
│   ├── audit/page.tsx
│   ├── dashboard/page.tsx
│   ├── reports/page.tsx
│   ├── users/page.tsx
│   └── debug/page.tsx
└── .env.local                        # NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 5. Code Style & Architecture Conventions

### Hexagonal Architecture & Port Preservation
The application already defines `DataClientPort`. The integration **must not** bypass this port by calling `fetch()` directly inside UI components (like `CatalogPage` or `AuditPage`). Instead:
1. `ApiDataClient` implements `DataClientPort`.
2. All page components continue to invoke methods via `useDataClient()`.

### Code Example: `ApiDataClient.ts`
```typescript
import { DataClientPort } from "../ports/DataClientPort";
import { UserRole, ArticuloPublicView, ArticuloAdminView, AuditEntry, AuditResult } from "../types/domain";
import { httpClient } from "./httpClient";

export class ApiDataClient implements DataClientPort {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  async getArticulos(role?: UserRole): Promise<(ArticuloPublicView | ArticuloAdminView)[]> {
    const data = await httpClient.get<{ items: (ArticuloPublicView | ArticuloAdminView)[] }>(
      `${this.baseUrl}/api/v1/articles?limit=100`
    );
    return data.items;
  }

  async registerAudit(entry: AuditEntry): Promise<AuditResult> {
    return await httpClient.post<AuditResult>(`${this.baseUrl}/api/v1/stock/audit`, {
      id_articulo: entry.id_articulo,
      stock_fisico_contado: entry.stock_fisico_contado,
      lote: entry.lote ?? null,
      observation: entry.observation ?? null,
    });
  }

  // ... remaining DataClientPort methods
}
```

### JWT Claims Structure
Decoded from FastAPI JWT payload:
- `sub`: User email
- `role`: Role string (`"administrador"`, `"supervisor"`, `"auditor"`)
- `tenant_id`: Tenant ID integer
- `branch_id`: Branch ID integer
- `user_id` / `id_usuario`: User ID integer

---

## 6. Testing Strategy

1. **Contract Testing:** Verify each endpoint path and payload matches the backend FastAPI schema:
   - `POST /api/v1/auth/login` → `{ access_token, token_type }`
   - `GET /api/v1/articles` → `{ items: [...], total, page, limit, pages }`
   - `GET /api/v1/articles/search?query=...` → `[...]`
   - `POST /api/v1/stock/audit` → `AuditEntryResult`
   - `GET /api/v1/stock/kpis` → `DashboardKPIsResponse`
   - `GET /api/v1/reports/*` → strictly validated against report schemas
   - `GET /api/v1/users`, `PATCH /api/v1/users/{id}/status`, `PUT /api/v1/users/{id}/roles` → `UserResponse`
2. **CORS Validation:** Verify browser pre-flight (`OPTIONS`) succeeds when Next.js (`http://localhost:3000`) sends `Authorization: Bearer <token>`.
3. **RBAC Field Stripping:** Confirm non-admin accounts never receive or render `pcio_com_siva` or unit costs.
4. **Resilience & Error Handling:** Verify that network disconnections or expired tokens trigger clean UI error alerts rather than unhandled promise rejections.

---

## 7. Boundaries

- **Always do:**
  - Route all API calls through `DataClientPort` via `ApiDataClient`.
  - Store JWT tokens securely and clean them up on 401 Unauthorized or manual logout.
  - Set `Authorization: Bearer <token>` on all authenticated backend calls.
  - Support a clean fallback toggle via `NEXT_PUBLIC_DATA_SOURCE=api | mock`.
- **Ask first:**
  - If new backend endpoints are needed.
  - If changing CORS origins or authentication token expiration policies.
- **Never do:**
  - Hardcode authentication tokens or API URLs directly in UI components.
  - Remove existing mock files (`MockDataContext.tsx`, `seed-data.ts`) until all E2E flows are validated against the live server.
  - Expose cost fields (`pcio_com_siva`) to Auditor or Supervisor roles.

---

## 8. Success Criteria

- [x] Logging in on `/login` with real credentials (`user_0@example.com` / `password123`) authenticates via `POST /api/v1/auth/login` and receives a valid JWT.
- [x] Catalog screen (`/catalog`) displays articles loaded from `GET /api/v1/articles` instead of `INITIAL_ARTICULOS_SEED`.
- [x] Submitting a stock audit on `/audit` calls `POST /api/v1/stock/audit`, updates theoretical stock in the backend, and records the audit event.
- [x] Reports screen (`/reports`) pulls real data from `/api/v1/reports/shrinkage`, `goods-received`, and `inventory-balance`.
- [x] Users screen (`/users`) pulls and mutates real tenant users via `/api/v1/users`, `/api/v1/users/{id}/status`, and `/api/v1/users/{id}/roles`.
- [x] Switching roles via login respects backend RBAC (Supervisor/Auditor cannot view costs or access `/reports` or `/users`).
- [x] Next.js production build (`npm run build`) completes with 0 TypeScript or lint errors.

---

## 9. Resolved Endpoint Gaps & Mitigations

1. **User Management Endpoint (Resolved):**
   - *Resolution:* `backend/api/v1/users.py` now exposes `GET /api/v1/users`, `PATCH /api/v1/users/{user_id}/status`, and `PUT /api/v1/users/{user_id}/roles`, and `ApiDataClient` calls them directly.
2. **Dashboard KPI Endpoint (Resolved):**
   - *Resolution:* `backend/api/v1/stock.py` exposes `GET /api/v1/stock/kpis` (`StockKPIService`), and `ApiDataClient.getDashboardKPIs()` consumes it directly.
3. **CORS Allow Origins (Resolved):**
   - *Resolution:* `backend/api/main.py` configures `CORSMiddleware` and `docker/nginx/nginx.conf` provides unified same-origin reverse proxy routing on `NGINX_PORT` (`8080`).
