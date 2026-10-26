# Specification: Local On-Premise Deployment Package & Verification

- **Change ID:** `local-onpremise-deployment`
- **Status:** `Approved`
- **Approved By:** fede
- **Approval Date:** 2026-10-25
- **Author Agent:** Antigravity (Gemini)
- **Initiative:** Pharmacy Branch On-Premise Local Distribution

---

## 1. Objective

Provide a robust, verified, and self-contained On-Premise Local Deployment Package for pharmacy clients. This package allows pharmacy branches to host the SaaS Stock Deposit Control auditing platform on their local server/LAN with zero cloud hosting costs, keeping their product/pricing databases private and secure, while supporting native mobile barcode scanning and web dashboard auditing.

Cloud deployment automation (via GitHub Actions SSH CD) is explicitly deferred until requested by specific clients.

---

## 2. Assumptions

- `A1:` The pharmacy client maintains their own product, pricing, and stock database (`db_articles` / MariaDB 10.x) on their local server or network.
- `A2:` For audit integrity and safety, the client grants the application **read-only** credentials (`SELECT`) to their `db_articles` database.
- `A3:` The application's `db_users` (authentication, auditor accounts) and `db_analytics` (audit sessions, barcode scan history, discrepancy reports) are hosted on the pharmacy host via the bundled MariaDB container (`COMPOSE_PROFILES=with-db`), incurring zero cloud fees.
- `A4:` Native Expo mobile app (`frontend-mobile`) accesses the device camera via native hardware permissions, which operate over plain HTTP on the local network (`http://<lan-ip>:8080`). Modern desktop/mobile web browsers (`frontend-web`) enforce secure context requirements (`https://` or `localhost`) for browser-based camera access.
- `A5:` Target pharmacy host servers may already run existing software on standard web ports (`80`, `443`), requiring configurable or non-colliding ingress port bindings.

---

## 3. Tech Stack & Reference Commands

