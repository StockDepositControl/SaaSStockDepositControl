# Technical Implementation Plan: Frontend Web to Backend Live Integration

> **Status: Implemented & Tested (100% Complete)** — Live FastAPI backend integration is fully implemented and verified across all web routes, including `GET /api/v1/stock/kpis` for dashboard KPI aggregation, `/api/v1/reports/*` (`shrinkage`, `goods-received`, `inventory-balance`) for financial analytics, and `/api/v1/users` (`GET /api/v1/users`, `PATCH /api/v1/users/{user_id}/status`, `PUT /api/v1/users/{user_id}/roles`) for administrator user & role management.

**Reference Spec:** `specs/SPEC-frontend-backend-integration.md`

## 1. Architecture & Component Mapping

```
[ Next.js Pages (Catalog, Audit, Dashboard, Reports, Users, Login) ]
                          │
                          ▼
                  [ useDataClient() ]
                          │
                          ▼
                [ DataClientPort.ts ]
                          │
       ┌──────────────────┴──────────────────┐
       ▼                                     ▼
[ MockDataContext.tsx ]             [ ApiDataClient.ts ]
 (in-memory test data)               (live fetch adapter)
                                             │
                                             ▼
                                  [ backend: FastAPI :8000 ]
```

### Components Created / Modified:
1. `frontend-web/lib/adapters/httpClient.ts`: Fetch wrapper with JSON handling, base URL, and Bearer token header injection.
2. `frontend-web/lib/adapters/ApiDataClient.ts`: Concrete implementation of `DataClientPort` executing real HTTP calls.
3. `frontend-web/lib/context/ApiDataContext.tsx`: React Context providing `ApiDataClient`, session state, and cached query states.
4. `frontend-web/app/providers.tsx`: Configured to provide `ApiDataProvider` when `NEXT_PUBLIC_DATA_SOURCE !== 'mock'`.
5. `frontend-web/.env.local`: Environment variable `NEXT_PUBLIC_API_URL=http://localhost:8000`.
6. `backend/api/main.py` / `.env`: Verify `CORS_ORIGINS` includes `http://localhost:3000`.

---

## 2. Implementation Order

### Milestone 1: Environment & HTTP Foundation
- Add `.env.local` to `frontend-web` with `NEXT_PUBLIC_API_URL`.
- Build `httpClient.ts` with error normalization, Bearer token handling, and request typing.

### Milestone 2: Authentication & Session Adapter
- Implement `login`, `logout`, and `getCurrentUser` in `ApiDataClient`.
- Implement JWT decode utility to extract role and user claims.
- Wire session persistence via `localStorage`.

### Milestone 3: Catalog & Article Search
- Implement `getArticulos`, `getArticuloByBarcode`, and `searchArticulos` in `ApiDataClient`.
- Map backend response schemas (`items`, `total`, `pages`) to `ArticuloPublicView` / `ArticuloAdminView`.
- Verify role-based masking.

### Milestone 4: Stock Audit & Position Registration
- Implement `registerAudit` calling `POST /api/v1/stock/audit`.
- Map `AuditEntryResult` back to domain `AuditResult`.

### Milestone 5: Reports, Dashboard KPIs & User Administration
- Connect `getKPIs()` directly to `GET /api/v1/stock/kpis` (`id_deposito=1`), returning `DashboardKPIsBase` for `auditor`/`supervisor` and `DashboardKPIsAdmin` (with `montoValorizadoTotal`, `montoValorizadoAlta`, `montoValorizadoBaja`) for `administrador`.
- Connect `/reports` tabs to `/api/v1/reports/shrinkage`, `/api/v1/reports/goods-received`, and `/api/v1/reports/inventory-balance`.
- Connect `/users` administration (`getUsers`, `updateUserStatus`, `updateUserRole`) to `GET /api/v1/users`, `PATCH /api/v1/users/{user_id}/status`, and `PUT /api/v1/users/{user_id}/roles`.

### Milestone 6: Provider Wiring & End-to-End Verification
- Update `frontend-web/app/providers.tsx` to mount `ApiDataProvider`.
- Run automated Vitest test suites and end-to-end verification against the FastAPI server.

---

## 3. Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| CORS blocked by browser on credentialed requests | Frontend cannot communicate with `:8000` | Ensure `backend/.env` has `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` |
| Token expiration during user session | Unhandled 401 exceptions across pages | `httpClient` catches 401, clears token, and redirects to `/login` |
| Administrator self-lockout on `/api/v1/users` | Admin accidentally deactivates or demotes own account | Enforced both in `app/users/page.tsx` UI (disabled controls for `isMe` + optimistic rollback) and in backend `/api/v1/users/{user_id}/status` & `/roles` endpoints |
| Cost leakage to non-admin roles | Security violation | Server-side masking is maintained and strictly enforced via `mapArticleByRole` in `ApiDataClient` |

---

## 4. Verification Checkpoints

- **Checkpoint 1 (Auth):** Submitting credentials on `/login` generates valid JWT token, stores it in `localStorage`, and redirects to `/dashboard`.
- **Checkpoint 2 (Catalog):** Navigating to `/catalog` issues `GET /api/v1/articles` and renders live database articles with role-appropriate cost visibility.
- **Checkpoint 3 (Audit):** Performing an audit on `/audit` updates the database via `POST /api/v1/stock/audit` and returns calculated delta and valorization.
- **Checkpoint 4 (KPIs & Reports):** Dashboard queries `GET /api/v1/stock/kpis` and Admin accessing `/reports` views real data from `/api/v1/reports/*` analytics endpoints.
- **Checkpoint 5 (Users & Roles):** Admin accessing `/users` lists organization users (`GET /api/v1/users`), toggles active status (`PATCH /api/v1/users/{user_id}/status`), and assigns roles (`PUT /api/v1/users/{user_id}/roles`).
- **Checkpoint 6 (Build & Tests):** `npm test` (`npx vitest run`) and `npm run build` pass with zero errors.
