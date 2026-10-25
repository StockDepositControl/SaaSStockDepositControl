#!/usr/bin/env bash
# Container entrypoint: optionally apply migrations, then start the API.
# SECRET_KEY validation is intentionally NOT done here; the FastAPI lifespan owns it.
set -eo pipefail

# Any command other than the default one (e.g. `python -c ...`) runs as-is.
if [ "${1:-uvicorn}" != "uvicorn" ]; then
    exec "$@"
fi

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    cd /app
    for cfg in alembic.ini alembic_users.ini alembic_analytics.ini; do
        echo "Applying migrations: ${cfg}"
        alembic -c "backend/migrations/${cfg}" upgrade head
    done
fi

exec uvicorn backend.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-2}" \
    --no-access-log
