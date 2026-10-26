#!/usr/bin/env bash
# Container entrypoint: optionally apply migrations, then start the API.
# SECRET_KEY validation is intentionally NOT done here; the FastAPI lifespan owns it.
set -eo pipefail

# `serve` (the image default) starts the API; extra arguments are forwarded to
# uvicorn (e.g. `serve --reload` in the dev override, so migrations still run).
# Any other command, including a custom `uvicorn ...` invocation, is exec'd
# untouched and skips migrations.
if [ "${1:-serve}" != "serve" ]; then
    exec "$@"
fi
shift || true

# $1 = per-database switch value, $2 = Alembic config file.
migrate() {
    if [ "$1" != "true" ]; then
        echo "Skipping migrations: $2"
        return 0
    fi
    echo "Applying migrations: $2"
    alembic -c "backend/migrations/$2" upgrade head
}

# RUN_MIGRATIONS is the master switch; the per-database switches only narrow it.
# Set RUN_MIGRATIONS_ARTICLES=false when db_articles is an external read-only DB.
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    cd "${APP_DIR:-/app}"
    migrate "${RUN_MIGRATIONS_ARTICLES:-true}" alembic.ini
    migrate "${RUN_MIGRATIONS_USERS:-true}" alembic_users.ini
    migrate "${RUN_MIGRATIONS_ANALYTICS:-true}" alembic_analytics.ini
fi

# Port 8000 is shared with EXPOSE and HEALTHCHECK in the Dockerfile and with the
# Caddy upstream; change them together. Access logs are off because the Caddy
# ingress already logs every request.
exec uvicorn backend.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-2}" \
    --no-access-log \
    "$@"
