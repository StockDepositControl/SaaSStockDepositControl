# Handoff Log: CI Pipeline Stability & Security Fixes

- **Spec:** `specs/ci-fixes/spec.md`
- **Tasks:** `specs/ci-fixes/tasks.md`
- **Current Phase:** `Build complete (T1-T4)`
- **Engram Topic Key:** `spec/ci-fixes/decisions`

---

## 1. Handoff Status

- **Spec Status:** `Approved` (Approved by fede on 2026-10-25)
- **Last Updated By:** `Claude Code`
- **Completed Tasks:** `T1` (`05f90b6`), `T2` (`c10b8ae`), `T3` (`ec99bd0`), `T4` (`40d27b6`)
- **Pending Tasks:** `None`

---

## 2. Durable Decisions & Rationale

| Date | Actor | Decision | Rationale / Tradeoff | Engram / ADR Ref |
|---|---|---|---|---|
| `2026-10-25` | Antigravity | Default `CORS_ORIGINS` to `""` instead of `"*"` in `backend/api/main.py` | With `allow_credentials=True`, `*` exposes authenticated endpoints to all origins. Unset environments like CI default to `""`, relying on `local_network_regex` for LAN/local testing and properly blocking malicious origins in `test_cors.py`. | `spec/ci-fixes/decisions` |
| `2026-10-25` | Antigravity | Use `.gitleaksignore` + `.gitleaks.toml` allowlist instead of git history rewrite | All 4 detections in git history are unit test fixtures or doc examples. Rewriting git history via `git-filter-repo` on a shared repository forces hard resets for all collaborators. Fingerprinting in `.gitleaksignore` cleanly unblocks CI while preserving active scanning. | `spec/ci-fixes/decisions` |
| `2026-10-25` | Antigravity | Exclude `migrations` from Ruff checks via `pyproject.toml` | Alembic migrations use defensive `try ... except Exception: pass` when dropping indexes/constraints across dialects. Historical migrations should not be altered for linters (`BLE001`, `S110`). | `spec/ci-fixes/decisions` |

---

## 3. Open Questions & Blockers

- None. Awaiting push and a CI run to confirm `S1`-`S6` on GitHub Actions.

---

## 4. Build Notes (Claude Code)

- Verified locally: `test_cors.py` 21 passed; full pytest 372 passed; `ruff check .` and `ruff format --check .` exit 0; gitleaks reports `no leaks found` (120 commits); `ci.yml` parses.
- **Deviation from the T3 literal steps:** the spec's Ruff config left 136 violations after `ruff check --fix` + `ruff format`. Per human decision, all were fixed in code instead of loosening the config: long docstrings/comments wrapped, long string literals split (content unchanged), 15 `F821` forward refs fixed with a `TYPE_CHECKING` block in `api/dependencies/services.py`, `UserORM.is_active == True` changed to `.is_(True)`, an `APIRouter` import hoisted in `api/main.py`, 2 unused variables and one ambiguous name removed in `api/v1/stock.py` and `scripts/seed.py`, and `# noqa: E402` on three `scripts/seed.py` imports that must follow its `sys.path` bootstrap.
- Only the backend Ruff steps lost `continue-on-error`; the web lint/typecheck and Expo doctor steps keep it (out of scope).
- Reminder: `summary_project.md:635` held a 40-char `SECRET_KEY` (commit `4dae916`). Ignoring it hides the finding; rotate it if it was ever deployed.

---

## 5. Next Action

- Push `feat/pdc-slice-4` and confirm CI is green.
