# Specification: Article Search Stock Enrichment

- **Change ID:** `fix-search-stock-enrichment`
- **Status:** `Approved`
- **Approved By:** `fede`
- **Approval Date:** `2026-10-28`
- **Author Agent:** Antigravity (Gemini)

---

## 1. Objective

Resolve the stock inconsistency where searching for articles via `GET /api/v1/articles/search` (consumed by the Stock Audit autocomplete and item search on both web and mobile) returns `stock_real = None`, causing the UI to display `Stock: 0` for all pending items, even though the Item Catalog correctly displays their positive baseline stock (e.g. 194).

This change integrates `GET /api/v1/articles/search` with the existing domain orchestrator ([`ArticleCatalogOrchestrator`](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/app/articles/orchestrator.py)), ensuring all article search results are enriched with effective stock quantities resolved via [`StockLookupService`](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/app/movements/services.py) across bounded contexts (`db_analytics` session audits with fallback to `db_articles.stock_posicion`).

---

## 2. Assumptions & Invariants

- `A1:` `StockLookupService.get_effective_stocks_batch` is already implemented, tested, and handles cross-database stock resolution (prioritizing active session audit counts in `db_analytics` and falling back to `stock_posicion` in `db_articles`).
- `A2:` `ArticleCatalogOrchestrator` is the established Pure Fabrication service responsible for cross-context stock enrichment between `ArticleSearchService` and `StockLookupService`.
- `A3:` `GET /api/v1/articles/search` should accept an optional `id_deposito: int = Query(1, ge=1)` parameter (defaulting to warehouse 1, matching the existing behavior of `GET /api/v1/articles` and `GET /api/v1/articles/{id_articulo}`).
- `A4:` Role-based field masking remains strict: Administrators receive `ArticuloAdminOut` (including `pcio_com_siva`), while auditors/supervisors receive `ArticuloPublicOut` (cost strictly omitted).
- `A5:` If the search query returns zero matching articles, the orchestrator returns an empty list without attempting redundant database calls to `StockLookupService`.

---

## 3. Boundaries & Out of Scope

- **Frontend changes:** None. The frontend web mapper (`mapToArticuloPublicView` in `frontend-web/lib/adapters/mappers.ts`) already maps `raw.stock_real` to a number when provided; it was only defaulting to `0` because `raw.stock_real` was `null`. Once the backend sends the integer, the UI instantly displays the real stock.
- **Database schema / migrations:** No schema changes or migrations are needed.
- **Catalog endpoint:** `GET /api/v1/articles` and `GET /api/v1/articles/{id_articulo}` are already properly enriched and remain untouched.

---

## 4. Tech Stack & Commands

Commands inherited from [`AGENTS.md`](file:///home/fede/Proyectos/SaaSStockDepositControl/AGENTS.md) (`cd backend`, python virtual environment at `backend/.venv`):

- **Run focused backend tests:**
  ```bash
  pytest tests/api/test_articles_routes.py tests/domain/test_article_catalog_orchestrator.py
  ```
- **Run all backend tests:**
  ```bash
  pytest
  ```
- **Lint & format check:**
  ```bash
  ruff check . && ruff format --check .
  ```

---

## 5. Architectural Specification

### 5.1 Domain Layer: `ArticleCatalogOrchestrator`
Add method `search_and_enrich_articles` to [`backend/app/articles/orchestrator.py`](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/app/articles/orchestrator.py):

```python
async def search_and_enrich_articles(
    self,
    query: str,
    deposit_id: int = 1,
    active_session_id: Optional[int] = None,
) -> List[Articulo]:
    """
    Orchestrates:
    1. Multi-field search across article ID, barcode, or description via ArticleSearchService.
    2. Batch lookup of effective stock levels via StockLookupService.get_effective_stocks_batch.
    3. Immutable enrichment of article domain entities with resolved stock_real.
    """
```

### 5.2 API Layer: `search_articles` Router
Update `search_articles` in [`backend/api/v1/articles.py`](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/api/v1/articles.py):
- Inject `orchestrator: ArticleCatalogOrchestrator = Depends(get_article_catalog_orchestrator)`.
- Accept `id_deposito: int = Query(1, ge=1, description="Deposit/Warehouse ID for stock resolution")`.
- Replace `search_service.search_articles(...)` with `orchestrator.search_and_enrich_articles(query=query, deposit_id=id_deposito, active_session_id=session.session_id)`.
- Continue serializing results via `ArticuloAdminOut` or `ArticuloPublicOut`.

---

## 6. Acceptance Criteria (Behaviourial `Given / When / Then`)

- `S1 (Baseline stock enrichment):`
  - **Given** an article `"ART-00002"` that has not been audited in the active work session and has a baseline stock of `194` in `db_articles.stock_posicion` for warehouse `1`,
  - **When** an auditor requests `GET /api/v1/articles/search?query=MED+Esa`,
  - **Then** the response status is `200 OK`, and the item in the response list contains `"stock_real": 194` and `"fue_auditado": false`.

- `S2 (Audited stock priority):`
  - **Given** an article `"ART-00002"` that has an active session audit record in `db_analytics` with counted stock `195`,
  - **When** an auditor requests `GET /api/v1/articles/search?query=MED+Esa`,
  - **Then** the response status is `200 OK`, and the item in the response list contains `"stock_real": 195` and `"fue_auditado": true`.

- `S3 (Warehouse deposit parameter propagation):`
  - **Given** deposit `2` with distinct stock levels,
  - **When** a user requests `GET /api/v1/articles/search?query=MED+Esa&id_deposito=2`,
  - **Then** `orchestrator.search_and_enrich_articles` passes `deposit_id=2` to `StockLookupService`.

- `S4 (Empty search query handling):`
  - **Given** a query matching no items in the database,
  - **When** a user requests `GET /api/v1/articles/search?query=nonexistent`,
  - **Then** the response status is `200 OK` with an empty array `[]`, and `stock_lookup_service.get_effective_stocks_batch` is never called.
