### ASSUMPTIONS I'M MAKING:
1. The new dedicated KPI aggregation endpoint will be hosted under `backend/api/v1/stock.py` as `GET /api/v1/stock/kpis` (or a dedicated `backend/api/v1/dashboard.py`), secured by standard tenant claims and active work session resolution.
2. Calculations for `total_articulos` and `out_of_stock_count` are resolved against the catalog and `stock_por_deposito` tables scoped to the active tenant/deposit.
3. Calculations for `auditados`, `discrepancias_alta`, `discrepancias_baja`, and `monto_valorizado_baja` are aggregated in the database directly from `audit_records` for the active work session (or current operational day).
4. `useArticles()` will be completely removed from `app/dashboard/page.tsx`, eliminating the heavy `GET /api/v1/articles?page=1&limit=100` catalog fetch on login/dashboard.
5. In `frontend-web/lib/adapters/ApiDataClient.ts`, `getKPIs()` will make a single request to `GET /api/v1/stock/kpis` instead of firing two dummy pagination calls (`limit=1` and `limit=1&fue_auditado=true`).
6. `MockDataClient` and domain types (`DashboardKPIsBase`, `DashboardKPIsAdmin`) will be updated to include `outOfStockCount` directly, maintaining backward compatibility with tests.

---

# Spec: Dedicated Dashboard KPI Aggregation Endpoint & Catalog Overfetch Elimination

## 1. Objective
Eliminate the architectural anti-pattern of client-side metrics aggregation via paginated catalog endpoints. 

Upon user login and dashboard access, the web client currently executes three separate requests against `/api/v1/articles`:
- Two `limit=1` queries used as a workaround to read the `total` count header for total and audited articles.
- One `limit=100` query fetching full product and barcode records across all user roles, used solely by the Administrator view to compute an out-of-stock count on the client.

This specification defines a single, tenant-scoped, role-aware database aggregation endpoint (`GET /api/v1/stock/kpis`) and aligns the frontend data adapter and dashboard page to consume it, reducing dashboard network roundtrips from 3 to 1 and eliminating unnecessary payload transfer.

---

## 2. Tech Stack
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, MariaDB 10.11 / MySQL.
- **Frontend:** Next.js 16.2 (App Router), React 19, TypeScript 5.x, Vitest 2.1, Tailwind CSS.
- **Architecture:** Hexagonal / Clean Architecture (Port & Adapters) with multi-tenant database isolation.

---

## 3. Commands
- **Backend Tests:** `pytest tests/api/test_stock_kpis.py tests/unit/test_stock_kpis_service.py` (inside `backend/`)
- **Backend Dev Server:** `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload` (inside `backend/`)
- **Frontend Tests:** `npm test` or `npx vitest run lib/hooks/useKPIs.test.ts lib/adapters/ApiDataClient.test.ts app/dashboard/page.test.tsx` (inside `frontend-web/`)
- **Frontend Typecheck & Build:** `npm run build` (inside `frontend-web/`)
- **Frontend Dev Server:** `npm run dev` (inside `frontend-web/`)

---

## 4. Project Structure & Affected Surfaces

```
backend/
├── app/
│   └── movements/
│       ├── ports.py                    → [MODIFY] Add get_dashboard_kpis method to AuditRepositoryPort or StockRepositoryPort
│       ├── schemas.py                  → [MODIFY] Define DashboardKPIsResponse schema (base & admin fields)
│       └── services.py                 → [MODIFY] Implement get_dashboard_kpis logic aggregating counts & amounts
├── adapters/
│   └── repositories/
│       └── stock_repository.py         → [MODIFY] Execute SQL aggregation queries (COUNT, SUM) on stock_por_deposito & audit_records
└── api/
    └── v1/
        └── stock.py                    → [NEW ENDPOINT] Add GET /api/v1/stock/kpis with role filtering and deposit param

frontend-web/
├── lib/
│   ├── types/
│   │   └── domain.ts                   → [MODIFY] Add outOfStockCount to DashboardKPIsBase
│   ├── adapters/
│   │   ├── ApiDataClient.ts            → [MODIFY] Refactor getKPIs() to call GET /api/v1/stock/kpis (single request)
│   │   └── ApiDataClient.test.ts       → [MODIFY] Update tests to mock/assert GET /api/v1/stock/kpis
│   └── mocks/
│       └── MockDataContext.tsx         → [MODIFY] Add outOfStockCount to mock KPIs
└── app/
    └── dashboard/
        ├── page.tsx                    → [MODIFY] Remove useArticles(); read outOfStockCount from kpis
        └── page.test.tsx               → [MODIFY] Update mock kpis to supply outOfStockCount; verify no useArticles calls
```

---

## 5. Code Style & Architecture

### 5.1 Backend: Single-Query Aggregation Pattern
Avoid in-memory filtering or looping over entity lists in Python. Use SQLAlchemy `func.count` and `func.coalesce` with index-backed columns.

