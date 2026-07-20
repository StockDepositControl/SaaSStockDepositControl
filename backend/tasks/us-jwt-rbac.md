# TASK: Implement US-05 — JWT Authentication and Three-Level RBAC Skeleton

## 1. Context & Objectives
We are establishing the security foundation for "Global Medica (Phase 1)". Your task is to implement **US-05 (JWT Authentication and Three-Level RBAC Skeleton)**. This story sets up secure, stateless JWT authentication and a robust Role-Based Access Control (RBAC) engine. It must cleanly integrate with our Hexagonal Architecture, ensuring domain-level purity while preparing hook points for Phase 2 multi-tenancy.

---

## 2. Technical Constraints & Standards
You must strictly adhere to the following guardrails during implementation:
* **Hexagonal Architecture Boundaries:** * Domain layer (`backend/app/domain/`) must remain 100% pure. It MUST NOT import external frameworks (e.g., FastAPI, SQLAlchemy, Alembic).
    * Define contracts as abstract **Ports** in the application layer (`backend/app/application/ports/`).
    * Implement concrete adapters (e.g., JWT handlers, hashing utilities) inside the infrastructure layer (`backend/app/adapters/` or `backend/api/` for endpoints).
* **JWT Terminology:** Use "decode/verify" the token in all code comments, docstrings, and messages. Never use "decrypt", as the JWT is signed, not encrypted.
* **Financial Precision (Decimal):** Absolutely no `float` types are allowed for monetary or financial representation. Ensure any schema or model referencing price/costs (such as prepping the ground for `pcio_com_siva`) imports and uses `decimal.Decimal`.
* **Database Constraints:** This is a MariaDB project. Do not write PostgreSQL-specific syntax or RLS triggers.

---

## 3. Explicit Acceptance Criteria to Implement
You are expected to build and verify the following components:

### A. Domain Roles Representation (Domain)
* Define the three system roles: `administrador`, `supervisor`, and `auditor` as a strict Python `Enum` inside the domain.

### B. Ports & Adapters for Security (Application & Infrastructure)
* **TokenProvider Port:** Create an abstract interface in `application/ports/` for generating, decoding, and verifying JWTs.
* **PyJWT Adapter:** Implement the Port in `infrastructure/security/` using `PyJWT`.
* **Password Hashing Port & Adapter:** Provide secure hashing/verification interfaces and implementations using `bcrypt` or `Argon2`.

### C. FastAPI Authentication Dependency & Field-Level RBAC
* **Authentication Dependency:** Create a reusable FastAPI dependency (or middleware) that:
    1. Extracts and decodes/verifies incoming JWTs.
    2. Extracts user data: `role` and `id_sucursal` (tenant_id).
    3. Exposes this context dynamically for downstream database routing.
* **Role Restriction Guards:** Implement a decorator or dependency to restrict API routes dynamically based on allowed roles (e.g., `RoleChecker(["administrador"])`).
* **Field-Level Enforcement Hook:** Implement a prototype Pydantic response serializer/schema hook designed to dynamically strip/exclude sensitive fields (such as `pcio_com_siva`) if the resolved user role is not `administrador`. *Note: Do not implement the actual stock database query logic yet, just build and test the schema-level conditional field-stripping mechanism.*

### D. REST Endpoint
* Create `POST /api/v1/auth/login` accepting credentials and returning a signed JWT containing the user's role and `id_sucursal` as claims.

### E. Unit Testing
* Write unit tests in the appropriate directory.
* Mock infrastructure Ports. 
* Test cases must cover: 
    1. Successful login and token emission.
    2. Request with a valid token.
    3. Request with an expired/invalid token.
    4. Request with insufficient role privileges.

---

## 4. Required Execution Workflow (Skills & Tooling)
To successfully resolve this story, you must invoke the following tools and skills sequentially:
1.  **Codebase Query:** Query the `codebase-memory` MCP server to inspect the existing monorepo structure, FastAPI bootstrapping files (`HU-03`), and database models to ensure alignment.
2.  **Verify Architecture:** Call the `architecture-patterns` skill to validate your planned directory layouts for the token ports/adapters.
3.  **Implement & Document:** Code the domain components first, then application Ports, then adapters, and finally HTTP interfaces. Use `fastapi-pro` and `auth-implementation-patterns` skills for expert-level implementation insights
4.  **Test Suite Execution:** Run `pytest-skill` to execute your tests with clean mock fixtures. Ensure 100% test pass rate.
5.  **Final Quality Check:** Invoke `check-hexagonal` to ensure that no forbidden infrastructure imports leaked into the domain layers. Do not mark the task as complete unless this validation passes.