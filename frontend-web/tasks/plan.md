# Technical Implementation Plan: Frontend Web to Backend Live Integration

**Reference Spec:** `specs/SPEC-frontend-backend-integration.md`

## 1. Architecture & Component Mapping

```
[ Next.js Pages (Catalog, Audit, Dashboard, Reports, Login) ]
                          │
                          ▼
                  [ useDataClient() ]
                          │
                          ▼
                [ DataClientPort.ts ]
                          │
       ┌──────────────────┴──────────────────┐
       ▼                                     ▼
[ MockDataClient.ts ]               [ ApiDataClient.ts ]
 (in-memory test data)               (live fetch adapter)
                                             │
                                             ▼
                                  [ backend: FastAPI :8000 ]
```

### Components to Create / Modify:
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

### Milestone 5: Reports & Dashboard KPIs
- Connect `getKPIs()` and report tabs to `/api/v1/reports/shrinkage`, `goods-received`, and `inventory-balance`.
- Compute dashboard counters dynamically from real backend reports.

### Milestone 6: Provider Wiring & End-to-End Verification
- Update `frontend-web/app/providers.tsx` to mount `ApiDataProvider`.
- Run end-to-end smoke test against the live running FastAPI server.

---

## 3. Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| CORS blocked by browser on credentialed requests | Frontend cannot communicate with `:8000` | Ensure `backend/.env` has `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` |
| Token expiration during user session | Unhandled 401 exceptions across pages | `httpClient` catches 401, clears token, and redirects to `/login` |
| Missing `/api/v1/users` endpoint | User management tab might fail | `ApiDataClient.getUsers()` falls back gracefully to active user info |
| Cost leakage to non-admin roles | Security violation | Ensure server-side masking is maintained and sanitized in `ApiDataClient` |

---

## 4. Verification Checkpoints

- **Checkpoint 1 (Auth):** Submitting credentials on `/login` generates valid JWT token, stores it in `localStorage`, and redirects to `/dashboard`.
- **Checkpoint 2 (Catalog):** Navigating to `/catalog` issues `GET /api/v1/articles` and renders live database articles.
- **Checkpoint 3 (Audit):** Performing an audit on `/audit` updates the database and returns calculated delta and valorization.
- **Checkpoint 4 (Reports):** Admin accessing `/reportes` views real data from backend analytics endpoints.
- **Checkpoint 5 (Build):** `npm run build` passes with zero errors.
