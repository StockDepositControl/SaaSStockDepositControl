# Handoff Log: Catalog Server-Side Pagination and Search

- **Spec:** `specs/catalog-server-pagination-search/spec.md`
- **Tasks:** `specs/catalog-server-pagination-search/tasks.md`
- **Current Phase:** `Ready for Build (Approved)`
- **Engram Topic Key:** `spec/catalog-server-pagination-search/decisions`

---

## 1. Handoff Status

- **Spec Status:** `Approved`
- **Last Updated By:** `Antigravity (Gemini)`
- **Completed Tasks:** `None`
- **Pending Tasks:** `T1, T2, T3, T4`

---

## 2. Spec-Challenge Notes (Filled by Claude Code in Plan Mode Before Coding)

- **Contradictions Found:**
  - `spec.md` §4 names the service method `get_families()`, while the §5 endpoint snippet calls `search_service.list_families()`. `tasks.md` T1 lists `ports.py`/`services.py` but not `orchestrator.py`. Decision: use `list_families` consistently (repository port, service, endpoint).
  - `A2`/`S2` use inconsistent identifiers (`ART-00000..249` are "MED", prefix `"ART "` vs `ART-`). Seed data shape must be confirmed before writing the S2 fixture.
  - `S2` ("searches for `ART`" shows ART articles) conflicts with current `list_articles` search: it matches `id_articulo == term` (exact) OR description tokens (`ilike %term%`). There is no id-prefix match, so `ART` would not select ART-prefixed ids.
- **Missing Edge Cases / Failure Modes:**
  - `GET /articles/families` must be registered BEFORE `/{id_articulo}` or it is shadowed.
  - The §5 families snippet has no auth dependency; sibling routes require `get_current_user_claims`. Default: require auth.
  - `Familia` response model does not exist in the backend; must be created (`id_familia`, `des_familia`).
  - `fue_auditado=false` is silently ignored when there is no active session (repository behaviour).
  - §7 mentions a user-selected page size (10/25/50) but the hook contract has no `setLimit`; treated as out of scope (fixed `limit = 10`).
- **Untestable Criteria:** `S2` (search `ART`) until the decision below is made.
- **Resolution:** `Blocked awaiting human decision (S2 search semantics)`

---

## 3. Durable Decisions & Rationale

| Date | Actor | Decision | Rationale / Tradeoff | Engram / ADR Ref |
|---|---|---|---|---|
| 2026-10-28 | Human (fede) & Antigravity | Implement true server-side pagination and search for the catalog module | Loading the entire database into browser memory degrades client performance for real pharmacy inventories (thousands of articles). Backend `GET /api/v1/articles` already supports pagination and filtering. | `spec/catalog-server-pagination-search/decisions` |
| 2026-10-28 | Antigravity | Add barcode matching to `list_articles` query and introduce `GET /api/v1/articles/families` | Harmonizes catalog search with audit module search capabilities, and allows the family dropdown to be populated independently of the current 10-item page slice. | `spec/catalog-server-pagination-search/decisions` |
| 2026-10-28 | Antigravity | Preserve `getArticulos(role)` on `DataClientPort` while adding `getPaginatedArticles` | Prevents breaking other callers (such as `NetInventoryBalanceTab` in reports) while enabling clean, strongly-typed paginated access for the catalog. | `spec/catalog-server-pagination-search/decisions` |

---

## 4. Open Questions & Blockers

- None. All requirements and architectural boundaries validated.

---

## 5. Next Action

- **Mandatory Approval Gate:** Await human review and explicit sign-off in chat to change `spec.md` status from `Draft` to `Approved`.
- **Handoff to Build Agent (Claude Code):** Once approved, Claude Code will execute tasks `T1` through `T4` following TDD (`Red -> Green -> Refactor`).

## T1 — Spec-Challenge Notes & Outcome (Claude Code)

- `familias` has no active flag; `GET /api/v1/articles/families` returns all families ordered by `id_familia` (matches spec contract "Returns all product families").
- Barcode match uses an `IN (SELECT id_articulo FROM codigos_barra_articulo WHERE cod_barra = :search)` subquery inside the existing `OR`, so `total` is not inflated by joins.
- `/families` is registered before `/{id_articulo}` to avoid path capture; it requires auth like the other article routes.
- Repository behaviour is verified by compiling the captured SQL statements (no DB in route tests).
- Verification: `pytest` 401 passed; `ruff check .` and `ruff format --check .` clean.

## T2 — Spec-Challenge Notes & Outcome (Claude Code)

- `ArticleCatalogQuery`, `PaginatedArticlesResult`, `ArticleFamily` live in `lib/types/domain.ts` (port contract); `lib/types/api.ts` adds the wire shape `ApiFamilyOut`. Existing `ApiArticleListResponse` reused.
- `ApiDataClient.getPaginatedArticles` defaults to `page=1, limit=10` and drops undefined/blank params (no `search=`).
- Mock parity: in-memory filter by `id_familia`, `id_grupo`, `fue_auditado`, and case-insensitive search over id/description/barcodes; `pages = ceil(total/limit)` (0 when empty, mirrors backend). Mock families are derived distinct from seed articles, sorted by id.
- Out-of-surface touch: `lib/context/ApiDataContext.tsx` wrapper implements `DataClientPort`; two pass-through lines added so `tsc` passes.
- Verification: `ApiDataClient.test.ts` 18 passed; `tsc --noEmit` clean. Pre-existing on baseline (unrelated): `app/reports/page.test.tsx` 1 failing test, `app/users/page.tsx` 1 lint error.
