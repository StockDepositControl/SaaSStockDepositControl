# Handoff: Article Search Stock Enrichment

- **Spec:** [`specs/fix-search-stock-enrichment/spec.md`](file:///home/fede/Proyectos/SaaSStockDepositControl/specs/fix-search-stock-enrichment/spec.md)
- **Tasks:** [`specs/fix-search-stock-enrichment/tasks.md`](file:///home/fede/Proyectos/SaaSStockDepositControl/specs/fix-search-stock-enrichment/tasks.md)
- **Status:** `Approved - Ready for Execution`
- **Approved By:** `fede`
- **Approval Date:** `2026-10-28`

---

## Context & Architecture Summary

1. **Problem:**
   - In `backend/api/v1/articles.py`, `GET /api/v1/articles/search` directly calls `search_service.search_articles(...)`, bypassing `ArticleCatalogOrchestrator` and `StockLookupService`.
   - Domain `Articulo` instances return with `stock_real = None`.
   - Frontend web mapper converts `null` to `0`, making the Stock Audit search autocomplete display `Stock: 0` for all items until an individual item is audited.
2. **Resolution:**
   - `T1`: Add `search_and_enrich_articles` to `ArticleCatalogOrchestrator` in `backend/app/articles/orchestrator.py` with domain unit tests.
   - `T2`: Wire `search_articles` route in `backend/api/v1/articles.py` to `ArticleCatalogOrchestrator` with route tests.
   - `T3`: Verify audited stock session priority and RBAC masking regressions.
   - `T4`: Run static quality gates (`pytest`, `ruff`), commit, and finalize docs.

---

## Instructions for Claude Code (Build Agent)

Follow the 4 prompts provided for `T1` through `T4`.
Remember:
- Branch: `git checkout -b fix/search-stock-enrichment`
- Follow strict TDD: Red -> Green -> Refactor.
- Run tests from `backend/` using the commands defined in `tasks.md`.
- No AI attribution in git commits.

---

## Progress Log

### `T1` — Done (2026-10-28, uncommitted; commit deferred to `T4`)
- Added `ArticleCatalogOrchestrator.search_and_enrich_articles(query, deposit_id=1, active_session_id=None) -> List[Articulo]` in `backend/app/articles/orchestrator.py`.
  - Calls `ArticleSearchService.search_articles(query=..., active_session_id=...)` (signature verified in `backend/app/articles/services.py`).
  - Empty result short-circuits to `[]` without calling `StockLookupService`.
  - Enriches via `model_copy(update={"stock_real": stock_map.get(id, 0)})`; missing stock defaults to `0`, originals are not mutated.
- Tests: `test_search_and_enrich_articles_resolves_stock`, `test_search_and_enrich_articles_empty_result` in `backend/tests/domain/test_article_catalog_orchestrator.py` (RED observed, then GREEN: 8 passed).
- `ruff check` / `ruff format --check` clean on touched files.
- **Next:** `T2` — inject the orchestrator into `GET /api/v1/articles/search` and call `search_and_enrich_articles`.

### `T4` — Done (2026-10-28)
- `pytest` (from `backend/`): 408 passed.
- `ruff check .`: all checks passed; `ruff format --check .`: 127 files already formatted.
- No source changes required. T1–T4 committed together as `fix(backend): enrich article search results with effective stock levels`.
- **Status:** Change complete; all `S1`–`S4` verified.
