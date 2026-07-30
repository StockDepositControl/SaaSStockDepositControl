# 🚀 Multi-Database Container Deployment Runbook

This document provides deployment guidelines and operational runbooks for running the consolidated **MariaDB 10.11 LTS** database infrastructure for the SaaS Stock Deposit Control project.

---

## 1. Architecture Overview

To minimize RAM memory overhead and physical disk usage, three independent backend logical databases are consolidated into a **single containerized MariaDB engine**:

| Database Name | Purpose | Application Env Var |
|:--------------|:--------|:--------------------|
| `db_articles` | Operational Catalog, Stock & FEFO movements | `DB_NAME_ARTICLES` / `DATABASE_URL` |
| `db_users` | Multi-tenant user authentication & RBAC roles | `DB_NAME_USERS` / `USERS_DATABASE_URL` |
| `db_analytics` | Audit records, daily reports & shrinkage alerts | `DB_NAME_ANALYTICS` / `ANALYTICS_DATABASE_URL` |

### Key Benefits

- **Single Memory Pool**: Shares InnoDB buffer pool across all three databases.
- **Automated Initialization**: Database schemas are auto-created on container first boot via `docker/mariadb/init-dbs.sql`.
- **Persistent Volume**: Data is preserved across container recreations inside the Docker volume `mariadb_data`.

---

## 2. Quick Start (Single-File Deployment)

The deployment process is fully automated using `scripts/devops/deploy.sh`.

### Step 1: Prepare Environment File

Copy the template file to create your active `.env`:

```bash
cp .env.example .env
```

Review `.env` and set secure passwords for `MARIADB_ROOT_PASSWORD` and `MARIADB_APP_PASSWORD`.

### Step 2: Launch Database Infrastructure

Run the deployment script:

```bash
./scripts/devops/deploy.sh up
```

The script will automatically:
1. Verify system pre-requisites (`docker`, `docker-compose`, `.env`).
2. Launch the MariaDB container detached.
3. Wait for the engine to become healthy (`mariadb-admin ping`).
4. Display database initialization confirmation.

---

## 3. Operational Commands

### Check Status & Health

```bash
# View container status and port mapping
./scripts/devops/deploy.sh status

# Run instant connectivity check
./scripts/devops/deploy.sh health
```

### View Engine Logs

```bash
# Tail live container output logs
./scripts/devops/deploy.sh logs
```

### Stop Infrastructure

```bash
# Stop MariaDB service (Data remains safe in mariadb_data volume)
./scripts/devops/deploy.sh down
```

---

## 4. Troubleshooting & Maintenance

### Reset Database Volume (Destructive Action)

> ⚠️ **CAUTION:** The following command permanently removes all stored data in `mariadb_data`.

```bash
docker-compose down -v
```

Re-running `./scripts/devops/deploy.sh up` after this will trigger a fresh initialization from `docker/mariadb/init-dbs.sql`.
