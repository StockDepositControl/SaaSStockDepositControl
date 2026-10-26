# Implementation Tasks: Local On-Premise Deployment Package & Verification

- **Spec Reference:** `specs/local-onpremise-deployment/spec.md` (`Status` must be `Approved` before execution)
- **Delivery Strategy:** Vertical slices (`<= 400` changed lines per commit), TDD (`Red -> Green -> Refactor`), dependency-ordered.

---

## Task Breakdown

### `T1`: Granular Database Migration Control (`docker-entrypoint.sh`)
- **Covers Spec IDs:** `S1`, `S2`
- **Dependencies:** None
- **Route:** `inline` (Claude Code)
- **Risk Tier:** `low` (Startup shell script refactor)
- **Target Modules / Files:**
  - `backend/docker-entrypoint.sh`
  - `.env.example`
- **Acceptance Criteria:**
  - [x] Support `RUN_MIGRATIONS_ARTICLES` (default `true`), `RUN_MIGRATIONS_USERS` (default `true`), `RUN_MIGRATIONS_ANALYTICS` (default `true`).
  - [x] If `RUN_MIGRATIONS=false`, all migrations are skipped.
  - [x] If `RUN_MIGRATIONS_ARTICLES=false`, `alembic.ini` is skipped, protecting read-only external pharmacy databases.
  - [x] Shell script passes syntax check: `bash -n backend/docker-entrypoint.sh`.
- **Verification Command:** `bash -n backend/docker-entrypoint.sh`
- **Status:** `[x] completed` (2026-10-26, commit: `3874ece`)

---

### `T2`: Configurable Ingress Port Bindings (`docker-compose.yml`)
- **Covers Spec IDs:** `S3`
- **Dependencies:** `T1`
- **Route:** `inline` (Claude Code)
- **Risk Tier:** `low` (Docker Compose configuration)
- **Target Modules / Files:**
  - `docker-compose.yml`
  - `.env.example`
- **Acceptance Criteria:**
  - [ ] Make host port bindings for `80` and `443` configurable or conditional so target hosts with occupied ports 80/443 can run without port collision errors.
  - [ ] Default `HTTP_PORT=8080` remains functional for plain HTTP LAN access.
  - [ ] Docker Compose passes validation across profiles.
- **Verification Command:** `docker compose config -q && docker compose --profile with-db config -q`
- **Status:** `[ ] pending`

---

### `T3`: On-Premise Pharmacy Deployment Runbook & Operational Guide
- **Covers Spec IDs:** `S4`, `S5`
- **Dependencies:** `T1`, `T2`
- **Route:** `inline` (Claude Code)
- **Risk Tier:** `low` (Documentation)
- **Target Modules / Files:**
  - `docs/deploy/README.md`
  - `docs/deploy/local-onpremise-runbook.md`
- **Acceptance Criteria:**
  - [ ] Add complete end-to-end On-Premise Pharmacy Runbook detailing:
    1. Host pre-requisites (Docker Engine, memory, storage).
    2. Read-only user creation on the client's pharmacy database (`GRANT SELECT ON db_articles.* TO 'ro_user'@'%' ...`).
    3. Bundled MariaDB initialization for `db_users` and `db_analytics`.
    4. `.env` configuration template for on-premise deployments.
    5. Startup command (`./scripts/devops/deploy.sh up with-db`).
    6. Verification commands (`./scripts/devops/deploy.sh health`, `curl http://localhost:8080/api/v1/health`).
    7. Auditor mobile app connection instructions via Wi-Fi LAN.
- **Verification Command:** `test -f docs/deploy/local-onpremise-runbook.md`
- **Status:** `[ ] pending`

---

### `T4`: Automated Verification & Health Probe for Hybrid Deployment
- **Covers Spec IDs:** `S1`, `S3`, `S4`
- **Dependencies:** `T1`, `T2`, `T3`
- **Route:** `inline` (Claude Code)
- **Risk Tier:** `medium` (Validation script / backend smoke test)
- **Target Modules / Files:**
  - `backend/tests/api/test_health.py`
  - `scripts/devops/verify-local-package.sh`
- **Acceptance Criteria:**
  - [ ] Add / verify backend health endpoint tests for multi-database status.
  - [ ] Provide lightweight verification script `scripts/devops/verify-local-package.sh` that checks `.env` syntax, validates Docker Compose configuration, tests database reachability, and verifies `/api/v1/health`.
  - [ ] Verification script passes syntax check: `bash -n scripts/devops/verify-local-package.sh`.
- **Verification Command:** `pytest tests/api/test_health.py && bash -n scripts/devops/verify-local-package.sh`
- **Status:** `[ ] pending`
