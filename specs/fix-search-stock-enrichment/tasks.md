# Implementation Tasks: Article Search Stock Enrichment

- **Spec Reference:** `specs/fix-search-stock-enrichment/spec.md` (`Status: Approved`)
- **Delivery Strategy:** Vertical slices (`<= 400` changed lines), TDD (`Red -> Green -> Refactor`), token-minimal prompts for Claude Code.

---

## Task Breakdown

### `T1`: Domain Orchestrator `search_and_enrich_articles` & Unit Tests
- **Covers Spec IDs:** `S1`, `S4`
- **Dependencies:** None
- **Route:** `inline`
- **Risk Tier:** `low` (Pure domain service logic, in-memory mocks, zero external network/DB)
- **Allowed Edit Surfaces:**
  - `backend/app/articles/orchestrator.py`
  - `backend/tests/domain/test_article_catalog_orchestrator.py`
- **Acceptance Criteria:**
  - [x] **RED:** Add test in `test_article_catalog_orchestrator.py` calling `orchestrator.search_and_enrich_articles("Ibu", deposit_id=1, active_session_id=10)` expecting domain `Articulo` list with `stock_real` populated from `stock_lookup_service.get_effective_stocks_batch`.
  - [x] **RED:** Add test verifying empty search query results return `[]` without calling `stock_lookup_service`.
  - [x] **GREEN:** Implement `search_and_enrich_articles` in `ArticleCatalogOrchestrator` ([`backend/app/articles/orchestrator.py`](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/app/articles/orchestrator.py)).
- **Verification Command:** `pytest tests/domain/test_article_catalog_orchestrator.py`
- **Status:** `[x] done`

---

### `T2`: API Router `search_articles` Orchestrator Wiring
- **Covers Spec IDs:** `S1`, `S3`
- **Dependencies:** `T1`
- **Route:** `inline`
- **Risk Tier:** `low` (FastAPI dependency injection and query parameter addition)
- **Allowed Edit Surfaces:**
  - `backend/api/v1/articles.py`
  - `backend/tests/api/test_articles_routes.py`
- **Acceptance Criteria:**
  - [x] **RED:** Update route tests in `test_articles_routes.py` for `GET /api/v1/articles/search`: mock `orchestrator.search_and_enrich_articles` and assert returned items have `stock_real` integer value (not `null`).
  - [x] **RED:** Verify route accepts query parameter `id_deposito: int` (default `1`) and forwards it to the orchestrator.
  - [x] **GREEN:** In `backend/api/v1/articles.py:search_articles`, inject `orchestrator: ArticleCatalogOrchestrator = Depends(get_article_catalog_orchestrator)` and replace `search_service.search_articles(...)` with `orchestrator.search_and_enrich_articles(...)`.
- **Verification Command:** `pytest tests/api/test_articles_routes.py`
- **Status:** `[x] done`

---

### `T3`: Audited Stock Session Priority & Role Masking Regression Tests
- **Covers Spec IDs:** `S2`, `S3`, `S4`
- **Dependencies:** `T2`
- **Route:** `inline`
- **Risk Tier:** `medium` (Verifies multi-database session audit priority over baseline stock and ensures RBAC financial masking is preserved)
- **Allowed Edit Surfaces:**
  - `backend/tests/api/test_articles_routes.py`
  - `backend/tests/domain/test_article_catalog_orchestrator.py`
- **Acceptance Criteria:**
  - [x] Test that when an article is marked audited (`fue_auditado=True`), `stock_real` returns the audited quantity from session audits.
  - [x] Test that non-admin (auditor/supervisor) responses strictly omit `pcio_com_siva` while admin responses include `pcio_com_siva`.
  - [x] Test search with query returning zero matches returns `200 OK` with `[]`.
- **Verification Command:** `pytest tests/api/test_articles_routes.py tests/domain/test_article_catalog_orchestrator.py`
- **Status:** `[x] done`

---

### `T4`: Full Quality Gates, Regression Suite & Conventional Commit
- **Covers Spec IDs:** `S1`, `S2`, `S3`, `S4`
- **Dependencies:** `T3`
- **Route:** `inline`
- **Risk Tier:** `low` (Verification only, no code logic changes)
- **Allowed Edit Surfaces:**
  - `specs/fix-search-stock-enrichment/tasks.md`
  - `specs/fix-search-stock-enrichment/handoff.md`
- **Acceptance Criteria:**
  - [x] All 377+ backend tests pass: `pytest`.
  - [x] Linters and formatting pass: `ruff check . && ruff format --check .`.
  - [x] Create conventional commit: `git commit -m "fix(backend): enrich article search results with effective stock levels"`.
  - [x] Update `tasks.md` and `handoff.md` to reflect completion.
- **Verification Command:** `pytest && ruff check . && ruff format --check .`
- **Status:** `[x] done`
