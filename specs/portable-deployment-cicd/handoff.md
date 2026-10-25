# Handoff: Portable Deployment + CI/CD with GitHub Actions

- **From:** Antigravity (Specification & Architecture Agent)
- **To:** Claude Code (Build Agent)
- **Spec:** [`specs/portable-deployment-cicd/spec.md`](file:///home/fede/Proyectos/SaaSStockDepositControl/specs/portable-deployment-cicd/spec.md)
- **Tasks:** [`specs/portable-deployment-cicd/tasks.md`](file:///home/fede/Proyectos/SaaSStockDepositControl/specs/portable-deployment-cicd/tasks.md)
- **Status:** Approved for Implementation (Revised with Spec-Challenge Decisions)

---

## 1. Context & Architectural Overview

The goal of this initiative is to eliminate the current development-only hosting model and deliver a portable, single-compose containerized distribution paired with enterprise-grade CI/CD automation.

### Key Architectural Invariants to Maintain:
1. **Hexagonal Architecture Preservation:** All Docker, Caddy, Alembic, and Compose changes are infrastructure concerns (`docker/`, `scripts/`, `backend/adapters/`, `.github/`). Under no circumstances should framework or container details leak into `backend/app/` (domain services, entities, ports).
2. **Multi-Database Topology:** The system manages 3 distinct logical databases (`db_articles`, `db_users`, `db_analytics`). The connection provider, health probe, Alembic environment, and CI smoke test must maintain separate engine pools and migrations across all three.
3. **Single Origin & Relative URLs:** Caddy serves as the unified ingress gateway. The frontend web application must keep `NEXT_PUBLIC_API_URL` empty, routing `/api/*` through Caddy to the backend, ensuring browser camera permissions (`getUserMedia`) function without cross-origin or insecure context blocks.
4. **Least-Privilege & Zero-Secrets:** Non-root users in containers (`appuser` 10001, `nextjs` 1001), localhost-only database ports, and strict prohibition of secrets in repos, images, or CI workflow files.

---

## 2. Durable Decisions & Spec-Challenge Resolutions

| Decision | Rationale | Spec / ADR Ref |
|:---|:---|:---|
| **Pytest Execution from `backend/`** | `backend/pytest.ini` defines `pythonpath = . ..` and `testpaths = tests`. All backend pytest and lint commands must run from `cd backend`. | `AGENTS.md` (`## Commands`) |
| **Deterministic DATABASE_URL Precedence** | Enforce a single uniform precedence: Specific URL (`*_DATABASE_URL`) -> Base `DATABASE_URL` fallback -> `DB_*` individual components across both `connection.py` and Alembic `env.py`. | `spec.md` §5.4 |
| **Alembic Percent-Escaping (`%%`)** | Alembic uses `configparser`; unescaped `%` in passwords triggers `InterpolationSyntaxError`. Passwords/URLs must be escaped with `.replace("%", "%%")` before calling `set_main_option()`. | `spec.md` §5.4 |
| **Single `SECRET_KEY` Check Authority** | The Python FastAPI lifespan (`backend/api/main.py`) in Task T3 is the sole authority for validating `SECRET_KEY` when `ENVIRONMENT=production`. Removed duplicate shell checks from entrypoint scripts. | `spec.md` §5.1, §5.4 |
| **Default `ENVIRONMENT=production` in Compose** | `docker-compose.yml` defaults `ENVIRONMENT: ${ENVIRONMENT:-production}` so all container targets run with production security invariants by default; overridden in `docker-compose.dev.yml`. | `spec.md` §5.3 |
| **Caddy Ingress & Clean Health/ACME** | Caddy replaces Nginx. Health handler uses canonical syntax `respond /caddy-health "healthy" 200`. Avoid dummy default email `admin@example.com` to prevent ACME registration failures. | `spec.md` §5.2 |
| **Compose Service Profiles** | Allows running identical images and compose file across Client (external DB), Staging (bundled DB), Demos (seed), and Tunnel targets using `--profile`. | `spec.md` §5.3 |
| **Dedicated Mobile Slice (T15)** | Separated mobile runtime config (AsyncStorage dynamic server URL and connection test) into its own vertical slice distinct from compose and bash automation. | `tasks.md` Phase 4 |
| **Repo Governance Status** | The `.gitignore` half of T2 (untracking `/specs`) is already completed in commit `c4d5bc3`; T2 only needs to update `antigravity.yaml`. | `tasks.md` T2 |

---

## 3. Implementation Order for Claude Code (The Build Agent)

Execute the tasks sequentially following the vertical slices defined in `tasks.md`:

1. **Slice 1 (Security & Core Primitives):**
   - Run `T1` (Split dependencies: `backend/requirements.txt` vs `requirements-dev.txt`). **Done** — commit `0739f85`.
   - Run `T2` (Update `antigravity.yaml` `allowed_directories`). **Done** — commit `8ba48f2`.
   - Run `T3` (Enforce production `SECRET_KEY` startup check in `backend/api/main.py`). **Done** — commit `3580e00`.
   - Run `T4` (Database TLS and URL precedence in `backend/adapters/database/connection.py`). **Done** — commit `ff5eaf4`.
   - Run `T5` (Alembic `migrations/env.py` URL precedence, `%` escape, and TLS). **Done** — commit `5de4820`.
   - Run `T6` (Multi-database `/api/v1/health` connectivity probe). **Done** — see §8.
2. **Slice 2 (Containerization & Ingress):**
   - Run `T7` (`backend/Dockerfile` and `docker-entrypoint.sh` without duplicate secret check).
   - Run `T8` (`frontend-web/next.config.ts` standalone + relative URLs).
   - Run `T9` (`frontend-web/Dockerfile`).
   - Run `T10` (`docker/caddy/Caddyfile` with clean syntax & no fake email).
3. **Slice 3 (Compose & DevOps Scripts):**
   - Run `T11` (`docker/mariadb/01-init-dbs.sh` variable fix).
   - Run `T12` (`docker-compose.yml` multi-profile with `ENVIRONMENT: production` default).
   - Run `T13` (`docker-compose.dev.yml` override).
   - Run `T14` (`.env.example` update).
   - Run `T16` (`scripts/devops/deploy.sh` enhancement & runbooks).
4. **Slice 4 (Mobile Runtime Portability — Dedicated Slice):**
   - Run `T15` (Mobile AsyncStorage dynamic server URL and connection test).
5. **Slice 5 (CI Pipeline & Smoke Test):**
   - Run `T17` (`.github/workflows/ci.yml`, Dependabot, MariaDB 10.11 smoke test).
6. **Slice 6 (CD Pipeline & Release Engineering):**
   - Run `T18` (`.github/workflows/cd.yml`, GHCR multi-arch, staging SSH deploy, release bundle).

---

## 4. Verification Checkpoints (per AGENTS.md)

After implementing each slice, Claude Code must run the corresponding verification command specified in `tasks.md`:
- `backend`: `cd backend && pytest` (and `pytest --cov=backend tests/`)
- `web`: `cd frontend-web && npm run build && npm test && npx tsc --noEmit`
- `mobile`: `cd frontend-mobile && npx tsc --noEmit && npx expo-doctor`
- `docker / compose`: `docker compose config -q` (across profiles: `--profile with-db`, `--profile demo`, `--profile tunnel`)
- `scripts`: `bash -n scripts/devops/deploy.sh docker/mariadb/01-init-dbs.sh`
- `ci / cd`: validate YAML syntax via `python3 -c "import yaml; ..."`

---

## 5. T3 Spec-Challenge Notes & Outcome

- Blocklist follows `spec.md` §5.4 (`changeme`, `changeme_secret_key`, `secret`, empty, `< 32` chars); `tasks.md` T3 omitted `secret`.
- `tasks.md` T3 second verify command needs the repo root on `PYTHONPATH` when run from `backend/`: `PYTHONPATH=.. python -c ...`.
- Check lives in `validate_production_secret_key()` called from the lifespan; tests enter it via `TestClient(app)` context. Full backend suite: 292 passed.
- Pre-existing ruff `I001` warnings in `backend/api/main.py` (sys.path hack) left untouched.

## 6. T4 Notes & Outcome

- New public helpers in `connection.py`: `resolve_database_url(target)`, `build_ssl_connect_args()`, `DatabaseConfigError(ValueError)`. All three factories and `SQLAlchemyConnectionProvider` use them. T5 should mirror `resolve_database_url` semantics in `migrations/env.py`.
- Behaviour change: `get_users_session_factory` / `get_analytics_session_factory` now fall back to `DATABASE_URL` with the database name swapped (name from `DB_NAME_USERS` / `DB_NAME_ANALYTICS`); previously they only read their specific URL.
- TLS: `require` encrypts without cert verification; `verify-ca` validates the chain against `DB_SSL_CA` (system trust store if unset). Hostname is never checked in either mode (CA-only verification, per mode name). Invalid `DB_SSL_MODE` or unreadable `DB_SSL_CA` raises `DatabaseConfigError`.
- Full backend suite: 318 passed (292 baseline + 26 new). Pre-existing ruff warnings in `connection.py` left untouched.

## 7. T5 Notes & Outcome

- `env.py` executes migrations at import and needs an Alembic context, so it cannot be imported in tests. The pure helpers live in the new `backend/migrations/url_config.py` (`resolve_alembic_url`, `escape_for_configparser`, `alembic_engine_kwargs`); `env.py` only wires them. `resolve_alembic_url` delegates to T4's `resolve_database_url`, so app and Alembic share one precedence implementation.
- `alembic_engine_kwargs` returns `{}` for SQLite (no SSL args), otherwise `{"connect_args": build_ssl_connect_args()}` when `DB_SSL_MODE != disable`.
- Deviations from `tasks.md` T5 (approved plan): extra files `url_config.py` and `tests/db/test_alembic_env_url.py`. Verify command #2 (`from backend.migrations.env import db_target`) cannot work by design; use `cd backend && PYTHONPATH=.. python -c "from backend.migrations.url_config import resolve_alembic_url"` instead. Verify command #1 needs an absolute SQLite path (`sqlite+aiosqlite:////tmp/x.db`); the relative `///tmp/test.db` form fails with "unable to open database file".
- Because `load_dotenv()` runs in `env.py`, a developer `.env` with `<TARGET>_DATABASE_URL` takes precedence over an inline `DATABASE_URL`; clear the specific var (e.g. `ARTICLES_DATABASE_URL=`) to force the fallback in a manual check.
- Full backend suite: 330 passed (318 baseline + 12 new). Pre-existing ruff `I001` in `env.py` left untouched.

## 8. T6 Notes & Outcome

- Port: `ConnectionProvider.check_connectivity()` stays abstract (bool). New non-abstract `check_databases() -> dict[str, bool]` defaults to the single `check_connectivity()` result for articles/users/analytics, so legacy providers and test mocks keep working. `SQLAlchemyConnectionProvider` overrides it with a real `SELECT 1` per database (own pool for articles; `get_users_session_factory` / `get_analytics_session_factory` for the others), and `check_connectivity()` now returns `all(...)` of it.
- `/health` body: legacy `"database"` is kept as the aggregate (`connected`/`disconnected`); added `"databases"` (per-DB) and `"version"` (read from `request.app.version`, no duplicated constant). Any DB down or probe exception -> 503 with `status: unhealthy`.
- Deviations from `tasks.md` T6: `backend/tests/api/test_health.py` did not exist (created); `tests/api/test_api_bootstrap.py` had an exact-equality assertion on the old body and was relaxed to key checks.
- Full backend suite: 341 passed (330 baseline + 11 new). Pre-existing ruff warnings in touched files left untouched.

## 9. T1 Notes & Slice 1 Closure

- T1 (`0739f85`): `pytest`, `pytest-asyncio`, `httpx` and `aiosqlite` moved to `requirements-dev.txt`, which also gains `pytest-cov`, `ruff` and `pip-audit`. `cryptography` added to runtime for MySQL TLS. Deviation from `tasks.md` T1: `faker` stays in runtime because `seed.py` imports it.
- Slice 1 commits: T1 `0739f85`, T2 `8ba48f2`, T3 `3580e00`, T4 `ff5eaf4`, T5 `5de4820`, T6 `c825678`.
- Closing verification (from `backend/`): `pytest` 341 passed; `pip-audit -r requirements.txt` clean; T1 verify commands pass.
- Known baseline: `ruff check .` / `ruff format --check .` report pre-existing violations repo-wide (806 errors, 124 files unformatted, mostly in untouched code). The lint gate in CI (T17) needs a baseline/ruff-config decision before it can be enforced.

## 10. Slice 1 Code-Review Follow-ups

Raised by `/code-review medium` and `/simplify` after Slice 1; the first item is fixed, the rest are open decisions.

- **Fixed (`19b898c`):** the production `SECRET_KEY` check now normalises `ENVIRONMENT` (strip + lowercase); `Production` previously skipped it.
- **`/health` error detail:** the exception path returns `str(e)` to unauthenticated callers (`backend/api/v1/health.py`). S14 does not require it; changing it is a public-contract change (AGENTS.md "Ask First").
- **`DATABASE_URL` fan-out (T4):** `resolve_database_url` now applies `DATABASE_URL` to users and analytics with the database name swapped. Deployments mixing `DATABASE_URL` (articles) with `DB_*` for the others change target. Legacy `DB_NAME` is no longer honoured for articles in Alembic.
- **`check_connectivity` meaning (T6):** now true only when all three databases respond; a caller that only needs articles will fail when users or analytics is down.
- **Probe vs injected provider:** a `SQLAlchemyConnectionProvider` built with an explicit URL probes its own articles engine but users/analytics via module-global, env-derived factories.
- **TLS:** `verify-ca` does not check the hostname; a `verify-full` mode would close that gap.
- **Docs:** `AGENTS.md` Install / Setup should also install `requirements-dev.txt` for the test environment.
- **Outside the diff:** `backend/scripts/seed.py` builds its URLs from `DB_*` and ignores `DATABASE_URL` / `*_DATABASE_URL`; `api/dependencies/__init__.py:30` reads `SECRET_KEY` with its own dev default.
