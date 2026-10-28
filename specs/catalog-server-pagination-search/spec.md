# Specification: Catalog Server-Side Pagination and Search

- **Change ID:** `catalog-server-pagination-search`
- **Status:** `Approved`
- **Approved By:** `fede`
- **Approval Date:** `2026-10-28`
- **Author Agent:** Antigravity (Gemini)

---

## 1. Objective

Resolve the inconsistency where the web frontend catalog displays only 10 pages and exclusively shows "MED" articles (omitting all "ART" articles present in the database), while the audit module search successfully accesses all database items.

This change transitions the catalog module from a hardcoded client-side 100-item in-memory slice to true **server-side pagination, search, and filtering**, allowing warehouse auditors and administrators to browse, filter, and search across the entire database catalog regardless of size.

---

## 2. Assumptions

- `A1:` The backend endpoint `GET /api/v1/articles` already supports `page`, `limit`, `search`, `id_familia`, `id_grupo`, and `fue_auditado`, and returns `{ items, total, page, limit, pages }`.
- `A2:` In MariaDB `db_articles`, articles are ordered by `id_articulo ASC`. Seed data generates 250 "MED" articles followed by 250 "ART" articles; fetching only the first 100 records was the sole reason "ART" articles never appeared.
- `A3:` Searching in the catalog should match article code (`id_articulo`), barcode (`cod_barra`), and description tokens (`des_articulo`), aligning catalog search capabilities with the audit search module.
- `A4:` A catalog page size of 10 items per page matches the existing `DataTable` presentation, while the server pagination controls will reflect the true database total (e.g., 500 items across 50 pages).
- `A5:` The report module (`app/reports/page.tsx`) consumes `useArticles()`, so backward compatibility or clean propagation of `useArticles` options must be preserved.

---

## 3. Tech Stack & Commands

