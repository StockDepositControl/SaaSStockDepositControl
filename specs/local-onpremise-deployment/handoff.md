# Handoff Log: Local On-Premise Deployment Package & Verification

- **Spec:** `specs/local-onpremise-deployment/spec.md`
- **Tasks:** `specs/local-onpremise-deployment/tasks.md`
- **Current Phase:** `Ready for Build (Approved)`
- **Engram Topic Key:** `spec/local-onpremise-deployment/decisions`

---

## 1. Handoff Status

- **Spec Status:** `Approved` (Approved by fede on 2026-10-25)
- **Last Updated By:** `Antigravity`
- **Completed Tasks:** None
- **Pending Tasks:** `T1`, `T2`, `T3`, `T4`

---

## 2. Strategic Context & Architecture Notes

1. **Strategic Shift:** The user prioritized local on-premise deployment over cloud deployment CD secrets. The platform is designed for conducting product audits across pharmacy branches. Pharmacy clients already maintain their product, pricing, and stock databases (`db_articles`) on local servers.
2. **Database Separation:**
   - `db_articles`: Client pharmacy database (MariaDB 10.x), accessed in read-only mode (`SELECT`). Must not have Alembic migrations run against it.
   - `db_users` & `db_analytics`: Hosted locally on the pharmacy host via the bundled MariaDB container (`with-db` profile), incurring zero cloud fees.
3. **Ingress & Camera Compatibility:**
   - Caddy proxy runs on `:8080`.
   - Host port conflicts on `80`/`443` must be avoided via configurable port mapping.
   - Native Expo mobile app operates camera natively over plain HTTP LAN without browser WebRTC secure-context restrictions.
   - Cloudflare Tunnel (`--profile tunnel`) provides remote/multi-branch connectivity when needed.

---

## 3. Durable Decisions & Rationale

| Date | Actor | Decision | Rationale / Tradeoff | Engram / ADR Ref |
|---|---|---|---|---|
| 2026-10-25 | fede | Prioritize local on-premise deployment over cloud CD secrets | Pharmacy branches maintain local databases; cloud hosting will be tackled only if explicitly requested by clients. | Engram #14 (`architecture/deployment-strategy`) |
| 2026-10-25 | fede | Pharmacy database is MariaDB 10.x (Q1 resolved) | Standard MariaDB user grants and `utf8mb4_unicode_ci` collation. | `specs/local-onpremise-deployment/spec.md` §9 |
| 2026-10-25 | fede / Antigravity | Hybrid Ingress: Local Wi-Fi LAN + Tunnel Fallback (Q2 resolved) | Direct Wi-Fi LAN has lowest latency and zero internet dependency; Cloudflare Tunnel enables remote/multi-branch access without opening router ports. | `specs/local-onpremise-deployment/spec.md` §9 |
| 2026-10-25 | Antigravity | Introduce granular migration flags (`RUN_MIGRATIONS_ARTICLES`) | Prevents Alembic from crashing when connecting to external read-only pharmacy databases. | `specs/local-onpremise-deployment/spec.md` §6 |
| 2026-10-25 | Antigravity | Parameterize Compose ingress host ports | Prevents `bind: address already in use` crashes on client servers with existing web services on 80/443. | `specs/local-onpremise-deployment/spec.md` §6 |

---

## 4. Open Questions & Blockers

- None. All open questions resolved and specification approved by human engineer.

---

## 5. Next Action

- **Claude Code (Build Agent)**: Execute vertical slice `T1` (`RUN_MIGRATIONS_ARTICLES` in `backend/docker-entrypoint.sh` and `.env.example`).

