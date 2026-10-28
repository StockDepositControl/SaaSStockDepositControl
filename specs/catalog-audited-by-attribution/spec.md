# Specification: Auditor Attribution in Item Catalog

- **Change ID:** `catalog-audited-by-attribution`
- **Status:** `Approved`
- **Approved By:** `fede`
- **Approval Date:** `2026-10-28`
- **Author Agent:** Antigravity (Gemini)

---

## 1. Objective

Resolve the catalog audit authorship inconsistency where an item audited by an auditor (or any non-supervisor user) displays the name and initials of the currently logged-in supervisor in the "AUDITADO POR" column when viewed under a supervisor profile in the "Item Catalog" module (`/catalog`).

This change implements end-to-end auditor attribution across the full stack:
1. `AuditRepositoryPort` and `SQLAlchemyAuditRepository` in `db_analytics` batch-resolve the `user_id` of the latest audit record per article for the active session.
2. `ArticleCatalogOrchestrator` cross-resolves `user_id` against `UserRepositoryPort` (`db_users`) to enrich articles with the auditor's full name via `audited_by: Optional[str]`.
3. Backend API schemas (`ArticuloPublicOut`, `ArticuloAdminOut`) and frontend domain types expose `audited_by`.
4. `frontend-web` components (`DataTable.tsx`, `MockDataContext.tsx`) replace the pseudo-random hashing helper with direct rendering of `art.audited_by`.

---

## 2. Assumptions & Invariants

- `A1:` `AuditRecordORM` in `db_analytics` already persists `user_id` on every successful audit movement (`AuditRecordORM.user_id: int`).
- `A2:` If an article has multiple audit scans within an active work session, the most recent scan (ordered by `scan_timestamp DESC`) dictates both effective stock quantity and the effective auditor.
- `A3:` In accordance with Hexagonal Architecture and the three-database boundary (`db_articles`, `db_users`, `db_analytics`), cross-database resolution is executed exclusively in the domain orchestration layer (`ArticleCatalogOrchestrator`), never via raw cross-database SQL JOINs.
- `A4:` The auditor's display name is formatted as `f"{first_name} {last_name}".strip()` from `db_users.users`. If a user has only `first_name` or names are whitespace-padded, the string is trimmed.
- `A5:` If an article is not audited (`fue_auditado == False`), `audited_by` must strictly be `None` (or `null` in JSON).
- `A6:` If an article is audited but its user ID cannot be resolved from `db_users` (e.g. deleted or orphaned user), `audited_by` falls back to `None`, and the UI displays the neutral fallback dash (`—`).
- `A7:` Role-based field masking remains invariant: `audited_by` is visible to supervisors in the catalog; purchase cost (`pcio_com_siva`) remains strictly restricted to administrators.

---

## 3. Tech Stack & Commands

