# Project Agent Rules (`AGENTS.md`)

> This file defines project-specific commands, structure, conventions, and boundaries.  
> It supplements `~/.config/ai-workflow/GLOBAL_RULES.md` and must never weaken the `Status: Approved` spec gate.

## Commands

Monorepo: run each block from the directory shown.

### Backend (`cd backend`, venv at `backend/.venv`)

`pytest.ini` lives in `backend/` (`pythonpath = . ..`, `testpaths = tests`), so pytest runs from `backend/`.

- **Install / Setup:** `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt`
- **Test (All):** `pytest`
- **Test (Coverage):** `pytest --cov=backend --cov-report=term-missing tests/`
- **Test (Single / Focused):** `pytest tests/<path>::<test_name>` or `pytest tests/<path> -k <expr>`
- **Lint / Format Check:** `ruff check . && ruff format --check .`
- **Dependency audit:** `pip-audit -r requirements.txt`

### Database migrations (repo root; three logical DBs)

- `alembic -c backend/migrations/alembic.ini upgrade head` (`db_articles`)
- `alembic -c backend/migrations/alembic_users.ini upgrade head` (`db_users`)
- `alembic -c backend/migrations/alembic_analytics.ini upgrade head` (`db_analytics`)

### Frontend Web (`cd frontend-web`)

- **Install / Setup:** `npm ci`
- **Test (All):** `npm test` (`vitest run`)
- **Test (Single / Focused):** `npx vitest run <path>`
- **Typecheck:** `npx tsc --noEmit`
- **Lint:** `npm run lint`
- **Build:** `npm run build`
- **Dependency audit:** `npm audit --audit-level=high`

### Frontend Mobile (`cd frontend-mobile`)

No test or lint scripts exist; verification is typecheck + Expo health.

- **Install / Setup:** `npm ci`
- **Typecheck:** `npx tsc --noEmit`
- **Health:** `npx expo-doctor`

### Infrastructure (repo root)

- **Compose validation:** `docker compose config -q` (and per profile: `docker compose --profile with-db config -q`, `--profile demo`, `--profile tunnel`, plus `-f docker-compose.yml -f docker-compose.public.yml config -q`)
- **On-premise package verification:** `./scripts/devops/verify-local-package.sh`
- **Dockerfile lint:** `hadolint backend/Dockerfile frontend-web/Dockerfile`
- **Shell syntax:** `bash -n scripts/devops/deploy.sh scripts/devops/verify-local-package.sh docker/mariadb/01-init-dbs.sh`
- **Secret scan:** `gitleaks detect --source . -v`

## Structure

Document key directories and architectural boundaries:

- `backend/app/`: Domain core (entities, services, ports). Framework-, DB- and container-free.
- `backend/adapters/`: Port implementations (database, external services).
- `backend/api/`: FastAPI routers and app wiring (`backend/api/main.py`).
- `backend/migrations/`: Alembic, one config + versions dir per DB (`versions/`, `versions_users/`, `versions_analytics/`).
- `backend/tests/`: `unit/`, `domain/`, `adapters/`, `api/`, `db/`, `reports/`.
- `frontend-web/`: Next.js app (`app/`, `components/`, `lib/adapters/`).
- `frontend-mobile/`: Expo / React Native app.
- `shared/`: Code shared by web and mobile.
- `docker/`, `scripts/devops/`, `.github/`: Infrastructure and CI/CD.
- `specs/`: Change specifications (`specs/<change>/{spec.md,tasks.md,handoff.md}`)
- `docs/adr/`: Architectural Decision Records (`NNNN-<slug>.md`)
- `GLOSSARY.md`: Ubiquitous domain language definitions

## Style & Conventions

- Follow SOLID, separation of concerns, and explicit module interfaces.
- Validate all external inputs at system boundaries; use typed/structured errors.
- Keep functions small, cohesive, and free of hidden global state.
- Hexagonal architecture: infrastructure details never leak into `backend/app/`.
- Backend: Python 3.12, FastAPI, async SQLAlchemy 2.0 + aiomysql, Pydantic v2. Three separate engines/pools (`db_articles`, `db_users`, `db_analytics`).
- Frontend: strict TypeScript; web uses relative API URLs (empty `NEXT_PUBLIC_API_URL`) behind the single-origin proxy.
- DB collation: `utf8mb4_unicode_ci`.

## Testing

- **Default:** Test-Driven Development (Red -> Green -> Refactor) using the commands in `## Commands`.
- Assert observable behaviour through public interfaces, covering happy paths, edge cases, and failure modes.
- External services must be isolated or tested with deterministic fixtures/fakes; never hit live production endpoints in tests.

## Boundaries

- **Always:**
  - Require `specs/<change>/spec.md` with `Status: Approved` before writing implementation code.
  - Run focused tests and lint/typecheck from `## Commands` before committing each work unit.
  - Use Conventional Commits (`<= 400` changed lines per slice) without AI attribution.
- **Ask First:**
  - Adding new third-party dependencies or upgrading major framework versions.
  - Changing database schemas, public API contracts, or authentication/authorization flows.
  - Modifying CI/CD pipelines, deployment configs, or environment variable contracts.
- **Never:**
  - Commit secrets, `.env` files, credentials, or private keys.
  - Bypass or weaken tests, linters, or the `Status: Approved` spec gate.
  - Mutate or delete existing user/production data without explicit approval and a rollback plan.

## Definition of Done

- [ ] Every requirement (`S#`) in `specs/<change>/spec.md` is satisfied and verified by tests.
- [ ] All `Test`, `Typecheck`, `Lint`, and `Build` commands in `## Commands` pass with zero errors.
- [ ] Edge cases, error paths, and regressions on shared code paths are covered.
- [ ] `specs/<change>/tasks.md` and `specs/<change>/handoff.md` are updated with final status and commits.
- [ ] Architectural decisions are recorded in `docs/adr/` and saved to Engram.