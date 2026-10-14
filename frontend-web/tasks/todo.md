# Tasks: Frontend Web to Backend Live Integration

- [x] Task 1: Environment & CORS Configuration
  - Acceptance: Backend allows requests from `http://localhost:3000` with credentials (configured via root `.env`); frontend has `.env.local` pointing to backend `http://localhost:8000`.
  - Verify: Curl or OPTIONS pre-flight test to `http://localhost:8000/api/v1/health` with `Origin: http://localhost:3000`.
  - Files: `.env`, `frontend-web/.env.local`, `frontend-web/.env.example`.

- [x] Task 2: Core HTTP Client & JWT Interceptor
  - Acceptance: Reusable `httpClient` handles base URL, request serialization, error normalization, and Bearer token injection from `localStorage`.
  - Verify: Unit tests in `httpClient.test.ts` pass verifying Authorization header presence, query params, and 401 handling.
  - Files: `frontend-web/lib/adapters/httpClient.ts`, `frontend-web/lib/adapters/httpClient.test.ts`.

- [x] Task 3: Authentication & Session Adapter (`ApiDataClient`)
  - Acceptance: `ApiDataClient.login()` authenticates against `POST /api/v1/auth/login`, decodes JWT claims (`sub`, `role`, `tenant_id`, `branch_id`, `user_id`), and stores token. `logout()` clears state.
  - Verify: Unit tests in `jwt.test.ts` and `ApiDataClient.test.ts` pass.
  - Files: `frontend-web/lib/adapters/ApiDataClient.ts`, `frontend-web/lib/utils/jwt.ts`, `frontend-web/lib/types/api.ts`.

- [x] Task 4: Articles & Catalog Integration
  - Acceptance: `ApiDataClient.getArticulos()`, `searchArticulos()`, and `getArticuloByBarcode()` fetch real articles from `GET /api/v1/articles` and `GET /api/v1/articles/search`. RBAC field stripping strictly enforced via whitelist mappers.
  - Verify: Unit tests in `mappers.test.ts` verifying omission of `pcio_com_siva` for non-admin roles; catalog renders.
  - Files: `frontend-web/lib/adapters/ApiDataClient.ts`, `frontend-web/lib/adapters/mappers.ts`.

- [x] Task 5: Stock Audit & Physical Count Mutation
  - Acceptance: `ApiDataClient.registerAudit()` submits `POST /api/v1/stock/audit` with physical count, returning computed delta, action type, and voucher classification.
  - Verify: Unit tests in `ApiDataClient.test.ts` pass; audit mutation updates context state and audit logs.
  - Files: `frontend-web/lib/adapters/ApiDataClient.ts`, `frontend-web/lib/adapters/mappers.ts`.

- [x] Task 6: Reports & Dashboard Financial Integration
  - Acceptance: `ApiDataClient` fetches live report data from `/api/v1/reports/shrinkage`, `goods-received`, and `inventory-balance`, deriving KPIs for `/dashboard` and `/reportes`.
  - Verify: Unit tests pass; role protection enforced.
  - Files: `frontend-web/lib/adapters/ApiDataClient.ts`, `frontend-web/lib/types/api.ts`.

- [x] Task 7: Context Provider Wiring & Build Verification
  - Acceptance: `frontend-web/app/providers.tsx` supplies `ApiDataProvider` by default with `NEXT_PUBLIC_DATA_SOURCE=mock` toggle support. `npm run build` succeeds without type errors.
  - Verify: `npm run build` succeeds with 0 errors across all routes; 16 unit tests pass cleanly.
  - Files: `frontend-web/lib/context/ApiDataContext.tsx`, `frontend-web/lib/context/DataContext.tsx`, `frontend-web/app/providers.tsx`, `frontend-web/lib/hooks/useDataClient.ts`.
