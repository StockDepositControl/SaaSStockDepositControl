#!/usr/bin/env bash
# Container entrypoint: optionally apply migrations, then start the API.
# SECRET_KEY validation is intentionally NOT done here; the FastAPI lifespan owns it.
set -eo pipefail

# `serve` (the image default) starts the API. Any other command, including a
# custom `uvicorn ...` invocation, is exec'd untouched and skips migrations.
if [ "${1:-serve}" != "serve" ]; then
    exec "$@"
fi

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    cd /app
    for cfg in alembic.ini alembic_users.ini alembic_analytics.ini; do
        echo "Applying migrations: ${cfg}"
        alembic -c "backend/migrations/${cfg}" upgrade head
    done
fi

# Port 8000 is shared with EXPOSE and HEALTHCHECK in the Dockerfile and with the
# Caddy upstream; change them together. Access logs are off because the Caddy
# ingress already logs every request.
exec uvicorn backend.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-2}" \
    --no-access-log
