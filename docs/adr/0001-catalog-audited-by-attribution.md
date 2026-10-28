# ADR 0001: Auditor Attribution in Item Catalog

- **Status:** Accepted
- **Date:** 2026-10-28
- **Related Spec:** `specs/catalog-audited-by-attribution/spec.md`

## Context

When an item audit is recorded by an auditor (or any non-supervisor user), and the system is subsequently accessed using a supervisor profile, the "Item Catalog" module (`/catalog`) displays the audited item as "AUDITADO". However, the "AUDITADO POR" column incorrectly displays the name of the currently logged-in supervisor instead of the auditor who actually conducted the audit.

Investigation revealed three compounding causes:
1. `frontend-web/components/ui/DataTable.tsx` contained a temporary mock helper `getAuditorForArticle(articleId)` that generated a pseudo-random hash of the article ID string modulo `users.filter(u => u.role === UserRole.AUDITOR || u.role === UserRole.SUPERVISOR)`.
2. In `frontend-web/lib/context/ApiDataContext.tsx`, under zero-prefetch architecture, `users` is initialized strictly as `currentUser ? [currentUser] : []`. When a supervisor logs in, `users` contains only that supervisor (`length = 1`), meaning `getAuditorForArticle` unconditionally resolved to the logged-in supervisor for 100% of audited articles.
3. In `backend/api/v1/articles.py` and `backend/app/articles/orchestrator.py`, the catalog endpoint queries `_get_audited_article_codes` which only returns boolean audit membership (`fue_auditado: bool`). `AuditRecordORM` in `db_analytics` stores `user_id` on every scan, but this authorship was never resolved or exposed through `ArticuloPublicOut` / `ArticuloAdminOut`.

## Decision

We adopt a **Full-Stack Auditor Attribution Architecture**:
1. **Analytics Repository Batch User Lookup:** Extend `AuditRepositoryPort` and `SQLAlchemyAuditRepository` with `get_latest_audit_users_for_articles(session_id, article_ids) -> Dict[str, int]` leveraging the existing window function partitioned by `article_code` and ordered by `scan_timestamp DESC`.
2. **Domain Orchestration Across Bounded Contexts:** In `ArticleCatalogOrchestrator`, inject `user_repository: Optional[UserRepositoryPort] = None`. When enriching catalog items for an active session, retrieve the mapping of `{article_code: user_id}` via `StockLookupService`, resolve user names against `UserRepositoryPort.list_by_tenant(tenant_id)` in `db_users`, and enrich `Articulo.audited_by` with the auditor's full name (`"{first_name} {last_name}"`).
3. **API & Domain Contracts:** Add `audited_by: Optional[str] = None` to `ArticuloBase`, `ArticuloPublicOut`, `ArticuloAdminOut`, and frontend types (`ArticuloBase`, `ApiArticuloBase`).
4. **Frontend Deterministic Attribution:** In `DataTable.tsx`, completely delete `getAuditorForArticle` and render `art.audited_by` directly. In `MockDataContext.tsx`, ensure `registerAudit` stamps `audited_by: currentUser?.name || "Auditor"` when mutating articles in state.

## Alternatives Considered

1. **Frontend-Only Audit Log Correlation:** The frontend would fetch `/api/v1/audit/logs` and correlate `user_id` with a cached user list.
   - *Rejected:* Violates separation of concerns, requires exposing user directory to supervisors, introduces N+1 client roundtrips, and fails for paginated catalog views where audit history exceeds the client window.
2. **Direct Cross-Database SQL JOIN:** Joining `db_analytics.audit_records` directly with `db_users.users` in a single SQL query.
   - *Rejected:* Violates Hexagonal Architecture and the project's strict three-database boundary (`db_articles`, `db_users`, `db_analytics` run on isolated connection pools and may reside on separate database servers, especially under the hybrid on-premise topology documented in `docs/deploy/local-onpremise-runbook.md`).

## Consequences

- **Positive:**
  - Complete, end-to-end truth in audit authorship visible to supervisors across desktop and mobile catalog interfaces.
  - Zero cross-database SQL leakage: cross-context resolution is handled strictly at the Pure Fabrication application service layer (`ArticleCatalogOrchestrator`).
  - Fully testable via TDD with explicit Red/Green boundaries.
  - Mock and API data providers remain 100% symmetric.
- **Negative / Operational Considerations:**
  - `ArticleCatalogOrchestrator` requires `user_repository` injection in FastAPI dependency injection (`backend/api/dependencies/services.py`).
  - Slight latency increase in catalog retrieval when resolving unique user IDs in memory, mitigated by batch querying users per tenant (`list_by_tenant` or set of user IDs).