Inherited from [`AGENTS.md`](file:///home/fede/Proyectos/SaaSStockDepositControl/AGENTS.md):

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2
  - **Tests (Focused):** `pytest tests/api/test_articles_routes.py tests/domain/test_article_search_service.py`
  - **Tests (All):** `pytest`
  - **Lint & Format:** `ruff check . && ruff format --check .`
- **Frontend Web:** Next.js 14 App Router, TypeScript, React 19, Vitest
  - **Tests (Focused):** `npx vitest run lib/adapters/ApiDataClient.test.ts lib/hooks/useArticles.test.ts app/catalog/page.test.tsx`
  - **Tests (All):** `npm test`
  - **Typecheck:** `npx tsc --noEmit`
  - **Lint:** `npm run lint`

---

## 4. Project Structure & Module Boundaries

### Backend Modules
- **`backend/adapters/repositories/article_repository.py`:**
  - Update `list_articles` to support barcode search by joining or subquerying `CodigoBarraArticuloORM.cod_barra == clean_search`.
  - Add `list_families` method to query distinct active families (`id_familia`, `des_familia`) from table `familias`.
- **`backend/app/articles/services.py` & `orchestrator.py`:**
  - Expose `get_families()` in `ArticleSearchService`.
- **`backend/api/v1/articles.py`:**
  - Expose `GET /api/v1/articles/families` returning `List[Familia]` (`id_familia`, `des_familia`).

### Frontend Web Modules
- **`frontend-web/lib/types/api.ts` & `domain.ts`:**
  - Define `ArticleCatalogQuery` and `PaginatedArticlesResult`.
  - Define `ArticleFamily` interface (`{ id_familia: string; des_familia: string }`).
- **`frontend-web/lib/ports/DataClientPort.ts`:**
  - Add `getPaginatedArticles(query?: ArticleCatalogQuery, role?: UserRole): Promise<PaginatedArticlesResult>`.
  - Add `getFamilies(): Promise<ArticleFamily[]>`.
  - Preserve `getArticulos(role?: UserRole)` for backward compatibility.
- **`frontend-web/lib/adapters/ApiDataClient.ts` & `MockDataContext.tsx`:**
  - Implement `getPaginatedArticles` calling `/api/v1/articles` with query parameters.
  - Implement `getFamilies` calling `/api/v1/articles/families` (or mock seed families).
- **`frontend-web/lib/hooks/useArticles.ts`:**
  - Provide server-driven query state: `page`, `limit` (default 10), `search`, `id_familia`, `status` (`fue_auditado`).
  - Provide debounced search query trigger (~250ms).
  - Return `{ articles, total, page, limit, pages, families, setPage, setSearch, setFamily, setStatus, isLoading, error, refetch }`.
- **`frontend-web/components/ui/DataTable.tsx` & `app/catalog/page.tsx`:**
  - Convert `DataTable` from client-side array slice to controlled server-pagination component.
  - Wire search input, family selector, status selector, and pagination buttons to server callbacks.
  - Update catalog subtitle to display actual database total: `${total} artículos`.

---

## 5. Code Style & Contract Snippets

### Frontend Data Port & Query Contracts

```typescript
export interface ArticleCatalogQuery {
  page?: number;
  limit?: number;
  search?: string;
  id_familia?: string;
  id_grupo?: string;
  fue_auditado?: boolean;
  id_deposito?: number;
}

export interface PaginatedArticlesResult {
  items: (ArticuloPublicView | ArticuloAdminView)[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface ArticleFamily {
  id_familia: string;
  des_familia: string;
}

export interface DataClientPort {
  // Existing methods preserved...
  getArticulos(role?: UserRole): Promise<(ArticuloPublicView | ArticuloAdminView)[]>;
  getPaginatedArticles(query?: ArticleCatalogQuery, role?: UserRole): Promise<PaginatedArticlesResult>;
  getFamilies(): Promise<ArticleFamily[]>;
}
```

### Backend Family Endpoint Contract

```python
@router.get(
    "/families",
    response_model=List[Familia],
    summary="List all product families",
    description="Returns all product families for catalog filtering."
)
async def list_families(
    search_service: ArticleSearchService = Depends(get_article_search_service),
) -> List[Familia]:
    return await search_service.list_families()
```

---

## 6. Acceptance Criteria (Behavioural & Testable)

- **`S1` (Full Catalog Pagination Beyond 100 Items):**
  - **Given:** A database seeded with 500 articles.
  - **When:** An authenticated user navigates to `/catalog` with default page size 10.
  - **Then:** The catalog header indicates `500 artículos`, the pagination footer indicates `1-10 de 500 ítems`, `totalPages` is `50`, and navigating to page 11 requests `{ page: 11, limit: 10 }` and renders items 101–110.

- **`S2` (Visibility of "ART" and Taxable Items):**
  - **Given:** Articles `ART-00000` through `ART-00249` are "MED" and `ART-00250` through `ART-00499` are "ART".
  - **When:** The user navigates to page 26 or searches for `"ART"`.
  - **Then:** Articles with prefix `"ART "` are rendered in the catalog table with their corresponding descriptions and stocks.

- **`S3` (Server-Side Multi-Token & Barcode Search):**
  - **Given:** An article with barcode `"7791234567890"` and name `"Amoxicilina 500mg"`.
  - **When:** The user enters `"7791234567890"` or `"Amoxicilina"` into the catalog search field.
  - **Then:** The client debounces for 250ms and calls `GET /api/v1/articles?search=...`, returning the matching item and resetting `page` to 1.

- **`S4` (Server-Side Family Filtering):**
  - **Given:** Families `"01"` ("Medicamentos") and `"02"` ("Perfumería").
  - **When:** The user selects "Perfumería" from the family filter dropdown.
  - **Then:** The client requests `GET /api/v1/articles?id_familia=02&page=1`, returning exclusively articles belonging to family `"02"`, updating total results and total pages accordingly.

- **`S5` (Role-Based Price Masking Across All Pages):**
  - **Given:** Any page (e.g. page 1, 26, or search results) fetched by an `AUDITOR` or `SUPERVISOR`.
  - **When:** Articles are mapped and rendered.
  - **Then:** `pcio_com_siva` is structurally omitted from the domain view and table columns.
  - **Given:** An `ADMINISTRADOR` user.
  - **When:** Any page is fetched.
  - **Then:** `pcio_com_siva` is present, parsed as a number, and displayed in the cost column.

- **`S6` (In-Flight Request Cancellation & Race Safety):**
  - **Given:** The user types rapidly in the search input or rapidly clicks through pages.
  - **When:** Multiple HTTP requests are dispatched in quick succession.
  - **Then:** Previous pending requests are aborted/cancelled, and only the response matching the latest active query updates the UI.

- **`S7` (MockDataProvider Fallback Parity):**
  - **Given:** The application runs with `NEXT_PUBLIC_DATA_SOURCE=mock`.
  - **When:** `getPaginatedArticles` or `getFamilies` is called.
  - **Then:** Mock data is paginated and filtered in memory matching the exact response contract `{ items, total, page, limit, pages }`.

---

## 7. Risks, Edge Cases & Failure Modes

- **Race Conditions on Search Input:** Rapid typing could return responses out of order. Mitigated by `AbortController` / cancellation token pattern and settled-state tick checking.
- **Empty Filter Results:** When search or family filter matches 0 items, table must render empty state `"No se encontraron resultados"` without breaking pagination footer (showing `0-0 de 0 ítems` and disabling previous/next buttons).
- **Backend Limit Clamping:** Backend enforces `limit <= 200`. Catalog client uses `limit = 10` (or user-selected 10/25/50), well within the safe ceiling.
- **Family Filter Discrepancy:** The old client filtered in-memory by `des_familia` string. Backend filters by `id_familia` code. The new family selector must use `id_familia` as the `option` value and `des_familia` as the label.

---

## 8. Testing Strategy

- **Backend Unit & Integration:**
  - `backend/tests/api/test_articles_routes.py`:
    - Test `GET /api/v1/articles/families` returns list of families.
    - Test `GET /api/v1/articles?search=<barcode>` returns barcode match.
    - Test `GET /api/v1/articles?page=26&limit=10` returns correct slice and total count.
- **Frontend Unit & Integration:**
  - `frontend-web/lib/adapters/ApiDataClient.test.ts`:
    - Test `getPaginatedArticles` sends query parameters and returns `PaginatedArticlesResult`.
    - Test `getFamilies` fetches `/api/v1/articles/families`.
  - `frontend-web/lib/hooks/useArticles.test.ts`:
    - Test pagination changes trigger refetch with updated `page`.
    - Test debounced search triggers refetch and resets `page` to 1.
    - Test role-based masking on paginated results.
  - `frontend-web/app/catalog/page.test.tsx`:
    - Test catalog table renders total items, navigates pages, and triggers search.

---

## 9. Boundaries & Out of Scope

- **In Scope:**
  - Backend barcode search matching in `SQLAlchemyArticleRepository.list_articles`.
  - Backend `GET /api/v1/articles/families` endpoint.
  - Frontend `DataClientPort`, `ApiDataClient`, and `MockDataContext` paginated methods.
  - `useArticles` hook refactoring with debounced search and server-side pagination state.
  - `DataTable.tsx` and `app/catalog/page.tsx` integration with server pagination and filtering.
- **Out of Scope:**
  - Altering database schema or MariaDB tables.
  - Changing audit module search behavior (which already works properly).
  - Editing mobile app catalog (no mobile catalog exists).

---

## 10. Open Questions

- None. Requirements and approach (server-side pagination and search) are fully validated.
