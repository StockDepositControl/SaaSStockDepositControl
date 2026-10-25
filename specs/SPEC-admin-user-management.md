### ASSUMPTIONS I'M MAKING

1. **Soft Deactivation Only**: Users must never be permanently deleted from the database because historical stock audit logs and work sessions link to `user_id`. Deactivating sets `is_active = False`.
2. **Tenant Isolation**: An administrator can only see and manage users belonging to their own `tenant_id` (extracted from the verified JWT claims).
3. **Anti-Lockout Invariants**: An administrator cannot deactivate their own active account, nor remove the `administrador` role from themselves if they are the only active administrator in the tenant.
4. **Role Model**: System roles correspond strictly to the existing domain enum: `administrador`, `supervisor`, and `auditor`.
5. **No Schema Changes Required**: The `users`, `roles`, and `user_roles` relational tables already exist in `db_users` with all required foreign keys and indexes.

---

# Spec: Administrator User Management & Role Assignment

> [!NOTE]
> **Implementation Status: Implemented** — This specification has been fully implemented in [`backend/api/v1/users.py`](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/api/v1/users.py), [`backend/app/users/services.py`](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/app/users/services.py), [`frontend-web/lib/adapters/ApiDataClient.ts`](file:///home/fede/Proyectos/SaaSStockDepositControl/frontend-web/lib/adapters/ApiDataClient.ts), and [`frontend-web/app/users/page.tsx`](file:///home/fede/Proyectos/SaaSStockDepositControl/frontend-web/app/users/page.tsx).

## 1. Objective

Enable tenant administrators to view all organization users, toggle user activation status (deactivate / reactivate), and assign operational roles (`administrador`, `supervisor`, `auditor`) through a dedicated administrative interface and secure backend API.

### Business Value & Context

In warehouse inventory and audit operations, staff turnover and role reassignments occur frequently. Administrators need full control over who has access to the mobile audit tools and web management consoles. Preserving audit traceability requires soft-deactivation instead of physical deletion.

---

## 2. Tech Stack & Affected Surfaces

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Pydantic V2, Pytest
- **Persistence**: MariaDB (`db_users`), tables: `users`, `roles`, `user_roles`
- **Frontend Web**: Next.js 16 (App Router), React 19, TypeScript, Vitest, Tailwind CSS
- **Architecture**: Hexagonal Architecture / Ports & Adapters with strict tenant isolation

---

## 3. Commands

### Backend

- **Run Tests**: `pytest backend/tests/api/test_users_routes.py`
- **Run Dev Server**: `uvicorn backend.api.main:app --reload`
- **Run Linting**: `ruff check backend/` or `flake8 backend/`

### Frontend

- **Run Tests**: `npm test` (inside `frontend-web/`)
- **Run Dev Server**: `npm run dev` (inside `frontend-web/`)
- **Typecheck & Build**: `npm run build` (inside `frontend-web/`)

---

## 4. Project Structure & Affected Surfaces

```
specs/
└── SPEC-admin-user-management.md             → [NEW] This specification

backend/
├── app/users/
│   ├── models.py                              → [MODIFY] Add request/response schemas (UserStatusUpdate, UserRoleAssignment, UserResponse)
│   ├── ports.py                               → [MODIFY] Add list_by_tenant, update_status, update_roles to UserRepositoryPort
│   └── services.py                            → [MODIFY] Add UserService with tenant boundaries & anti-lockout validations
├── adapters/repositories/
│   └── user_repository.py                     → [MODIFY] Implement listing with filter, status toggle, and role association update
├── api/
│   ├── dependencies/services.py               → [MODIFY] Add get_user_service dependency factory
│   ├── v1/users.py                            → [NEW] Admin-only REST endpoints (GET /, PATCH /{id}/status, PUT /{id}/roles)
│   └── main.py                                → [MODIFY] Mount /api/v1/users router
└── tests/api/
    └── test_users_routes.py                   → [NEW] Integration tests for user management & RBAC

frontend-web/
├── lib/
│   ├── types/
│   │   ├── api.ts                             → [MODIFY] Add user management payload DTOs
│   │   └── domain.ts                          → [MODIFY] Ensure MockUser/User contracts match API responses
│   ├── ports/
│   │   └── DataClientPort.ts                  → [MODIFY] Add updateUserStatus and updateUserRole methods
│   ├── adapters/
│   │   ├── ApiDataClient.ts                   → [MODIFY] Implement real HTTP calls for user listing & mutations
│   │   └── ApiDataClient.test.ts              → [MODIFY] Add tests for user management API calls
│   └── mocks/
│       └── MockDataContext.tsx                → [MODIFY] Add stateful mock implementations for status and roles
└── app/users/
    └── page.tsx                               → [MODIFY] Replace mock toggle with ApiDataClient calls and add role selector UI
```

---

## 5. Architectural Context & Design Decisions

### Hexagonal Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PRIMARY ADAPTER: backend/api/v1/users.py                                        │
│ - Enforces RoleChecker(["administrador"])                                       │
│ - Extracts tenant_id & requesting user_id from verified JWT claims              │
│ - Validates DTOs with Pydantic V2                                               │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ APPLICATION / DOMAIN SERVICE: UserService (backend/app/users/services.py)      │
│ - Invariant 1: Target user must belong to caller's tenant_id                   │
│ - Invariant 2: Cannot deactivate own account (anti-lockout)                     │
│ - Invariant 3: Cannot remove admin role from oneself if last active admin       │
│ - Emits pure domain User models                                                 │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ SECONDARY ADAPTER: SQLAlchemyUserRepository (backend/adapters/repositories/)    │
│ - Operates exclusively on get_users_session_factory() (db_users)                │
│ - Uses selectinload(UserORM.roles) to avoid N+1 query overhead                  │
│ - Mutates status flag and synchronizes user_roles relationship                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Key Decisions & Rationale

1. **Explicit Endpoints vs. Generic PATCH**:
   - `PATCH /api/v1/users/{user_id}/status`: Single-purpose endpoint for deactivation/reactivation. Prevents unintended mass updates.
   - `PUT /api/v1/users/{user_id}/roles`: Dedicated role assignment endpoint requiring explicit role lists.
2. **Anti-Lockout Protection**:
   Attempting to deactivate the requesting administrator or demote the sole administrator raises a `BusinessRuleViolationException` (HTTP 400), preventing accidental lockout of the tenant.
3. **Audit History Preservation**:
   Users are never physically deleted. `is_active: False` invalidates login attempts in `AuthService.authenticate` immediately, while leaving historical records untouched.

---

## 6. Code Style & Implementation Specifications

### Domain Schemas (`backend/app/users/models.py`)

```python
class UserStatusUpdate(BaseModel):
    is_active: bool

class UserRoleAssignment(BaseModel):
    roles: List[UserRole]

class UserResponse(BaseModel):
    user_id: int
    tenant_id: int
    first_name: str
    last_name: str
    email: str
    branch_id: Optional[int] = None
    is_active: bool
    roles: List[UserRole]

    model_config = ConfigDict(from_attributes=True)
```

### Domain Service (`backend/app/users/services.py`)

```python
class UserService:
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository

    async def list_users(self, tenant_id: int, include_inactive: bool = True) -> list[User]:
        return await self.user_repository.list_by_tenant(tenant_id=tenant_id, include_inactive=include_inactive)

    async def update_status(self, tenant_id: int, target_user_id: int, is_active: bool, actor_user_id: int) -> User:
        if target_user_id == actor_user_id and not is_active:
            raise BusinessRuleViolationException("Administrators cannot deactivate their own account")
        
        user = await self.user_repository.get_by_id(tenant_id=tenant_id, user_id=target_user_id, include_inactive=True)
        if not user:
            raise EntityNotFoundException(f"User {target_user_id} not found in this tenant")
            
        return await self.user_repository.update_status(tenant_id=tenant_id, user_id=target_user_id, is_active=is_active)

    async def assign_roles(self, tenant_id: int, target_user_id: int, roles: list[UserRole], actor_user_id: int) -> User:
        if not roles:
            raise BusinessRuleViolationException("A user must have at least one role assigned")
            
        user = await self.user_repository.get_by_id(tenant_id=tenant_id, user_id=target_user_id, include_inactive=True)
        if not user:
            raise EntityNotFoundException(f"User {target_user_id} not found in this tenant")

        if target_user_id == actor_user_id and UserRole.ADMINISTRADOR not in roles:
            raise BusinessRuleViolationException("Administrators cannot remove the administrator role from themselves")

        return await self.user_repository.update_roles(tenant_id=tenant_id, user_id=target_user_id, roles=roles)
```

### API Router (`backend/api/v1/users.py`)

```python
router = APIRouter()
require_admin = RoleChecker(allowed_roles=["administrador"])

@router.get("", response_model=list[UserResponse])
async def list_users(
    include_inactive: bool = Query(default=True),
    claims: dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    tenant_id = int(claims.get("tenant_id", 1))
    return await user_service.list_users(tenant_id=tenant_id, include_inactive=include_inactive)

@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    claims: dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    tenant_id = int(claims.get("tenant_id", 1))
    actor_id = int(claims.get("id_usuario") or claims.get("user_id", 1))
    return await user_service.update_status(
        tenant_id=tenant_id, target_user_id=user_id, is_active=payload.is_active, actor_user_id=actor_id
    )

@router.put("/{user_id}/roles", response_model=UserResponse)
async def assign_user_roles(
    user_id: int,
    payload: UserRoleAssignment,
    claims: dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    tenant_id = int(claims.get("tenant_id", 1))
    actor_id = int(claims.get("id_usuario") or claims.get("user_id", 1))
    return await user_service.assign_roles(
        tenant_id=tenant_id, target_user_id=user_id, roles=payload.roles, actor_user_id=actor_id
    )
```

### Frontend UI Enhancement (`frontend-web/app/users/page.tsx`)

- Render role select element allowing quick toggle between `ADMINISTRADOR`, `SUPERVISOR`, and `AUDITOR`.
- Disable status button for the currently logged-in administrator (`isMe`), preventing accidental clicks.
- Display instant feedback (optimistic update with rollback on failure).

---

## 7. Testing Strategy

### Backend Tests (`backend/tests/api/test_users_routes.py`)

1. **RBAC Guard**:
   - Requests made with `auditor` or `supervisor` roles must return `403 FORBIDDEN`.
2. **List Users**:
   - `GET /api/v1/users` returns 200 with list of tenant users including active and inactive.
   - Cross-tenant data must never leak across `tenant_id` boundaries.
3. **Status Toggle**:
   - `PATCH /api/v1/users/{id}/status` flips `is_active` to `False` and returns updated model.
   - Self-deactivation attempt returns `400 BAD REQUEST` with explicit business rule violation message.
4. **Role Assignment**:
   - `PUT /api/v1/users/{id}/roles` with `["supervisor"]` updates associations and returns updated role list.
   - Self-demotion attempt without `administrador` returns `400 BAD REQUEST`.

### Frontend Tests (`frontend-web/lib/adapters/__tests__/ApiDataClient.test.ts`)

1. **API Client Integration**:
   - `getUsers()` queries `GET /api/v1/users`.
   - `updateUserStatus(id, false)` issues `PATCH /api/v1/users/{id}/status` with `{ is_active: false }`.
   - `updateUserRole(id, role)` issues `PUT /api/v1/users/{id}/roles` with `{ roles: [role] }`.
2. **Component Regression**:
   - `UsersPage` renders users table and prevents action on active user.

---

## 8. Boundaries

- **Always**:
  - Filter all database queries by `tenant_id`.
  - Validate role values against `UserRole` enum.
  - Keep domain services decoupled from FastAPI dependencies and SQLAlchemy models.
- **Ask First**:
  - Adding new user fields (e.g. phone number, national ID) or modifying database tables.
- **Never**:
  - Execute hard `DELETE FROM users`.
  - Permit an administrator to deactivate their own account.
  - Return hashed passwords in `UserResponse` DTO.

---

## 9. Success Criteria

- [x] `GET /api/v1/users` returns all users of the current tenant (admin-only).
- [x] `PATCH /api/v1/users/{user_id}/status` deactivates or reactivates a target user.
- [x] Self-deactivation returns HTTP 400 and is disabled in the frontend UI.
- [x] `PUT /api/v1/users/{user_id}/roles` updates the assigned role.
- [x] Deactivated users cannot log in (`/api/v1/auth/login` rejects inactive users).
- [x] `frontend-web/app/users/page.tsx` connects directly to the live backend API when `NEXT_PUBLIC_DATA_SOURCE=api`.
- [x] 100% of backend tests pass (`pytest backend/tests/api/test_users_routes.py`).
- [x] 100% of frontend tests pass (`npm test` in `frontend-web/`).

---

## 10. Open Questions

1. Should users support multiple simultaneous roles (e.g., both `supervisor` and `auditor`), or should the UI enforce single-role selection per user?

- **Answer**: The users can't support multiple simultaneous, they can only have one role at a time.
