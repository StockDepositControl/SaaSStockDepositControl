# Implementation Tasks: Catalog Server-Side Pagination and Search

- **Spec Reference:** `specs/catalog-server-pagination-search/spec.md` (`Status` must be `Approved` before execution)
- **Delivery Strategy:** Vertical slices (`<= 400` changed lines per commit), TDD (`Red -> Green -> Refactor`), dependency-ordered.

---

## Task Breakdown

### `T1`: Backend Barcode Search & Families Listing Endpoint
- **Covers Spec IDs:** `S2`, `S3`, `S4`
- **Dependencies:** None
- **Route:** `inline`
- **Risk Tier:** `low`
- **Target Modules / Files:**
  - `backend/adapters/repositories/article_repository.py`
  - `backend/app/articles/ports.py`
  - `backend/app/articles/services.py`
  - `backend/api/v1/articles.py`
  - `backend/tests/api/test_articles_routes.py`
- **Acceptance Criteria:**
  - [ ] RED tests added in `tests/api/test_articles_routes.py` verifying:
    - `GET /api/v1/articles/families` returns list of active product families.
    - `GET /api/v1/articles?search=<barcode>` successfully matches articles by barcode.
  - [ ] Minimal implementation passes GREEN:
    - Barcode matching subquery added to `SQLAlchemyArticleRepository.list_articles`.
    - `list_families` added to repository port, service, and exposed at `GET /api/v1/articles/families`.
  - [ ] Differential checks clean: all 377+ backend tests pass with zero lint errors.
- **Verification Command:** `pytest tests/api/test_articles_routes.py tests/domain/test_article_search_service.py && ruff check . && ruff format --check .`
- **Status:** `[x] done`

---

### `T2`: Frontend Port, Types & Adapters (ApiDataClient & MockDataContext)
- **Covers Spec IDs:** `S1`, `S4`, `S5`, `S7`
- **Dependencies:** `T1`
- **Route:** `inline`
- **Risk Tier:** `low`
- **Target Modules / Files:**
  - `frontend-web/lib/types/api.ts`
  - `frontend-web/lib/types/domain.ts`
  - `frontend-web/lib/ports/DataClientPort.ts`
  - `frontend-web/lib/adapters/ApiDataClient.ts`
  - `frontend-web/lib/mocks/MockDataContext.tsx`
  - `frontend-web/lib/adapters/ApiDataClient.test.ts`
- **Acceptance Criteria:**
  - [ ] Add `ArticleCatalogQuery`, `PaginatedArticlesResult`, and `ArticleFamily` interfaces in `api.ts` and `domain.ts`.
  - [ ] Add `getPaginatedArticles` and `getFamilies` methods to `DataClientPort`.
  - [ ] RED tests in `ApiDataClient.test.ts` verifying `getPaginatedArticles` query serialization, RBAC role-based field mapping, and `getFamilies` fetching.
  - [ ] Implement `getPaginatedArticles` and `getFamilies` in `ApiDataClient` (hitting `/api/v1/articles` and `/api/v1/articles/families`).
  - [ ] Implement `getPaginatedArticles` and `getFamilies` in `MockDataContext` for seamless mock parity.
  - [ ] GREEN tests and clean typecheck.
- **Verification Command:** `npx vitest run lib/adapters/ApiDataClient.test.ts && npx tsc --noEmit`
- **Status:** `[x] done`

---

### `T3`: Frontend Server-Driven Hook `useArticles`
- **Covers Spec IDs:** `S1`, `S3`, `S4`, `S5`, `S6`
- **Dependencies:** `T2`
- **Route:** `inline`
- **Risk Tier:** `medium` (state machine, debouncing & race-condition cancellation)
- **Target Modules / Files:**
  - `frontend-web/lib/hooks/useArticles.ts`
  - `frontend-web/lib/hooks/useArticles.test.ts`
- **Acceptance Criteria:**
  - [ ] RED tests in `useArticles.test.ts` verifying:
    - Setting `page` triggers fetch with updated `page`.
    - Setting `search` debounces (250ms) and resets `page` to 1.
    - Setting `family` or `status` updates query params and resets `page` to 1.
    - Out-of-order / superseded responses are safely discarded.
  - [ ] Implement query state controls (`page`, `limit`, `search`, `id_familia`, `status`), debounced search, and family fetching in `useArticles`.
  - [ ] Backward compatibility preserved for unconfigured callers (e.g., reports tab).
  - [ ] GREEN tests and clean typecheck.
- **Verification Command:** `npx vitest run lib/hooks/useArticles.test.ts && npx tsc --noEmit`
- **Status:** `[ ] pending`

---

### `T4`: Catalog UI & `DataTable` Server-Side Integration
- **Covers Spec IDs:** `S1`, `S2`, `S3`, `S4`, `S5`
- **Dependencies:** `T3`
- **Route:** `inline`
- **Risk Tier:** `low`
- **Target Modules / Files:**
  - `frontend-web/components/ui/DataTable.tsx`
  - `frontend-web/app/catalog/page.tsx`
  - `frontend-web/app/catalog/page.test.tsx`
- **Acceptance Criteria:**
  - [ ] RED test in `page.test.tsx` verifying:
    - Total count displayed reflects server response (e.g., `500 artículos`).
    - Pagination buttons invoke `setPage`.
    - Search input invokes `setSearch`.
    - Family filter dropdown renders fetched families and invokes `setFamily`.
  - [ ] Refactor `DataTable.tsx` to accept server pagination and filter props instead of in-memory slicing.
  - [ ] Update `CatalogPage` (`app/catalog/page.tsx`) to wire `useArticles` server controls to `DataTable`.
  - [ ] Verify pages 1 through 50 and search for "ART" items succeed.
  - [ ] All frontend test suites pass, TypeScript zero errors, ESLint zero errors.
- **Verification Command:** `npm test && npx tsc --noEmit && npm run lint`
- **Status:** `[ ] pending`
