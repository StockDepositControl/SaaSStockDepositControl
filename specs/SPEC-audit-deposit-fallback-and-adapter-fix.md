### ASSUMPTIONS I'M MAKING:
1. Multi-tenant warehouse stock in this application defaults to Warehouse/Deposit ID `1` ("Depósito Central" / default warehouse) when not explicitly specified by an operational work session or UI deposit selector.
2. The domain service `AuditService.register_single_audit` must remain strict (`id_sucursal` and `id_deposito` are mandatory domain invariants) to preserve Hexagonal/Clean Architecture boundaries; normalization and defaults belong in the primary API adapter (`backend/api/v1/stock.py`).
3. In `frontend-web`, the UI does not currently have a multi-deposit selector for regular count audits; audits target the user's branch and primary warehouse (`id_deposito: 1`), matching `frontend-mobile`'s fallback (`id_deposito: request.id_deposito || 1`).
4. `POST /api/v1/stock/audit/batch` must also receive defensive normalization so batch sync payloads with omitted branch or deposit IDs do not fail with `BusinessRuleViolationException`.

---

# Spec: Stock Audit Deposit Defensive Fallback & Web Client Adapter Hardening

## 1. Objective
Eliminate the HTTP 400 / `BusinessRuleViolationException: Branch ID (id_sucursal) and Deposit ID (id_deposito) are required` error when submitting stock audits.

### Root Cause Analysis
1. **Domain Contract**: Stock records are stored and tracked per `(tenant_id, id_sucursal, id_deposito, id_articulo)`. The domain use case `AuditService.register_single_audit` strictly validates that both `id_sucursal` and `id_deposito` are integers.
2. **Web Client Omission**: `frontend-web/lib/adapters/ApiDataClient.ts#registerAudit` sends `{ id_articulo, stock_fisico_contado, observation }`, completely omitting `id_deposito` and `id_sucursal`.
3. **Incomplete Backend Route Hydration**: In `backend/api/v1/stock.py#register_single_audit`, the endpoint auto-fills `id_sucursal` from JWT `claims["branch_id"]` if missing, but JWT claims do not contain `id_deposito`, leaving `effective_entry.id_deposito` as `None`.
4. **Endpoint Inconsistency**: Sibling endpoints like `GET /api/v1/stock/position` and `GET /api/v1/stock/kpis` already implement defensive defaults (`resolved_deposito = id_deposito if id_deposito is not None else 1`).

This specification establishes a robust dual-layer fix:
- **Layer 1 (Backend Primary Adapter)**: Defensive fallback in `/stock/audit` and `/stock/audit/batch` ensuring omitted `id_deposito` defaults to `1` and omitted `id_sucursal` defaults to JWT `claims["branch_id"]` or `1`.
- **Layer 2 (Frontend Client Adapter)**: Explicit contract compliance in `ApiDataClient.ts` passing `id_deposito: entry.id_deposito ?? 1` and `id_sucursal`.

---

## 2. Tech Stack & Affected Surfaces
- **Backend**: Python 3.12, FastAPI, Pydantic v2, Pytest
- **Frontend**: Next.js 16 (App Router), TypeScript 5.x, Vitest
- **Architecture**: Hexagonal Architecture / Ports & Adapters

---

## 3. Commands
- **Backend Tests**: `./backend/venv/bin/pytest backend/tests/api/test_stock_routes.py`
- **Frontend Tests**: `npm test` (inside `frontend-web/`)
- **Frontend Typecheck**: `npm run build` (inside `frontend-web/`)

---

## 4. Project Structure & Affected Surfaces

```
specs/
└── SPEC-audit-deposit-fallback-and-adapter-fix.md  → [NEW] This specification

backend/
├── api/v1/
│   └── stock.py                                    → [MODIFY] Normalize `id_sucursal` and `id_deposito` in single & batch audit routes
└── tests/api/
    └── test_stock_routes.py                        → [MODIFY] Add test cases for omitted `id_deposito` and `id_sucursal`

frontend-web/
├── lib/
│   ├── types/
│   │   └── domain.ts                               → [MODIFY] Add optional `id_sucursal` and `id_deposito` to `AuditEntry`
│   └── adapters/
│       ├── ApiDataClient.ts                        → [MODIFY] Include `id_deposito` and `id_sucursal` in audit payload
│       └── ApiDataClient.test.ts                   → [MODIFY] Assert `id_deposito` and `id_sucursal` in post expectations
```

---

## 5. Architectural Context & Design Decisions

### Hexagonal Layering Contract
```
[ Frontend UI ]
      │ (AuditEntry)
      ▼
[ ApiDataClient (Secondary Adapter) ] ── (HTTP POST /audit with id_deposito: 1) ──┐
                                                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┴──┐
│ BACKEND                                                                            │
│                                                                                    │
│ [ FastAPI Route api/v1/stock.py (Primary Adapter) ]                                │
│   Defensive Normalization:                                                         │
│   - id_sucursal = entry.id_sucursal or claims["branch_id"] or 1                    │
│   - id_deposito = entry.id_deposito or 1                                           │
│          │                                                                         │
│          ▼ (Effective AuditEntryRequest with non-null branch and deposit)          │
│ [ AuditService.register_single_audit (Domain Use Case) ]                           │
│   Enforces Domain Invariants:                                                      │
│   assert id_sucursal is not None and id_deposito is not None                       │
│          │                                                                         │
│          ▼                                                                         │
│ [ StockLookupService & ArticleRepository ]                                         │
└────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Why NOT change `AuditService.register_single_audit`?**
   The domain model requires physical stock to be placed in an unambiguous location (`id_sucursal` + `id_deposito`). Silently defaulting warehouse locations inside the core domain creates hidden coupling. The primary adapter (FastAPI route) is responsible for transport normalization.

2. **Why fix BOTH Backend and Frontend?**
   - If only the frontend is fixed: third-party API clients, mobile background flushes, or older web bundles will still crash.
   - If only the backend is fixed: the frontend adapter violates explicit typing contract (`ApiAuditEntryRequest` specifies `id_deposito`) and sends implicit partial payloads.

---

## 6. Code Style & Implementation Specifications

### Backend Primary Adapter (`backend/api/v1/stock.py`)

In `register_single_audit`:
```python
    tenant_id = str(claims.get("tenant_id", "1"))
    id_usuario = int(claims.get("id_usuario") or claims.get("user_id", 1))

    # Defensive fallback normalization
    updates = {}
    if entry.id_sucursal is None:
        updates["id_sucursal"] = claims.get("branch_id") or 1
    if entry.id_deposito is None:
        updates["id_deposito"] = 1

    effective_entry = entry.model_copy(update=updates) if updates else entry
