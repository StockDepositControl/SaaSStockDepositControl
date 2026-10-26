# Handoff Log: Local On-Premise Deployment Package & Verification

- **Spec:** `specs/local-onpremise-deployment/spec.md`
- **Tasks:** `specs/local-onpremise-deployment/tasks.md`
- **Current Phase:** `Build (T1, T2 done)`
- **Engram Topic Key:** `spec/local-onpremise-deployment/decisions`

---

## 1. Handoff Status

- **Spec Status:** `Approved` (Approved by fede on 2026-10-25)
- **Last Updated By:** `Claude Code`
- **Completed Tasks:** `T1` (2026-10-26, commit `3874ece`; Gentle-AI RDD review approved, lineage `review-ffd0184cf226bb44`), `T2` (completed 2026-10-26, commits `655aff4` + follow-up `80d16cc`; Gentle-AI RDD reviews approved, lineages `review-b80fe3863c525c65` (T2), `review-9b4536d03cf6c9d1` (T1+T2), `review-de7172b99765d4a7` (guard), `review-f2c5aefcd7f2625b` (branch))
- **Pending Tasks:** `T3`, `T4`
- **Delivery:** PR #38 (`feat/onprem-02-migration-flags` → `main`, stacked-to-main position 1 of 3, 357 changed lines). Includes CD bundle + README fix `3b3f045` (adds `docker-compose.public.yml` to `DEPLOY_FILES`; not RDD-reviewed, declined).

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
| 2026-10-26 | fede / Claude Code | `.env.example` ships `RUN_MIGRATIONS_ARTICLES=true` (not `false` as in spec §5.1), with a comment telling on-prem installs to set it to `false` | Script default must be `true` for S2. The template's default `DB_HOST=mariadb` (with-db/demo) needs `db_articles` migrated; `false` would leave it with no schema. | Spec-Challenge Note 1 (T1); commit `3874ece` |
| 2026-10-26 | Claude Code | Per-database switches accept only the literal `true`; any other value skips that config and logs `Skipping migrations: <cfg>` | Matches the existing `RUN_MIGRATIONS` contract and fails safe for the external read-only `db_articles`. Advisory (RDD R4): a typo in `RUN_MIGRATIONS_USERS`/`_ANALYTICS` lets uvicorn start against an unmigrated schema; consider rejecting non-`true`/`false` values in a follow-up. | RDD lineage `review-ffd0184cf226bb44`; Engram `spec/local-onpremise-deployment/decisions` |
| 2026-10-26 | fede / Claude Code | 80/443 published only by opt-in `docker-compose.public.yml`, selected via `COMPOSE_FILE` in `.env`; base file publishes only `HTTP_PORT` | Replaces spec §5.1 `BIND_HOST_PORTS` (Compose cannot drop a port entry from a boolean). Safe on-prem default. BREAKING: public-domain installs must set `COMPOSE_FILE=docker-compose.yml:docker-compose.public.yml`. | Spec-Challenge Notes (T2); commit `655aff4` |
| 2026-10-26 | fede / Claude Code | `deploy.sh` expands `.env` `COMPOSE_FILE` (colon-separated, relative to project root) into explicit `-f` flags and fails fast on a missing file | Its hardcoded `-f docker-compose.yml` would otherwise silently drop the public override. | commit `655aff4` |
| 2026-10-26 | fede / Claude Code | `deploy.sh` `check_ingress_ports` refuses `up`/`update`/`rollback` when `SERVER_NAME` does not start with `:` and `docker-compose.public.yml` is not listed in `COMPOSE_FILE`; runs before any pull or `.env` change | Prevents domain installs from silently losing HTTPS/ACME after the T2 breaking change. Known limits (§4b.6): `host:port` values are refused, and rollback is hard-gated. Both are follow-up candidates. | commit `80d16cc`; RDD `review-de7172b99765d4a7` |

---

## 4. Spec-Challenge Notes (T1, Claude Code, 2026-10-26)

1. **Resolved:** the `RUN_MIGRATIONS_ARTICLES` default conflicted between spec §5.1 (`false`) and tasks.md T1 (`true`). The human chose `true` plus a warning comment (see §3).
2. **Scope:** T1 also touches `docker-compose.yml` (`x-backend-env` pass-through; without it `.env` values never reach the container) and `backend/tests/unit/test_docker_entrypoint.py`.
3. **Semantics:** only the literal `true` enables a switch, matching the existing `RUN_MIGRATIONS` contract. Each skipped config is logged as `Skipping migrations: <cfg>`.
4. **Format:** spec §5.1 uses inline `# ...` comments; `.env.example` keeps comments on their own lines.

## 4b. Spec-Challenge Notes (T2, Claude Code, 2026-10-26)

1. **Target files:** the build prompt listed `backend/docker-entrypoint.sh`; tasks.md T2 lists `docker-compose.yml`. The entrypoint was left untouched (no port logic).
2. **Resolved:** `BIND_HOST_PORTS=false` (spec §5.1) is not expressible in Compose. The human chose an opt-in `docker-compose.public.yml` (new file).
3. **Resolved:** `deploy.sh` forced `-f docker-compose.yml`, ignoring `COMPOSE_FILE`. The human approved extending scope to `scripts/devops/deploy.sh` + `backend/tests/unit/test_deploy_script.py`.
4. **T3 must document** the `COMPOSE_FILE` line for public-domain installs (breaking change for existing domain deployments).
5. **RDD advisories (non-blocking, follow-up candidates):** (a) ~~R1/R3/R4: `deploy.sh` does not warn when `SERVER_NAME` is a domain but `COMPOSE_FILE` lacks the public override~~ fixed in `80d16cc` (`check_ingress_ports`, RDD `review-de7172b99765d4a7` approved); (b) R3: `compose_files` runs via process substitution, so its failure is not propagated under `set -e`; (c) R2: `COMPOSE_FILES` array not declared `local`, and the preflight comment implies `docker-compose.yml` is always included (COMPOSE_FILE replaces it); (d) R3: no tests for absolute-path / empty-segment `COMPOSE_FILE` entries.
6. **Ingress guard advisories (RDD `review-de7172b99765d4a7`, non-blocking):** (a) R3-001: any `SERVER_NAME` not starting with `:` is treated as needing 80/443, so `host:8080` / `IP:8080` values that worked before are now refused; (b) R4: the guard only recognises the basename `docker-compose.public.yml`; (c) R4: `rollback` (the recovery path) is hard-gated by the guard; consider warn-only there; (d) R3: rollback test does not assert the stderr message; no explicit `SERVER_NAME=:8080` test.

## 5. Open Questions & Blockers

- None. All open questions resolved and specification approved by human engineer.

---

## 6. Next Action

- **Claude Code (Build Agent)**: Execute vertical slice `T3` (on-premise runbook; include the `COMPOSE_FILE` public-override note from §4b.4).

