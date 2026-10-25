# Handoff Log: CI Pipeline Stability & Security Fixes

- **Spec:** `specs/ci-fixes/spec.md`
- **Tasks:** `specs/ci-fixes/tasks.md`
- **Current Phase:** `Ready for Build (Approved)`
- **Engram Topic Key:** `spec/ci-fixes/decisions`

---

## 1. Handoff Status

- **Spec Status:** `Approved` (Approved by fede on 2026-10-25)
- **Last Updated By:** `Antigravity`
- **Completed Tasks:** `None`
- **Pending Tasks:** `T1`, `T2`, `T3`, `T4`

---

## 2. Durable Decisions & Rationale

| Date | Actor | Decision | Rationale / Tradeoff | Engram / ADR Ref |
|---|---|---|---|---|
| `2026-10-25` | Antigravity | Default `CORS_ORIGINS` to `""` instead of `"*"` in `backend/api/main.py` | With `allow_credentials=True`, `*` exposes authenticated endpoints to all origins. Unset environments like CI default to `""`, relying on `local_network_regex` for LAN/local testing and properly blocking malicious origins in `test_cors.py`. | `spec/ci-fixes/decisions` |
| `2026-10-25` | Antigravity | Use `.gitleaksignore` + `.gitleaks.toml` allowlist instead of git history rewrite | All 4 detections in git history are unit test fixtures or doc examples. Rewriting git history via `git-filter-repo` on a shared repository forces hard resets for all collaborators. Fingerprinting in `.gitleaksignore` cleanly unblocks CI while preserving active scanning. | `spec/ci-fixes/decisions` |
| `2026-10-25` | Antigravity | Exclude `migrations` from Ruff checks via `pyproject.toml` | Alembic migrations use defensive `try ... except Exception: pass` when dropping indexes/constraints across dialects. Historical migrations should not be altered for linters (`BLE001`, `S110`). | `spec/ci-fixes/decisions` |

---

## 3. Open Questions & Blockers

- Awaiting human review and sign-off on `specs/ci-fixes/spec.md` to transition from `Draft` to `Approved`.

---

## 4. Next Action

- Human review and approval in chat.
- Once approved, hand off execution to Claude Code (Build Agent) with the step-by-step prompt.