```

In `register_batch_audit`:
Apply identical normalization for batch items:
```python
    default_branch = claims.get("branch_id") or 1
    normalized_items = []
    for item in batch.items:
        updates = {}
        if item.id_sucursal is None:
            updates["id_sucursal"] = default_branch
        if item.id_deposito is None:
            updates["id_deposito"] = 1
        normalized_items.append(item.model_copy(update=updates) if updates else item)

    effective_batch = AuditBatchInput(items=normalized_items)
```

---

### Frontend Domain & Adapter (`frontend-web/`)

#### 1. Domain Types (`frontend-web/lib/types/domain.ts`)
```typescript
export interface AuditEntry {
  id_articulo: string;
  stock_fisico_contado: number;
  id_sucursal?: number | null;
  id_deposito?: number | null;
  lote?: string | null;
  observation?: string | null;
}
```

#### 2. Client Adapter (`frontend-web/lib/adapters/ApiDataClient.ts`)
```typescript
  public async registerAudit(entry: AuditEntry): Promise<AuditResult> {
    const token = this.getStoredToken();
    const claims = token ? parseJwt(token) : null;
    const branchId = entry.id_sucursal ?? (claims?.branch_id ? Number(claims.branch_id) : 1);
    const depositId = entry.id_deposito ?? 1;

    const payload: ApiAuditEntryRequest = {
      id_articulo: entry.id_articulo,
      id_sucursal: branchId,
      id_deposito: depositId,
      stock_fisico_contado: entry.stock_fisico_contado,
      observation: entry.observation || null,
    };

    const result = await this.http.post<ApiAuditEntryResult>("/api/v1/stock/audit", payload);
    const domainResult = mapToDomainAuditResult(result, entry.id_articulo, entry.observation);
    this.sessionAuditLogs.unshift(domainResult);
    return domainResult;
  }
```

---

## 7. Testing Strategy

### Backend Tests (`backend/tests/api/test_stock_routes.py`)
1. **Single Audit Route Fallback Test**:
   - `test_post_single_audit_defaults_omitted_deposit_and_branch`:
   - Send payload with only `id_articulo`, `stock_fisico_contado`, and `observation` (omitting `id_sucursal` and `id_deposito`).
   - Mock JWT claims with `branch_id = 2`.
   - Assert `audit_service.register_single_audit` is invoked with `entry.id_sucursal == 2` and `entry.id_deposito == 1`.
   - Assert response status is `201 CREATED`.

2. **Batch Audit Route Fallback Test**:
   - `test_post_batch_audit_defaults_omitted_deposit_and_branch`:
   - Send batch with an item omitting `id_sucursal` and `id_deposito`.
   - Assert all entries in batch are processed without `BusinessRuleViolationException`.

### Frontend Tests (`frontend-web/lib/adapters/ApiDataClient.test.ts`)
1. **Adapter Payload Test**:
   - Update `registerAudit posts to /api/v1/stock/audit and maps domain result`:
   - Assert `postSpy` was called with `{ id_articulo: "ART-1", id_sucursal: 1, id_deposito: 1, stock_fisico_contado: 195, observation: "Conteo físico" }`.
2. **Explicit Override Test**:
   - Call `registerAudit` with explicit `id_sucursal: 3, id_deposito: 2`.
   - Assert `postSpy` transmits `id_sucursal: 3, id_deposito: 2`.

---

## 8. Boundaries

- **Always**:
  - Run full test suites before committing (`pytest` and `npm test`).
  - Preserve strict validation in `backend/app/movements/services.py` (Domain Core).
  - Use typed `ApiAuditEntryRequest` in `ApiDataClient.ts`.
- **Ask First**:
  - Changing multi-tenant session models or introducing database migrations for dynamic deposit assignment.
- **Never**:
  - Hardcode fallback branches when JWT claims provide a valid `branch_id`.
  - Swallow exceptions in the domain layer to mask missing data.

---

## 9. Success Criteria
- [ ] `POST /api/v1/stock/audit` with `{ "id_articulo": "...", "stock_fisico_contado": 12 }` succeeds with 201 without throwing `BusinessRuleViolationException`.
- [ ] `frontend-web` submits `{ id_articulo, id_sucursal, id_deposito, stock_fisico_contado, observation }` matching backend expectations.
- [ ] Backend test suite passes (`pytest backend/tests/api/test_stock_routes.py`).
- [ ] Frontend test suite passes (`npm test` in `frontend-web/`).
- [ ] No regression in mobile offline sync or existing audit pages.

---

## 10. Open Questions
None. The fallback convention of `id_deposito: 1` is already standard across `get_article_stock_position`, `get_dashboard_kpis`, and `frontend-mobile`.