Monorepo commands inherited from [`AGENTS.md`](file:///home/fede/Proyectos/SaaSStockDepositControl/AGENTS.md):

### Backend (`cd backend`, python virtual environment at `backend/.venv`)
- **Run focused backend tests:**
  ```bash
  pytest tests/domain/test_article_catalog_orchestrator.py tests/adapters/test_audit_repository.py tests/api/test_articles_routes.py
  ```
- **Run all backend tests:**
  ```bash
  pytest
  ```
- **Lint & format check:**
  ```bash
  ruff check . && ruff format --check .
  ```

### Frontend Web (`cd frontend-web`)
- **Run focused frontend tests:**
  ```bash
  npx vitest run app/catalog/page.test.tsx lib/adapters/mappers.test.ts
  ```
- **Run all frontend tests:**
  ```bash
  npm test
  ```
- **Typecheck:**
  ```bash
  npx tsc --noEmit
  ```
- **Lint:**
  ```bash
  npm run lint
  ```

---

## 4. Architectural Specification & Interfaces

### 4.1 Analytics Repository Port & Adapter (`backend/app/movements/ports.py` & `backend/adapters/repositories/audit_repository.py`)

Add method to `AuditRepositoryPort`:
```python
@abstractmethod
async def get_latest_audit_users_for_articles(
    self, session_id: int, article_ids: List[str]
) -> Dict[str, int]:
    """
    Retrieves the latest audit user_id for multiple articles within a specific session.
    Returns a mapping of {article_code: user_id}.
    """
    pass
```

Implementation in `SQLAlchemyAuditRepository` uses the existing window function pattern:
```python
async def get_latest_audit_users_for_articles(
    self, session_id: int, article_ids: List[str]
) -> Dict[str, int]:
    if not article_ids:
        return {}
    async with self.session_factory() as session:
        rn = (
            func.row_number()
            .over(
                partition_by=AuditRecordORM.article_code,
                order_by=AuditRecordORM.scan_timestamp.desc(),
            )
            .label("rn")
        )
        subq = (
            select(AuditRecordORM.article_code, AuditRecordORM.user_id, rn)
            .where(
                AuditRecordORM.session_id == session_id,
                AuditRecordORM.article_code.in_(article_ids),
            )
            .subquery()
        )
        stmt = select(subq.c.article_code, subq.c.user_id).where(subq.c.rn == 1)
        result = await session.execute(stmt)
        return {str(row[0]).strip(): int(row[1]) for row in result.all() if row[1] is not None}
```

Add delegation helper to `StockLookupService` in `backend/app/movements/services.py`:
```python
async def get_session_auditors_batch(
    self, session_id: int, article_ids: List[str]
) -> Dict[str, int]:
    return await self.audit_repository.get_latest_audit_users_for_articles(
        session_id=session_id, article_ids=article_ids
    )
```

### 4.2 Article Domain & Output Models (`backend/app/articles/models.py`)

Add `audited_by` to `ArticuloBase` and `ArticuloPublicOut`:
```python
class ArticuloBase(BaseModel):
    ...
    fue_auditado: bool = False
    stock_real: Optional[int] = None
    audited_by: Optional[str] = None

class ArticuloPublicOut(BaseModel):
    ...
    fue_auditado: bool = False
    stock_real: Optional[int] = None
    audited_by: Optional[str] = None

class ArticuloAdminOut(ArticuloPublicOut):
    pcio_com_siva: Decimal
```

### 4.3 Domain Orchestration (`backend/app/articles/orchestrator.py`)

Update `ArticleCatalogOrchestrator`:
- Inject `user_repository: Optional[UserRepositoryPort] = None` in `__init__`.
- Update `get_enriched_catalog(page, limit, search, id_familia, id_grupo, fue_auditado, deposit_id, active_session_id, tenant_id=None)`:
  - When `active_session_id` and `tenant_id` are provided and `articles` is non-empty:
    1. Call `stock_lookup_service.get_session_auditors_batch(session_id=active_session_id, article_ids=article_ids)` to retrieve `{article_code: user_id}`.
    2. Collect unique user IDs and resolve domain users via `user_repository.list_by_tenant(tenant_id)` or individual lookups, caching name mapping `{user_id: f"{u.first_name} {u.last_name}".strip()}`.
    3. Enrich articles with `audited_by = user_names.get(user_id)`.
- Apply identical enrichment in `search_and_enrich_articles` and `get_enriched_article`.

### 4.4 Dependency Injection & Router Wiring (`backend/api/dependencies/services.py` & `backend/api/v1/articles.py`)

- `get_article_catalog_orchestrator`:
  ```python
  def get_article_catalog_orchestrator(
      search_service: "ArticleSearchService" = Depends(get_article_search_service),
      stock_lookup_service: "StockLookupService" = Depends(get_stock_lookup_service),
  ) -> "ArticleCatalogOrchestrator":
      from backend.adapters.database.connection import get_users_session_factory
      from backend.adapters.repositories.user_repository import SQLAlchemyUserRepository
      from backend.app.articles.orchestrator import ArticleCatalogOrchestrator

      user_repo = SQLAlchemyUserRepository(get_users_session_factory())
      return ArticleCatalogOrchestrator(
          article_search_service=search_service,
          stock_lookup_service=stock_lookup_service,
          user_repository=user_repo,
      )
  ```
- In `backend/api/v1/articles.py`:
  Pass `tenant_id=int(tenant_id)` (from `claims.get("tenant_id", 1)`) to `orchestrator.get_enriched_catalog`, `orchestrator.search_and_enrich_articles`, and `orchestrator.get_enriched_article`.

### 4.5 Frontend Domain, Adapters & UI (`frontend-web/`)

1. **Domain Types (`frontend-web/lib/types/domain.ts` & `frontend-web/lib/types/api.ts`):**
   - Add `audited_by?: string | null;` to `ArticuloBase` and `ApiArticuloBase`.
2. **Mapper (`frontend-web/lib/adapters/mappers.ts`):**
   - In `mapToArticuloPublicView`: `audited_by: raw.audited_by ?? null`.
3. **Mock Data Provider (`frontend-web/lib/mocks/MockDataContext.tsx` & `seed-data.ts`):**
   - In `registerAudit`: set `audited_by: currentUser?.name || "Auditor"` when updating articles in state.
   - In `seed-data.ts`: add `audited_by: "Usuario Test (Auditor)"` to seeded audited items (`ART-00101`, `ART-00102`, `ART-00103`).
4. **Data Table Component (`frontend-web/components/ui/DataTable.tsx`):**
   - Delete `getAuditorForArticle` completely.
   - For both mobile card view and desktop table view under supervisor role:
     ```tsx
     const auditorName = art.audited_by;
     const auditorInitials = auditorName
       ? auditorName.trim().split(/\s+/).map((n) => n[0]).join("").substring(0, 2).toUpperCase()
       : "";
     ```
     - If `art.fue_auditado && auditorName`: render the blue avatar with initials and `auditorName`.
     - If `art.fue_auditado && !auditorName`: render `<span className="text-slate-400">—</span>`.
     - If `!art.fue_auditado`: render `<span className="text-slate-300">—</span>`.

---

## 5. Acceptance Criteria (Deterministic `Given / When / Then`)

### `S1`: Backend Analytics Audit User Resolution
- **Given** active session `10` containing an audit record for article `"ART-001"` performed by user `42` (`user_id = 42`),
- **When** `audit_repository.get_latest_audit_users_for_articles(session_id=10, article_ids=["ART-001"])` is called,
- **Then** the returned dictionary contains `{"ART-001": 42}`.

### `S2`: Cross-Context Orchestration & User Name Enrichment
- **Given** active session `10` where article `"ART-001"` was audited by user `42` and user `42` has `first_name="Carlos"`, `last_name="Auditor"` in `db_users`,
- **When** `orchestrator.get_enriched_catalog(page=1, limit=10, active_session_id=10, tenant_id=1)` is executed,
- **Then** the resulting article for `"ART-001"` has `fue_auditado=True`, `stock_real` resolved, and `audited_by="Carlos Auditor"`.

### `S3`: Endpoint Payload Attribution
- **Given** an article `"ART-001"` audited by user `"Carlos Auditor"`,
- **When** an authorized supervisor requests `GET /api/v1/articles`,
- **Then** the JSON response returns status `200 OK`, and the item object includes `"audited_by": "Carlos Auditor"` and `"fue_auditado": true`.

### `S4`: Unaudited Article Field Integrity
- **Given** an article `"ART-002"` that has not been audited in the active session,
- **When** any authorized user requests `GET /api/v1/articles`,
- **Then** the JSON response returns `"audited_by": null` and `"fue_auditado": false`.

### `S5`: Frontend DataTable Supervisor View Displays Actual Auditor
- **Given** article `"ART-001"` with `fue_auditado: true` and `audited_by: "Carlos Auditor"`, viewed by a user with role `UserRole.SUPERVISOR` named `"Silvia Supervisora"`,
- **When** `DataTable` is rendered,
- **Then** the "AUDITADO POR" column displays `"Carlos Auditor"` (initials `"CA"`), and does **not** display `"Silvia Supervisora"`.

### `S6`: Mock Mode Audit Attribution Fidelity
- **Given** an auditor user logged in under `MockDataProvider`,
- **When** the auditor registers a physical count for an unaudited article `"ART-00104"`,
- **And** the session switches to a supervisor profile,
- **Then** the catalog displays `"ART-00104"` with status `AUDITADO` and "AUDITADO POR" matching the auditor's name.

---

## 6. Risks, Edge Cases & Failure Modes

1. **User Not Found in `db_users`:** If a user account was deactivated or removed, `audited_by` gracefully evaluates to `None` without crashing, displaying `—`.
2. **Missing `active_session_id`:** When browsing the catalog outside an active session, `auditor_id_map` is empty and `audited_by` is safely `None`.
3. **Single Word Names:** Name initials splitting uses `.split(/\s+/)` with `.substring(0, 2)` to safely handle single-word names (e.g. `"Admin"` -> `"AD"`).
4. **Performance:** `list_by_tenant` is called at most once per catalog page request, caching user models in a local dictionary for $O(1)$ memory mapping over the page's article list.

---

## 7. Boundaries & Out of Scope

- **Out of Scope:**
  - Changes to mobile UI layouts (mobile uses `ArticuloAuditorView` which already omits the auditor attribution column).
  - Any alterations to MariaDB schema or migrations (`AuditRecordORM.user_id` and `User.user_id` already exist).
  - Modifying financial calculations, VAT rules, or voucher action types.

---

## 8. Open Questions

- None. All requirements and architectural choices resolved.