Inherited from project [AGENTS.md](file:///home/fede/Proyectos/SaaSStockDepositControl/AGENTS.md):

- **Backend Runtime:** Python 3.12, FastAPI, SQLAlchemy 2.0 (asyncio + aiomysql), Alembic, Uvicorn
- **Frontend Web Runtime:** Next.js (Standalone output), Node 20 LTS
- **Mobile Runtime:** Expo SDK 57, React Native 0.86 (AsyncStorage dynamic server URL)
- **Ingress Gateway:** Caddy 2.8+ Alpine
- **Database Engine:** Bundled MariaDB 10.11 LTS (`with-db` profile) + External MariaDB/MySQL 8 compatibility
- **Verification Commands:**
  - Compose validation: `docker compose config -q` (and with profiles: `docker compose --profile with-db config -q`)
  - Shell syntax: `bash -n backend/docker-entrypoint.sh scripts/devops/deploy.sh`
  - Backend tests: `pytest` (from `backend/`)
  - Web tests: `npm test` (from `frontend-web/`)
  - Mobile health: `npx expo-doctor` (from `frontend-mobile/`)

---

## 4. Module Boundaries & Deployment Topologies

```mermaid
flowchart TD
    subgraph PharmacyLAN["Pharmacy Branch Local Network (LAN)"]
        ClientMobile["Auditor Mobile Device<br/>(Expo App - Native Camera)"] -->|":8080 HTTP"| Proxy["Caddy Ingress Proxy"]
        ClientDesktop["Admin / Auditor PC<br/>(Web Browser)"] -->|":8080 HTTP"| Proxy

        Proxy -->|"/api/*"| Backend["FastAPI Backend Container"]
        Proxy -->|"/*"| Web["Next.js Web Container"]

        subgraph LocalDocker["Docker Compose (with-db)"]
            Backend
            Web
            Proxy
            MariaDB["Bundled MariaDB 10.11<br/>(127.0.0.1:3306)"]
            MariaDB -.->|"db_users (auth)"| Backend
            MariaDB -.->|"db_analytics (scans/kpi)"| Backend
        end

        subgraph PharmacyHost["Pharmacy Host Server / ERP"]
            PharmacyDB[("Existing Pharmacy DB<br/>db_articles (Read-Only)")]
        end

        Backend -->|"host.docker.internal / LAN IP<br/>(Read-Only SELECT)"| PharmacyDB
    end
```

### 4.1 Topology Components
1. **Application Core:** `backend`, `web`, and `proxy` containers running as non-root users from GHCR multi-arch images.
2. **Local Identity & Audit Storage:** `mariadb` container bound exclusively to `127.0.0.1`, holding `db_users` and `db_analytics`.
3. **Pharmacy Read-Only Ingestion:** `backend` connecting to `ARTICLES_DATABASE_URL` via `host.docker.internal` or local LAN IP.

---

## 5. Configuration & Environment Contracts

### 5.1 Environment Variables Matrix (`.env.example`)
```ini
# ─── Target Profile ───
COMPOSE_PROFILES=with-db

# ─── Ingress ───
SERVER_NAME=:8080
HTTP_PORT=8080
# Optional host bindings for 80/443 (leave empty or unset if ports are occupied by host services)
BIND_HOST_PORTS=false

# ─── Application Security ───
ENVIRONMENT=production
# Generate with: python3 -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY=<generate-min-32-chars>
ACCESS_TOKEN_EXPIRE_MINUTES=480

# ─── Granular Migration Control ───
RUN_MIGRATIONS=true
RUN_MIGRATIONS_ARTICLES=false      # Set to false for external read-only pharmacy DB!
RUN_MIGRATIONS_USERS=true
RUN_MIGRATIONS_ANALYTICS=true

# ─── Database Routing ───
# Bundled MariaDB credentials:
DB_HOST=mariadb
DB_PORT=3306
DB_USER=app_user
DB_PASSWORD=<secure-app-password>
MARIADB_ROOT_PASSWORD=<secure-root-password>
MARIADB_APP_PASSWORD=<secure-app-password>

# External Pharmacy Database (Read-Only):
ARTICLES_DATABASE_URL=mysql+aiomysql://ro_user:ro_pass@host.docker.internal:3306/db_articles
USERS_DATABASE_URL=mysql+aiomysql://app_user:<secure-app-password>@mariadb:3306/db_users
ANALYTICS_DATABASE_URL=mysql+aiomysql://app_user:<secure-app-password>@mariadb:3306/db_analytics
```

---

## 6. Acceptance Criteria (Behavioural & Testable)

### `S1`: Granular Migration Execution on Startup
- **Given:** A backend deployment configured with `RUN_MIGRATIONS=true`, `RUN_MIGRATIONS_ARTICLES=false`, `RUN_MIGRATIONS_USERS=true`, and `RUN_MIGRATIONS_ANALYTICS=true`.
- **When:** `backend/docker-entrypoint.sh` executes on container boot.
- **Then:** It skips `alembic.ini` (leaving `db_articles` completely untouched and writable permissions unneeded), while executing `alembic_users.ini upgrade head` and `alembic_analytics.ini upgrade head` successfully before spawning `uvicorn`.

### `S2`: Backward Compatibility of Migration Master Switch
- **Given:** A deployment using the legacy configuration where only `RUN_MIGRATIONS=true` is set, and `RUN_MIGRATIONS_ARTICLES`, `RUN_MIGRATIONS_USERS`, `RUN_MIGRATIONS_ANALYTICS` are unset.
- **When:** `backend/docker-entrypoint.sh` executes.
- **Then:** All three migration configs (`alembic.ini`, `alembic_users.ini`, `alembic_analytics.ini`) execute, preserving full backward compatibility. If `RUN_MIGRATIONS=false`, all migrations are skipped regardless of sub-switches.

### `S3`: Non-Conflicting Ingress Port Mapping
- **Given:** A target host server where ports `80` and `443` are already occupied by host services.
- **When:** `docker compose --profile with-db up` is executed with `SERVER_NAME=:8080` and `HTTP_PORT=8080` (with 80/443 bindings disabled or parameterized).
- **Then:** Docker Compose starts successfully without port collision errors (`bind: address already in use`), listening exclusively on `HTTP_PORT`.

### `S4`: Multi-Database Health Check Verification
- **Given:** The stack is started where `db_articles` points to an external MySQL/MariaDB database and `db_users` / `db_analytics` point to the bundled MariaDB container.
- **When:** Probing `GET /api/v1/health` through the Caddy proxy (`curl -f http://localhost:8080/api/v1/health`).
- **Then:** The response status is HTTP 200, returning `{"status": "healthy", "databases": {"articles": "connected", "users": "connected", "analytics": "connected"}}`.

### `S5`: Camera Scanner Operational Documentation & Guidelines
- **Given:** An on-premise local deployment accessed via plain HTTP (`http://<lan-ip>:8080`).
- **When:** A pharmacy operator consults the deployment guide [docs/deploy/README.md](file:///home/fede/Proyectos/SaaSStockDepositControl/docs/deploy/README.md).
- **Then:** The runbook clearly documents that mobile auditing devices must use the Expo mobile application for native camera hardware access over HTTP, and provides the step-by-step procedure for local network mobile connectivity.

---

## 7. Risks, Edge Cases & Failure Modes

- **Risk 1: Host Gateway Resolution on Linux:** `host.docker.internal` is natively supported in Docker Engine 20.10+ via `extra_hosts: ["host.docker.internal:host-gateway"]`. On older Docker engines, the host LAN IP must be specified directly in `ARTICLES_DATABASE_URL`.
- **Risk 2: MySQL 8 Authentication Compatibility:** Legacy MySQL 8 servers use `caching_sha2_password` by default, whereas `aiomysql` over unencrypted plain connection requires `mysql_native_password`. The runbook must include the exact GRANT command.
- **Risk 3: Accidental Schema Mutation:** If `RUN_MIGRATIONS_ARTICLES` is accidentally enabled against an external pharmacy DB with DDL permissions, Alembic could attempt schema alterations. The runbook must mandate a read-only database user (`GRANT SELECT ON ...`).

---

## 8. Boundaries & Out of Scope

- **In Scope:**
  - Granular migration switches in `backend/docker-entrypoint.sh`.
  - Ingress port parameterization in `docker-compose.yml`.
  - Environment variable documentation in `.env.example`.
  - Comprehensive On-Premise Pharmacy Deployment & Verification Runbook in `docs/deploy/README.md`.
  - Automated smoke test / verification script for the local bundle.
- **Out of Scope (Deferred):**
  - Provisioning GitHub repository secrets (`STAGING_SSH_*`, `PROD_SSH_*`) and variables (`STAGING_DOMAIN`, `PROD_DOMAIN`).
  - Automated CD deployment over SSH to external cloud VPS.
  - Multi-tenant cloud SaaS database consolidation.

---

## 9. Resolved Design Questions & Approvals

- [x] `Q1:` Does the pharmacy's database use MariaDB 10.x or MySQL 8.0?
  - **Resolution:** Confirmed MariaDB 10.x. Uses standard MariaDB user grants (`GRANT SELECT ON db_articles.* TO 'ro_user'@'%' IDENTIFIED BY '...'`) and `utf8mb4_unicode_ci` collation.
- [x] `Q2:` Will the auditor mobile devices connect to the local server via Wi-Fi LAN or mobile data/tunnel?
  - **Resolution:** **Hybrid Ingress Architecture (Wi-Fi LAN + Tunnel Fallback)**:
    - **Primary (In-Branch LAN):** Direct Wi-Fi access to `http://<lan-ip>:8080` via Expo mobile app. Fast, low latency, and zero dependency on branch internet connectivity (continues operating during ISP dropouts).
    - **Fallback / Off-LAN (Cloudflare Tunnel):** For auditors operating outside the local Wi-Fi or across branch offices without opening inbound firewall ports on the pharmacy router, run `--profile with-db,tunnel` with `CLOUDFLARE_TUNNEL_TOKEN`.
    - **Runtime Switching:** Auditor selects the URL on the Expo login screen (cached in `AsyncStorage`).

