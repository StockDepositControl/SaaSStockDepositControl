# 💾 Secondary Adapter Layer (`backend/adapters/`)

This layer contains the concrete infrastructure implementations used by the application. It translates the domain contracts into real SQLAlchemy repositories, JWT providers, password hashing, and database session management.

## Contents

1. `adapters/database/`: async database connection factories and tenant context helpers
2. `adapters/security/`: JWT, hashing, and authentication adapters
3. `adapters/repositories/`: repository implementations for the domain ports
4. `adapters/repositories/models/`: ORM mappings owned by the DBA side of the project

---

## Current adapter responsibilities

- `connection.py` creates the async engine and session factory for each database context
- `tenant_auth.py` binds tenant and user claims into request-scoped `ContextVar` state
- repository classes implement the port interfaces declared under `backend/app/*/ports.py`
- JWT and password adapters implement the contracts in `backend/app/ports/security.py`

---

## Strict rules

- Repositories must follow the port contract exactly and remain aligned with the domain interface.
- Repositories should not contain business rules; they should handle persistence and mapping only.
- The system is multi-database by design: each repository should work with the correct session factory for its target database.
- Tenant-scoped filtering is enforced using the current request context populated by the middleware.

---

## Ownership boundaries

- Core backend owns repository implementation files and adapter wiring.
- ORM models and migration logic remain under the DBA-managed area.
- Changes that affect schema or persistence structure should be coordinated with the DBA workflow before implementation.
