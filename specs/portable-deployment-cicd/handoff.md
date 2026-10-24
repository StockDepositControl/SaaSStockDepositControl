# Handoff: Portable Deployment + CI/CD with GitHub Actions

- **From:** Antigravity (Specification & Architecture Agent)
- **To:** Claude Code (Build Agent)
- **Spec:** [`specs/portable-deployment-cicd/spec.md`](file:///home/fede/Proyectos/SaaSStockDepositControl/specs/portable-deployment-cicd/spec.md)
- **Tasks:** [`specs/portable-deployment-cicd/tasks.md`](file:///home/fede/Proyectos/SaaSStockDepositControl/specs/portable-deployment-cicd/tasks.md)
- **Status:** Handed off for Implementation (Pending User Approval)

---

## 1. Context & Architectural Overview

The goal of this initiative is to eliminate the current development-only hosting model and deliver a portable, single-compose containerized distribution paired with enterprise-grade CI/CD automation.

### Key Architectural Invariants to Maintain:
1. **Hexagonal Architecture Preservation:** All Docker, Caddy, Alembic, and Compose changes are infrastructure concerns (`docker/`, `scripts/`, `backend/adapters/`, `.github/`). Under no circumstances should framework or container details leak into `backend/app/` (domain services, entities, ports).
2. **Multi-Database Topology:** The system manages 3 distinct logical databases (`db_articles`, `db_users`, `db_analytics`). The connection provider, health probe, Alembic environment, and CI smoke test must maintain separate engine pools and migrations across all three.
3. **Single Origin & Relative URLs:** Caddy serves as the unified ingress gateway. The frontend web application must keep `NEXT_PUBLIC_API_URL` empty, routing `/api/*` through Caddy to the backend, ensuring browser camera permissions (`getUserMedia`) function without cross-origin or insecure context blocks.
4. **Least-Privilege & Zero-Secrets:** Non-root users in containers (`appuser` 10001, `nextjs` 1001), localhost-only database ports, and strict prohibition of secrets in repos, images, or CI workflow files.

---

## 2. Decisions Recorded

| Decision | Rationale | Alternatives Considered |
|:---|:---|:---|
| **Replace Nginx with Caddy** | Automatic zero-configuration HTTPS via Let's Encrypt/ZeroSSL is essential for mobile camera barcode scanning; simple syntax handles both dev HTTP and public TLS. | Keep Nginx + Certbot container (higher operational complexity and manual renewal maintenance). |
| **Compose Service Profiles** | Allows running identical images and compose file across Client (external DB), Staging (bundled DB), Demos (seed), and Tunnel targets using `--profile`. | Multiple diverging compose files (causes config drift between environments). |
| **Real MariaDB CI Smoke Test** | Unit tests run on SQLite (`aiosqlite`), masking MariaDB-specific DDL, collation, and type incompatibilities. A real container validates migrations and rollbacks before merge. | Continuing with SQLite-only test suites. |
| **Dual-Track Production Gate** | The GitHub repo is private; GitHub Free does not support Environment protection rules (reviewers). `workflow_dispatch` with confirmation input provides a safe manual gate. | Unprotected automated deployment to production. |
| **Dynamic Mobile Server URL** | Storing the target server URL in AsyncStorage and allowing config on the login screen decouples the mobile client APK from build-time environment variables. | Re-building separate APKs for every environment via EAS. |

---

## 3. Implementation Order for Claude Code (The Build Agent)

Execute the tasks sequentially following the vertical slices defined in `tasks.md`:

1. **Slice 1 (Security & Core Primitives):**
   - Run `T1` (Split dependencies: `backend/requirements.txt` vs `requirements-dev.txt`).
   - Run `T2` (Update `antigravity.yaml` and `.gitignore`).
   - Run `T3` (Enforce production `SECRET_KEY` startup check in `backend/api/main.py`).
   - Run `T4` (Database TLS and URL resolution in `backend/adapters/database/connection.py`).
   - Run `T5` (Alembic `migrations/env.py` URL & TLS update).
   - Run `T6` (Multi-database `/api/v1/health` connectivity probe).
2. **Slice 2 (Containerization & Ingress):**
   - Run `T7` (`backend/Dockerfile` and `docker-entrypoint.sh`).
   - Run `T8` (`frontend-web/next.config.ts` standalone + relative URLs).
   - Run `T9` (`frontend-web/Dockerfile`).
   - Run `T10` (`docker/caddy/Caddyfile`).
3. **Slice 3 (Compose & Automation):**
   - Run `T11` (`docker/mariadb/01-init-dbs.sh` variable fix).
   - Run `T12` (`docker-compose.yml` multi-profile refactor).
   - Run `T13` (`docker-compose.dev.yml` override).
   - Run `T14` (`.env.example` update).
   - Run `T15` (Mobile server URL setting & health probe).
   - Run `T16` (`scripts/devops/deploy.sh` enhancement & runbooks).
4. **Slice 4 (CI/CD Pipelines):**
   - Run `T17` (`.github/workflows/ci.yml`, Dependabot, MariaDB smoke test).
   - Run `T18` (`.github/workflows/cd.yml`, GHCR multi-arch, staging SSH deploy, release bundle).

---

## 4. Verification Checkpoints

After implementing each slice, Claude Code must run the corresponding verification command specified in `tasks.md`:
- `backend`: `pytest --cov=backend tests/`
- `web`: `cd frontend-web && npm run build && npm test`
- `docker`: `docker compose config`
- `scripts`: `bash -n scripts/devops/deploy.sh`
- `ci`: validate `.github/workflows/ci.yml` syntax
