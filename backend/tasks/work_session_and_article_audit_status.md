# Technical Specification: WorkSession Entity & Dynamic Article Audit Status

## Executive Summary
This document provides a comprehensive specification for introducing the `WorkSession` domain entity in `db_analytics`, linking audit events (`audit_records`) to specific daily work sessions, calculating article audit status (`fue_auditado`) dynamically, and exposing a standardized paginated endpoint (`GET /api/v1/articles`) to query articles alongside their daily audit status.

---

## 1. Database & ORM Layer (`db_analytics`)

### 1.1 New Entity: `WorkSession` (`work_sessions` table)
A new ORM model `WorkSession` will be added to [analytics.py](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/adapters/repositories/models/analytics.py) under `BaseAnalytics`.

* **Table Name**: `work_sessions`
* **Schema Definition**:
  * `session_id` (`BigInteger`, PK, autoincrement): Unique session identifier.
  * `tenant_id` (`Integer`, FK -> `record_tenants.tenant_id`, `nullable=False`): Multi-tenant isolation.
  * `branch_id` (`Integer`, `nullable=False`): Branch/sucursal identifier for the work session.
  * `opened_at` (`DateTime`, `nullable=False`): Session start timestamp (initialized at 00:00:00 of the day).
  * `closed_at` (`DateTime`, `nullable=True`): Session end timestamp (initialized at 23:59:59 of the day or closed explicitly).
  * `status` (`String(20)`, `nullable=False`, default `"OPEN"`): Session state (`"OPEN"`, `"CLOSED"`).
  * `created_at` (`DateTime`, default `datetime.utcnow`, `nullable=False`).

* **Indexes**:
  * `Index("idx_work_sessions_lookup", "tenant_id", "branch_id", "opened_at", "closed_at")`
  * `Index("idx_work_sessions_status", "tenant_id", "branch_id", "status")`

---

### 1.2 `AuditRecord` Schema Update
Update `AuditRecord` in [analytics.py](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/adapters/repositories/models/analytics.py) to reference `WorkSession`:

* **Column Addition**:
  * `session_id` (`BigInteger`, FK -> `work_sessions.session_id`, `nullable=False`): Foreign key linking each audit record scan to its active work session.
* **Relationship**:
  * `work_session: Mapped["WorkSession"] = relationship(back_populates="audit_records")`
* **Index**:
  * `Index("idx_audit_session_article", "session_id", "article_code")`: Optimized for instant audit status verification (`EXISTS` queries).

---

### 1.3 Database Migration (Alembic)
* Create a new migration file in `backend/migrations/versions_analytics/` (e.g., `add_work_sessions_table_and_session_id_fk.py`).
* Operations:
  1. Create `work_sessions` table with primary key, foreign keys, and indexes.
  2. Add `session_id` column to `audit_records`.
  3. Add Foreign Key constraint `fk_audit_records_session_id` referencing `work_sessions.session_id`.
  4. Add index `idx_audit_session_article` on `audit_records(session_id, article_code)`.

---

## 2. Work Session Business Logic & Lifecycle

### 2.1 Daily Session Bounds & Auto-Resolution
* **Daily Bound Rule**: Each work session represents a full calendar day from **00:00:00** to **23:59:59 (24 hours)** for a given `tenant_id` and `branch_id`.
* **Session Provider / Service** (`WorkSessionService` in `backend/app/analytics/` or `backend/app/work_sessions/`):
  * Method: `get_or_create_active_session(tenant_id: int, branch_id: int, current_dt: Optional[datetime] = None) -> WorkSession`
  * Logic:
    1. Determine current day boundaries (`start_of_day = 00:00:00`, `end_of_day = 23:59:59.999999`).
    2. Query `work_sessions` where `tenant_id = active_tenant`, `branch_id = active_branch`, and `opened_at <= current_dt <= closed_at`.
    3. If found, return existing `session_id`.
    4. If no session exists for the current day, automatically create and persist a new `WorkSession` record covering the full 24-hour range (`opened_at = start_of_day`, `closed_at = end_of_day`, `status = "OPEN"`).

---

## 3. Dynamic Article Audit Status (`fue_auditado`)

### 3.1 Calculation Strategy
`fue_auditado` is **never stored staticly** in database tables. Instead, it is projected dynamically during query time to preserve database normalization and guarantee 100% data consistency.

