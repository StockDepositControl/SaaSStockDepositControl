## Action Plan for US-05: JWT Authentication and Three-Level RBAC Skeleton

### 1. Domain Layer Updates (`backend/app/`)
- [x] **Users Domain (`backend/app/users/models.py`)**:
  - Verify `UserRole` enum.
  - Add schemas: `AuthToken` and `LoginCredentials`.
- [x] **Articles Domain (`backend/app/articles/models.py`)**:
  - Define `ArticuloPublicOut` (excludes `pcio_com_siva`).
  - Define `ArticuloAdminOut` (includes `pcio_com_siva`).

### 2. Application Layer Ports (`backend/app/ports/`)
- [x] **Security Ports (`backend/app/ports/security.py`)**:
  - Define abstract `TokenProvider` port.
  - Define abstract `PasswordHasher` port.

### 3. Infrastructure Layer Adapters (`backend/adapters/`)
- [x] **JWT Provider (`backend/adapters/security/jwt_provider.py`)**:
  - Implement `PyJWTTokenProvider` using PyJWT.
- [x] **Password Hasher (`backend/adapters/security/password_hasher.py`)**:
  - Implement `BcryptPasswordHasher` using bcrypt.

### 4. Primary Adapters / API Layer (`backend/api/`)
- [x] **Dependency Injection (`backend/api/dependencies/__init__.py`)**:
  - Add singleton provider getters for token and password hashing adapters.
- [x] **Tenant Auth Middleware (`backend/api/middlewares/tenant_auth.py`)**:
  - Extract `id_sucursal` (tenant_id) from verified JWT and bind to async contextvar.
- [x] **Auth Route/Dependencies (`backend/api/dependencies/auth.py`)**:
  - Implement dynamic route guards (`RoleChecker`) and `get_current_user` dependency.
- [x] **Login Router (`backend/api/v1/auth.py`)**:
  - Create route `POST /api/v1/auth/login` to emit signed tokens.
- [x] **Main App Bootstrapping (`backend/api/main.py`)**:
  - Register `TenantAuthMiddleware` and `auth` router.

### 5. Verification & Testing
- [x] Write unit tests verifying token emission, role guard access, schema restriction.
- [x] Run pytest suite.