```python
# backend/app/movements/schemas.py
class DashboardKPIsResponse(BaseModel):
    total_articulos: int
    auditados: int
    pendientes: int
    porcentaje_avance: int
    discrepancias_alta: int
    discrepancias_baja: int
    sin_accion: int
    out_of_stock_count: int
    monto_valorizado_baja: Optional[Decimal] = None
    monto_valorizado_alta: Optional[Decimal] = None
```

```python
# backend/api/v1/stock.py
@router.get(
    "/kpis",
    response_model=DashboardKPIsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated stock and audit KPIs for dashboard",
)
async def get_dashboard_kpis(
    id_deposito: int = Query(1, ge=1, description="Warehouse ID"),
    claims: dict = Depends(get_current_user_claims),
    service: StockKPIService = Depends(get_stock_kpi_service),
    work_session_service: WorkSessionService = Depends(get_work_session_service),
) -> DashboardKPIsResponse:
    tenant_id = str(claims.get("tenant_id", "1"))
    branch_id = claims.get("branch_id") or 1
    session = await work_session_service.get_or_create_active_session(tenant_id=tenant_id, branch_id=branch_id)
    user_role = claims.get("role", "").lower()
    
    return await service.get_dashboard_kpis(
        tenant_id=tenant_id,
        branch_id=branch_id,
        deposit_id=id_deposito,
        session_id=session.session_id,
        is_admin=(user_role == "administrador"),
    )
```

### 5.2 Frontend: Zero-Overfetch Consumption Pattern

```typescript
// frontend-web/app/dashboard/page.tsx
export default function DashboardPage() {
  const { currentUser, currentRole } = useDataClient();
  const { kpis } = useKPIs();
  const { auditLogs } = useAuditLogs();
  const isAdmin = currentRole === UserRole.ADMINISTRADOR;
  const adminKPIs = isAdmin ? (kpis as DashboardKPIsAdmin) : null;

  // OUT-OF-STOCK ALERT: Sourced directly from backend DB aggregation
  const outOfStockCount = kpis.outOfStockCount ?? 0;
  // ...
}
```

---

## 6. Testing Strategy

### Backend
- **Unit Test (`tests/unit/test_stock_kpis_service.py`)**:
  - Test calculation of `pendientes` = `max(0, total_articulos - auditados)`.
  - Test calculation of `porcentaje_avance` with 0 total items (avoid division by zero).
  - Test role filtering: non-admin requests mask or omit `monto_valorizado_baja`.
- **Integration/API Test (`tests/api/test_stock_kpis_api.py`)**:
  - Verify `GET /api/v1/stock/kpis` responds 200 with valid JWT.
  - Verify response time is < 50ms with 10,000 seeded articles and 1,000 audit records.

### Frontend
- **Adapter Unit Test (`lib/adapters/ApiDataClient.test.ts`)**:
  - Assert `client.getKPIs()` executes exactly ONE HTTP call to `/api/v1/stock/kpis`.
  - Assert it maps `outOfStockCount` and financial amounts accurately.
- **Component Test (`app/dashboard/page.test.tsx`)**:
  - Assert `DashboardPage` does NOT import or execute `useArticles()`.
  - Assert out-of-stock card renders `kpis.outOfStockCount` when role is Administrator.

---

## 7. Boundaries

- **Always:**
  - Scope all SQL aggregate queries strictly by `tenant_id`, `branch_id`, and `id_deposito`.
  - Return financial amounts (`monto_valorizado_baja`) only to authenticated administrators.
  - Keep domain ports decoupled from framework dependencies.
- **Ask First:**
  - If changing the table indexes on `stock_por_deposito` or `audit_records`.
  - If redefining the operational window for KPIs (e.g. active work session vs 24-hour rolling window).
- **Never:**
  - Never run `SELECT * FROM articulos` or scan full tables in Python to compute counters.
  - Never import `useArticles` into the dashboard page again.
  - Never expose financial loss amounts to Auditor or Supervisor roles.

---

## 8. Success Criteria

1. **Request count reduction:** Opening `/dashboard` triggers at most 1 API request for KPIs (`GET /api/v1/stock/kpis`) instead of 3 requests (`limit=1`, `limit=1&fue_auditado=true`, `limit=100`).
2. **Payload reduction:** The response size for dashboard KPIs is < 1 KB (down from ~50 KB+ caused by 100 article records).
3. **Calculation accuracy:** `outOfStockCount` reflects 100% of the warehouse catalog, regardless of whether there are 50, 500, or 50,000 items.
4. **Role isolation:** Auditor and Supervisor logins never fetch or transfer unneeded catalog rows or financial loss figures.
5. **Zero test regressions:** All existing Vitest and Pytest test suites continue to pass.

---

## 9. Architectural Decisions (Resolved)
- **Operational Scope:** Dashboard audit counters (`auditados`, `discrepancias_alta/baja`, `monto_valorizado_baja`) are strictly scoped to the **current active work session** (`session_id`).
- **Reports Module Separation:** Calendar day consolidation across all sessions remains exclusively within the dedicated Reports Module (`/reports` and `/api/v1/reports/*`).