### 3.2 SQL Query Pattern (`EXISTS` Subquery)
When fetching articles for a tenant and branch, the query performs an indexed `EXISTS` check against `audit_records` using the active daily `session_id`:

```sql
SELECT 
    a.id_empresa,
    a.id_articulo AS article_code,
    a.descripcion,
    a.id_familia,
    a.id_grupo,
    EXISTS (
        SELECT 1 
        FROM db_analytics.audit_records ar 
        WHERE ar.session_id = :active_session_id 
          AND ar.article_code = a.id_articulo
    ) AS fue_auditado
FROM db_articles.articulos a
WHERE a.id_empresa = :active_empresa
ORDER BY a.descripcion ASC
LIMIT :limit OFFSET :offset;
```

### 3.3 Evaluation Rules
* **`fue_auditado = True`**: At least one record exists in `audit_records` for `article_code` linked to `:active_session_id`.
* **`fue_auditado = False`**: Zero records exist in `audit_records` for `article_code` linked to `:active_session_id`.

---

## 4. API Endpoints & Request / Response DTOs

### 4.1 Get All Articles Endpoint (`GET /api/v1/articles`)
* **File Path**: `backend/api/v1/articles.py`
* **Route**: `GET /api/v1/articles` (or `/api/v1/articulos`)
* **Headers**: `Authorization: Bearer <jwt_token>` (Extracts `tenant_id` and `branch_id`).
* **Query Parameters**:
  * `page` (`int`, default `1`, min `1`)
  * `limit` (`int`, default `50`, min `1`, max `200`)
  * `search` (`Optional[str]`): Search filter by article code or description (`LIKE %search%`).
  * `id_familia` (`Optional[str]`): Filter by family code.
  * `id_grupo` (`Optional[str]`): Filter by group code.
  * `fue_auditado` (`Optional[bool]`): Optional filter to return only audited (`true`) or non-audited (`false`) articles.

* **Response Payload (JSON)**:
```json
{
  "items": [
    {
      "id_empresa": 1,
      "id_articulo": "ART-00123",
      "descripcion": "PARACETAMOL 500MG X 20 COMPRIMIDOS",
      "id_familia": "FAM-01",
      "id_grupo": "GRP-05",
      "fue_auditado": true
    },
    {
      "id_empresa": 1,
      "id_articulo": "ART-00124",
      "descripcion": "IBUPROFENO 400MG X 10 COMPRIMIDOS",
      "id_familia": "FAM-01",
      "id_grupo": "GRP-05",
      "fue_auditado": false
    }
  ],
  "total": 1420,
  "page": 1,
  "limit": 50,
  "pages": 29
}
```

### 4.2 Get Single Article Endpoint (`GET /api/v1/articles/{id_articulo}`)
* **Route**: `GET /api/v1/articles/{id_articulo}`
* **Response Payload (JSON)**: Includes article master data + dynamic `fue_auditado` boolean flag for current active work session.

---

## 5. Domain Models & Schemas Update

### 5.1 Article Domain Model (`backend/app/articles/models.py`)
Add `fue_auditado: bool = False` to `ArticuloResponse` / `Articulo` DTO.

```python
class ArticuloResponse(BaseModel):
    id_empresa: int
    id_articulo: str
    descripcion: str
    id_familia: Optional[str] = None
    id_grupo: Optional[str] = None
    fue_auditado: bool = False

    class Config:
        from_attributes = True
```

---

## 6. Implementation Checklist

1. [ ] **ORM Models**: Add `WorkSession` and update `AuditRecord` with `session_id` in `backend/adapters/repositories/models/analytics.py`.
2. [ ] **Alembic Migration**: Generate and verify Alembic migration script for `db_analytics` schema.
3. [ ] **WorkSession Service**: Implement `WorkSessionService` to manage daily 00:00 to 24:00 session resolution.
4. [ ] **Repository Layer**: Update article and audit repositories to execute `EXISTS` subqueries incorporating `session_id`.
5. [ ] **Domain Models & DTOs**: Add `fue_auditado` boolean field to `ArticuloResponse`.
6. [ ] **API Endpoint**: Implement / update `GET /api/v1/articles` and `GET /api/v1/articles/{id_articulo}` with pagination and filters.
7. [ ] **Automated Testing**: Write unit and integration tests covering session creation, dynamic `fue_auditado` computation, and API endpoints.
