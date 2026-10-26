#!/usr/bin/env bash

# ==============================================================================
# SaaS Stock Deposit Control — On-Premise Package Verification
# Read-only probe: checks .env, Compose config, external DB reachability and
# GET /api/v1/health. Runs every check, reports all failures, exits 1 if any.
# Secrets are never printed.
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# DEPLOY_ROOT lets tests (and unusual layouts) point the script at another tree.
PROJECT_ROOT="${DEPLOY_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
ENV_FILE="${PROJECT_ROOT}/.env"

HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-10}"
TCP_TIMEOUT="${TCP_TIMEOUT:-3}"
LOGICAL_DATABASES=(articles users analytics)

FAILURES=0

pass() { echo -e "${GREEN}[PASS]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*" >&2; FAILURES=$((FAILURES + 1)); }

# Values are data, never `source` the file.
env_get() {
    local key="$1" value
    value=$(grep -E "^${key}=" "${ENV_FILE}" | tail -n1 | cut -d '=' -f2- || true)
    value="${value%\"}"; value="${value#\"}"
    value="${value%\'}"; value="${value#\'}"
    printf '%s' "${value}"
}

check_env_file() {
    if [ ! -f "${ENV_FILE}" ]; then
        fail ".env not found at ${ENV_FILE} (copy .env.example and fill it in)."
        return 1
    fi

    local line_no=0 line bad=0
    while IFS= read -r line || [ -n "${line}" ]; do
        line_no=$((line_no + 1))
        [[ -z "${line// }" || "${line}" =~ ^[[:space:]]*# ]] && continue
        if [[ ! "${line}" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
            fail ".env line ${line_no} is not KEY=VALUE (no spaces around '=')."
            bad=1
        fi
    done < "${ENV_FILE}"

    if [ -z "$(env_get SECRET_KEY)" ]; then
        fail "SECRET_KEY is empty in .env."
        bad=1
    fi

    local key value
    for key in RUN_MIGRATIONS RUN_MIGRATIONS_ARTICLES RUN_MIGRATIONS_USERS RUN_MIGRATIONS_ANALYTICS; do
        value="$(env_get "${key}")"
        if [ -n "${value}" ] && [ "${value}" != "true" ] && [ "${value}" != "false" ]; then
            fail "${key} must be 'true' or 'false'."
            bad=1
        fi
    done

    value="$(env_get HTTP_PORT)"
    if [ -n "${value}" ] && [[ ! "${value}" =~ ^[0-9]+$ ]]; then
        fail "HTTP_PORT must be numeric."
        bad=1
    fi

    [ "${bad}" -eq 0 ] && pass ".env syntax and values are valid."
    return 0
}

check_compose_config() {
    local list file args=() files=()
    list="$(env_get COMPOSE_FILE)"
    IFS=':' read -r -a files <<< "${list:-docker-compose.yml}"
    for file in "${files[@]}"; do
        case "${file}" in
            /*) args+=(-f "${file}") ;;
            *) args+=(-f "${PROJECT_ROOT}/${file}") ;;
        esac
    done

    local env_args=()
    [ -f "${ENV_FILE}" ] && env_args=(--env-file "${ENV_FILE}")

    if docker compose "${args[@]}" "${env_args[@]}" config -q >/dev/null 2>&1; then
        pass "Docker Compose configuration is valid."
    else
        fail "Docker Compose configuration is invalid (run 'docker compose config' for details)."
    fi
}

# Plain TCP probe of the external db_articles host:port. No credentials are used or printed.
check_articles_reachable() {
    [ -f "${ENV_FILE}" ] || return 0
    local url hostport host port
    url="$(env_get ARTICLES_DATABASE_URL)"
    if [ -z "${url}" ]; then
        return 0
    fi

    hostport="${url#*://}"
    hostport="${hostport##*@}"
    hostport="${hostport%%/*}"
    host="${hostport%%:*}"
    port="3306"
    [[ "${hostport}" == *:* ]] && port="${hostport##*:}"

    if [ "${host}" = "host.docker.internal" ]; then
        warn "External articles DB uses host.docker.internal (resolvable only inside containers); relying on the health check."
        return 0
    fi

    if timeout "${TCP_TIMEOUT}" bash -c "exec 3<>/dev/tcp/${host}/${port}" 2>/dev/null; then
        pass "External articles database reachable at ${host}:${port}."
    else
        fail "External articles database NOT reachable at ${host}:${port}."
    fi
}

check_health() {
    local port body db
    port="$(env_get HTTP_PORT 2>/dev/null || true)"
    port="${port:-8080}"

    if ! body="$(curl -fsS --max-time "${HEALTH_TIMEOUT}" "http://localhost:${port}/api/v1/health" 2>/dev/null)"; then
        fail "Health endpoint http://localhost:${port}/api/v1/health did not return 200 (is the stack up?)."
        return 0
    fi

    local ok=1
    if [[ ! "${body}" =~ \"status\"[[:space:]]*:[[:space:]]*\"healthy\" ]]; then
        fail "Health status is not 'healthy'."
        ok=0
    fi
    for db in "${LOGICAL_DATABASES[@]}"; do
        if [[ ! "${body}" =~ \"${db}\"[[:space:]]*:[[:space:]]*\"connected\" ]]; then
            fail "Database '${db}' is not connected according to /api/v1/health."
            ok=0
        fi
    done
    [ "${ok}" -eq 1 ] && pass "Health endpoint is healthy; articles, users and analytics are connected."
    return 0
}

main() {
    echo "Verifying on-premise package in ${PROJECT_ROOT}"
    check_env_file || true
    check_compose_config
    check_articles_reachable
    check_health

    if [ "${FAILURES}" -gt 0 ]; then
        echo -e "${RED}${FAILURES} check(s) failed.${NC}" >&2
        exit 1
    fi
    echo -e "${GREEN}All checks passed.${NC}"
}

main "$@"
