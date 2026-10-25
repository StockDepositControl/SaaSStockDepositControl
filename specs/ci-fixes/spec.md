# Specification: CI Pipeline Stability & Security Fixes

- **Change ID:** `ci-fixes`
- **Status:** `Approved`
- **Approved By:** `fede`
- **Approval Date:** `2026-10-25`
- **Author Agent:** Antigravity (Gemini)

---

## 1. Objective

Resolve the two failing GitHub Actions CI jobs (`Security (gitleaks, audits, trivy)` and `Backend (ruff + pytest)`) on branch `feat/pdc-slice-4`. Specifically:
1. Fix the CORS logic defect where unconfigured environments default to allowing any origin with credentials, causing 6 test failures in `backend/tests/api/test_cors.py`.
2. Suppress historical false-positive secret detections (test fixtures and documentation sample tokens) in Gitleaks history scanning so security checks pass deterministically.
3. Establish a standard Ruff configuration (`backend/pyproject.toml`) that excludes historical database migrations from strict application lints, auto-fixes formatting, and provides a clean linting baseline.

---

## 2. Assumptions

- `A1:` The 4 secret detections in git history (`backend/tests/api/test_auth_routes.py`, `docs/API_DOCUMENTATION.md`, and past revisions of `summary_project.md`) are mock/test tokens and documentation examples, not active production credentials.
- `A2:` `CORS_ORIGINS` is intentionally configured in production via `.env` or deployment variables. When omitted (e.g. CI or fresh containers), the backend should securely default to allowing only internal/RFC-1918 private network origins via `local_network_regex`, rather than opening the API to all origins with credentials.
- `A3:` Alembic migrations (`backend/migrations/`) are immutable schema transition records; they intentionally use defensive constructs (e.g. `try ... except Exception: pass` when dropping indexes) and must not be retroactively altered to satisfy application-level linter rules (`BLE001`, `S110`).

---

## 3. Tech Stack & Commands

Derived from `AGENTS.md` (`## Commands`):

- **Backend Runtime:** Python 3.12, FastAPI, Pytest, Ruff.
- **Backend Test Command:** `cd backend && pytest` (and `pytest tests/api/test_cors.py`)
- **Backend Lint Command:** `cd backend && ruff check . && ruff format --check .`
- **Security Check Command:** `gitleaks detect --source . -v`

---

## 4. Project Structure & Module Boundaries

- `backend/api/main.py`: Owns FastAPI application configuration and middleware attachment. `origins_str` default must be safe.
- `backend/pyproject.toml`: Project-level tool configuration for Ruff. Defines linter rules (`select`), line length, exclusions, and per-file ignores.
- `.gitleaksignore`: Git-tracked ignore file storing SHA:path:rule:line fingerprints of verified historical false positives.
- `.gitleaks.toml`: Gitleaks configuration defining path-based allowlists for tests and docs.

---

## 5. Code Style & Contract Changes

### CORS Fallback Invariant (`backend/api/main.py`)
```python
# Before (permits all origins in CI / unset environments):
origins_str = os.getenv("CORS_ORIGINS", "*")

# After (safe default: empty list; local_network_regex still permits private LAN/localhost):
origins_str = os.getenv("CORS_ORIGINS", "")
```

### Ruff Configuration Invariant (`backend/pyproject.toml`)
```toml
[tool.ruff]
target-version = "py312"
line-length = 88
extend-exclude = [
    "migrations",
    ".venv",
]

[tool.ruff.lint]
select = ["E", "F", "W", "I"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]
```

---

## 6. Acceptance Criteria (Behavioural & Testable)

- **`S1` (Gitleaks Full History Clean Scan):**
  - **Given:** Full git history scanned with `gitleaks detect --source . -v`.
  - **When:** Gitleaks evaluates commits containing test fixtures (`test-secret-key-...`) and documentation JWT examples (`eyJhbGci...`).
  - **Then:** All 8 known historical fingerprints are matched in `.gitleaksignore` or covered by path allowlists in `.gitleaks.toml`; Gitleaks exits with code 0 and reports `leaks found: 0`.

- **`S2` (CORS Preflight Rejection for Disallowed Origins):**
  - **Given:** `CORS_ORIGINS` is unset in the execution environment.
  - **When:** An `OPTIONS` preflight request is made to `/api/v1/health` with `Origin: http://malicious.example.com` or `https://evil-site.org`.
  - **Then:** The response must NOT include the `access-control-allow-origin` header.

- **`S3` (CORS Preflight Approval for Local Development):**
  - **Given:** `CORS_ORIGINS` is unset.
  - **When:** An `OPTIONS` preflight request is made to `/api/v1/health` with `Origin: http://localhost:3000` or `http://192.168.1.5:8080`.
  - **Then:** The response includes `access-control-allow-origin` matching the requested origin, and `access-control-allow-methods` contains `GET`.

- **`S4` (Ruff Exclusion of Migration Files):**
  - **Given:** `backend/migrations/` contains defensive `try ... except Exception: pass` blocks in migration scripts.
  - **When:** `ruff check .` is executed from `backend/`.
  - **Then:** No errors from `migrations/` (`BLE001`, `S110`) are reported.

- **`S5` (Clean Ruff Lint and Format Verification):**
  - **Given:** `backend/pyproject.toml` is present and auto-fixes/formatting have been applied to `backend/`.
  - **When:** Running `ruff check .` and `ruff format --check .` from `backend/`.
  - **Then:** Both commands exit with status 0 without error.

- **`S6` (Pytest Suite Full Pass in CI Context):**
  - **Given:** A clean environment without `.env` or `CORS_ORIGINS`.
  - **When:** Running `pytest --cov=backend tests/` from `backend/`.
  - **Then:** All 372+ backend tests pass with 0 failures (including all 21 tests in `tests/api/test_cors.py`).

---

## 7. Risks, Edge Cases & Failure Modes

- **Local Development Compatibility:** Changing the default `CORS_ORIGINS` to `""` does NOT affect web developers running Next.js locally, because `local_network_regex` explicitly allows `http://localhost:*`, `http://127.0.0.1:*`, and RFC-1918 private subnets (`192.168.*`, `10.*`, `172.16-31.*`).
- **Production Deployments:** Production environments using explicit domains (e.g. `https://stock.example.com`) continue to supply them via `CORS_ORIGINS` in `.env`, exactly as documented in `.env.example`.
- **False-Sense of Security in Gitleaks:** Only verified false-positive fingerprints and test/doc directories must be ignored. Real application secrets must never be added to `.gitleaksignore`.

---

## 8. Testing Strategy

- `tests/api/test_cors.py`: Verifies `S2` and `S3` under both populated and unpopulated `CORS_ORIGINS`.
- Full pytest suite: Verifies no regressions across authentication, health, and domain services (`S6`).
- Gitleaks CLI execution: Verifies `S1`.
- Ruff check & format: Verifies `S4` and `S5`.

---

## 9. Boundaries & Out of Scope

- **In Scope:** `backend/api/main.py`, `backend/pyproject.toml`, `.gitleaksignore`, `.gitleaks.toml`, `.github/workflows/ci.yml` (ruff step status).
- **Out of Scope (Do Not Modify):**
  - Do not rewrite git history with `git filter-repo` or BFG.
  - Do not edit historical Alembic migration scripts to satisfy linters.
  - Do not modify domain logic or entity models in `backend/app/`.

---

## 10. Open Questions

- None. All causes and fixes have been empirically verified.
