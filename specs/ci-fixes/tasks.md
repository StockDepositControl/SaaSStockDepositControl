# Implementation Tasks: CI Pipeline Stability & Security Fixes

- **Spec Reference:** `specs/ci-fixes/spec.md` (`Status` must be `Approved` before execution)
- **Delivery Strategy:** Vertical slices (`<= 400` changed lines per commit), TDD (`Red -> Green -> Refactor`), dependency-ordered.

---

## Task Breakdown

### `T1`: CORS Default Hardening in `backend/api/main.py`
- **Covers Spec IDs:** `S2`, `S3`, `S6`
- **Dependencies:** None
- **Route:** `inline`
- **Risk Tier:** `low`
- **Target Modules / Files:** `backend/api/main.py`
- **Acceptance Criteria:**
  - [ ] Set `origins_str = os.getenv("CORS_ORIGINS", "")` in `backend/api/main.py` so that unpopulated environments don't default to `["*"]`.
  - [ ] Verify that all 21 tests in `tests/api/test_cors.py` pass cleanly when `CORS_ORIGINS=""` is passed.
- **Verification Command:** `cd backend && CORS_ORIGINS="" .venv/bin/pytest tests/api/test_cors.py`
- **Status:** `[ ] pending`

---

### `T2`: Gitleaks Ignore & Allowlist Configuration
- **Covers Spec IDs:** `S1`
- **Dependencies:** None
- **Route:** `inline`
- **Risk Tier:** `low`
- **Target Modules / Files:** `.gitleaksignore`, `.gitleaks.toml`
- **Acceptance Criteria:**
  - [ ] Create `.gitleaksignore` in the repo root containing the 8 verified historical false-positive fingerprints from commits `7a477402`, `51e92717`, `4611af2d`, `e829fdc1`, `4dae9161`.
  - [ ] Create `.gitleaks.toml` with `[allowlist]` paths for `backend/tests/.*` and `docs/.*`.
  - [ ] Verify that running `gitleaks detect --source . -v` passes with 0 leaks found and exit code 0.
- **Verification Command:** `/home/fede/.gemini/antigravity/brain/0a32da85-d04c-42ba-b74e-107263f98a08/scratch/gitleaks detect --source . -v`
- **Status:** `[ ] pending`

---

### `T3`: Ruff Configuration & Formatting Baseline in Backend
- **Covers Spec IDs:** `S4`, `S5`
- **Dependencies:** `T1`
- **Route:** `inline`
- **Risk Tier:** `medium` (touches formatting across backend files)
- **Target Modules / Files:** `backend/pyproject.toml`, backend python files
- **Acceptance Criteria:**
  - [ ] Create `backend/pyproject.toml` configuring Ruff with `extend-exclude = ["migrations", ".venv"]`, `select = ["E", "F", "W", "I"]`, and `line-length = 88`.
  - [ ] Run `cd backend && .venv/bin/ruff check --fix .` to auto-fix imports and basic lints.
  - [ ] Run `cd backend && .venv/bin/ruff format .` to format files consistently.
  - [ ] Verify `ruff check .` and `ruff format --check .` both pass with 0 errors.
- **Verification Command:** `cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest`
- **Status:** `[ ] pending`

---

### `T4`: CI Workflow Quality Gate Cleanup
- **Covers Spec IDs:** `S5`, `S6`
- **Dependencies:** `T1`, `T2`, `T3`
- **Route:** `inline`
- **Risk Tier:** `low`
- **Target Modules / Files:** `.github/workflows/ci.yml`
- **Acceptance Criteria:**
  - [ ] Remove `continue-on-error: true` from the `Ruff lint` and `Ruff format` steps in `.github/workflows/ci.yml` now that the baseline is resolved.
  - [ ] Verify workflow YAML syntax with `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`.
- **Verification Command:** `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
- **Status:** `[ ] pending`
