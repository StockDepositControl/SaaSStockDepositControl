# Implementation Tasks: Auditor Attribution in Item Catalog

- **Spec Reference:** `specs/catalog-audited-by-attribution/spec.md` (`Status: Approved`)
- **Delivery Strategy:** Vertical slices (`<= 400` changed lines per commit), TDD (`Red -> Green -> Refactor`), dependency-ordered.

---

## Task Breakdown

### `T1`: Analytics Repository Batch User Resolution & Domain Models
- **Covers Spec IDs:** `S1`, `S4`
- **Dependencies:** None
- **Route:** `inline`
- **Risk Tier:** `low`
- **Target Modules / Files:**
  - `backend/app/movements/ports.py`
  - `backend/adapters/repositories/audit_repository.py`
  - `backend/app/movements/services.py`
  - `backend/app/articles/models.py`
  - `backend/tests/db/test_audit_repository.py` (moved from `tests/adapters/`: in-memory DB fixture lives in `tests/db/conftest.py`)
  - `backend/tests/domain/test_stock_lookup_batch.py`
- **Acceptance Criteria:**
  - [x] RED test: write a test in `tests/db/test_audit_repository.py` for `get_latest_audit_users_for_articles` asserting mapping `{article_code: user_id}` for latest audit in session.
  - [x] GREEN: implement `get_latest_audit_users_for_articles` in `SQLAlchemyAuditRepository` and `AuditRepositoryPort`.
  - [x] GREEN: add `get_session_auditors_batch` in `StockLookupService`.
  - [x] GREEN: add `audited_by: Optional[str] = None` to `ArticuloBase`, `Articulo`, `ArticuloPublicOut`, `ArticuloAdminOut` in `backend/app/articles/models.py`.
- **Verification Command:**
  ```bash
  cd backend && pytest tests/db/test_audit_repository.py tests/domain/test_article_catalog_orchestrator.py && ruff check . && ruff format --check .
  ```
- **Status:** `[x] done`

---

### `T2`: Domain Orchestration & API Routing (Cross-Context User Name Enrichment)
- **Covers Spec IDs:** `S2`, `S3`
- **Dependencies:** `T1`
- **Route:** `inline`
- **Risk Tier:** `medium` (touches cross-context orchestrator and router dependency injection)
- **Target Modules / Files:**
  - `backend/app/articles/orchestrator.py`
  - `backend/api/dependencies/services.py`
  - `backend/api/v1/articles.py`
  - `backend/tests/domain/test_article_catalog_orchestrator.py`
  - `backend/tests/api/test_articles_routes.py`
- **Acceptance Criteria:**
  - [x] RED test: write tests in `test_article_catalog_orchestrator.py` asserting `audited_by` is enriched with auditor's full name from `user_repository`.
  - [x] RED test: write test in `test_articles_routes.py` verifying `GET /api/v1/articles` serializes `"audited_by"`.
  - [x] GREEN: inject `user_repository` into `ArticleCatalogOrchestrator` and resolve user names for audited articles.
  - [x] GREEN: wire `SQLAlchemyUserRepository` in `get_article_catalog_orchestrator` and pass `tenant_id` in `backend/api/v1/articles.py`.
- **Verification Command:**
  ```bash
  cd backend && pytest tests/domain/test_article_catalog_orchestrator.py tests/api/test_articles_routes.py && ruff check . && ruff format --check .
  ```
- **Status:** `[x] done`

---

### `T3`: Frontend Domain Types, Adapters & Mock State
- **Covers Spec IDs:** `S6`
- **Dependencies:** None (can run in parallel with or after T1)
- **Route:** `inline`
- **Risk Tier:** `low`
- **Target Modules / Files:**
  - `frontend-web/lib/types/domain.ts`
  - `frontend-web/lib/types/api.ts`
  - `frontend-web/lib/adapters/mappers.ts`
  - `frontend-web/lib/adapters/mappers.test.ts`
  - `frontend-web/lib/mocks/seed-data.ts`
  - `frontend-web/lib/mocks/MockDataContext.tsx`
- **Acceptance Criteria:**
  - [x] RED test: update `mappers.test.ts` to assert `raw.audited_by` is correctly mapped to `domain.audited_by`.
  - [x] GREEN: add `audited_by?: string | null;` to `ArticuloBase` and `ApiArticuloBase`.
  - [x] GREEN: map `audited_by: raw.audited_by ?? null` in `mapToArticuloPublicView`.
  - [x] GREEN: populate `audited_by: "Usuario Test (Auditor)"` for audited items in `seed-data.ts`.
  - [x] GREEN: update `MockDataContext.tsx` `registerAudit` to set `audited_by: currentUser?.name || "Auditor"`.
- **Verification Command:**
  ```bash
  cd frontend-web && npx vitest run lib/adapters/mappers.test.ts && npx tsc --noEmit && npm run lint
  ```
- **Status:** `[x] done`

---

### `T4`: Frontend DataTable Supervisor Attribution & Page Tests
- **Covers Spec IDs:** `S5`
- **Dependencies:** `T2`, `T3`
- **Route:** `inline`
- **Risk Tier:** `low`
- **Target Modules / Files:**
  - `frontend-web/components/ui/DataTable.tsx`
  - `frontend-web/app/catalog/page.test.tsx`
- **Acceptance Criteria:**
  - [x] RED test: add test in `frontend-web/app/catalog/page.test.tsx` verifying that under `UserRole.SUPERVISOR`, an article with `fue_auditado: true` and `audited_by: "Carlos Auditor"` renders `"Carlos Auditor"` (with avatar `"CA"`) in the "AUDITADO POR" column, even when the logged-in supervisor is `"Silvia Supervisora"`.
  - [x] GREEN: remove `getAuditorForArticle` in `DataTable.tsx`. Render avatar and name from `art.audited_by` for desktop table and mobile card view.
  - [x] Regression check: all tests in `frontend-web` pass.
- **Verification Command:**
  ```bash
  cd frontend-web && npx vitest run app/catalog/page.test.tsx && npm test && npx tsc --noEmit && npm run lint
  ```
- **Status:** `[x] done`
