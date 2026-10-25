#!/usr/bin/env bash

# ==============================================================================
# SaaS Stock Deposit Control — Single-File Deployment Automation Script
# Maintainer: Alex (Senior DevOps & SRE Specialist)
# Standard: Strict Bash (set -euo pipefail), portable, defensive
# ==============================================================================

set -euo pipefail

# --- Color Definitions & Formatting ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Project Paths & Constants ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# DEPLOY_ROOT lets tests (and unusual layouts) point the script at another tree.
PROJECT_ROOT="${DEPLOY_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
PREVIOUS_TAG_FILE="${PROJECT_ROOT}/.previous_tag"
BACKUP_DIR="${PROJECT_ROOT}/backups"

# Rollback window: how long a new deployment may take to become healthy.
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-60}"
HEALTH_INTERVAL="${HEALTH_INTERVAL:-5}"

DATABASES=(db_articles db_users db_analytics)
SERVICES_TO_PULL=(backend web)

# --- Logging Helpers ---
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $*" >&2
}

# --- Cleanup & Error Handling Trap ---
cleanup_on_error() {
    local exit_code=$?
    if [ ${exit_code} -ne 0 ]; then
        log_error "Deployment script terminated unexpectedly with exit code ${exit_code}."
    fi
}
trap cleanup_on_error EXIT

# --- Compose CLI Command Resolver ---
get_compose_cmd() {
    if docker compose version &>/dev/null; then
        echo "docker compose"
    elif command -v docker-compose &>/dev/null; then
        echo "docker-compose"
    else
        log_error "Neither 'docker compose' nor 'docker-compose' was found on system PATH."
        exit 1
    fi
}

COMPOSE_CMD=$(get_compose_cmd)

compose() {
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" "$@"
}

# --- .env Helpers (never `source` the file: values are data, not shell) ---
env_get() {
    local key="$1" value
    [ -f "${ENV_FILE}" ] || return 0
    value=$(grep -E "^${key}=" "${ENV_FILE}" | tail -n1 | cut -d '=' -f2- || true)
    value="${value%\"}"; value="${value#\"}"
    value="${value%\'}"; value="${value#\'}"
    printf '%s' "${value}"
}

env_set() {
    local key="$1" value="$2"
    if grep -qE "^${key}=" "${ENV_FILE}"; then
        sed -i "s|^${key}=.*|${key}=${value}|" "${ENV_FILE}"
    else
        # Guard against a missing trailing newline gluing two entries together.
        if [ -s "${ENV_FILE}" ] && [ -n "$(tail -c1 "${ENV_FILE}")" ]; then
            echo >> "${ENV_FILE}"
        fi
        printf '%s=%s\n' "${key}" "${value}" >> "${ENV_FILE}"
    fi
}

# --- Pre-flight Checks ---
check_prerequisites() {
    log_info "Running deployment pre-flight checks..."

    # Check Docker engine availability
    if ! command -v docker &>/dev/null; then
        log_error "Docker is not installed or not available in PATH."
        exit 1
    fi

    if ! docker info &>/dev/null; then
        log_error "Docker daemon is not running or current user lacks access permission."
        exit 1
    fi

    if ! command -v curl &>/dev/null; then
        log_error "curl is required for health probes but was not found in PATH."
        exit 1
    fi

    if ! [[ "${HEALTH_TIMEOUT}" =~ ^[0-9]+$ ]] || ! [[ "${HEALTH_INTERVAL}" =~ ^[1-9][0-9]*$ ]]; then
        log_error "HEALTH_TIMEOUT must be an integer >= 0 and HEALTH_INTERVAL an integer >= 1 (seconds)."
        exit 1
    fi

    # Check environment file
    if [ ! -f "${ENV_FILE}" ]; then
        log_warn ".env file not found at ${ENV_FILE}."
        if [ -f "${ENV_EXAMPLE}" ]; then
            log_info "Copying template from .env.example..."
            cp "${ENV_EXAMPLE}" "${ENV_FILE}"
            log_warn "Created .env from template. Please update passwords in ${ENV_FILE} before production use!"
        else
            log_error ".env file missing and .env.example template not found."
            exit 1
        fi
    fi

    # Check compose file
    if [ ! -f "${COMPOSE_FILE}" ]; then
        log_error "docker-compose.yml not found at ${COMPOSE_FILE}."
        exit 1
    fi

    log_info "Pre-flight checks passed."
}

# --- Image Tag Helpers ---
validate_tag() {
    local tag="$1"
    # Docker tag grammar; also keeps the value safe for sed and .env.
    if ! [[ "${tag}" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
        log_error "Invalid image tag: '${tag}'."
        exit 1
    fi
}

current_tag() {
    local tag
    tag="$(env_get IMAGE_TAG)"
    echo "${tag:-latest}"
}

# --- Health Gates ---
# Public health endpoint through the ingress proxy, derived from SERVER_NAME
# (":8080" = plain HTTP on HTTP_PORT, otherwise a domain served over HTTPS).
default_health_url() {
    local server_name http_port
    server_name="$(env_get SERVER_NAME)"
    server_name="${server_name:-:8080}"
    http_port="$(env_get HTTP_PORT)"
    http_port="${http_port:-8080}"

    case "${server_name}" in
        :*)
            echo "http://127.0.0.1:${http_port}/api/v1/health"
            ;;
        http://*|https://*)
            echo "${server_name%/}/api/v1/health"
            ;;
        *)
            echo "https://${server_name}/api/v1/health"
            ;;
    esac
}

# Healthy means HTTP 200 *and* the body reports it (all 3 databases connected).
probe_health() {
    local url="$1" body
    local -a flags=(-fsS -m 5)
    if [[ "${url}" == https://* ]]; then
        flags+=(-k)
    fi
    body=$(curl "${flags[@]}" "${url}" 2>/dev/null) || return 1
    [[ "${body}" == *'"status":"healthy"'* ]]
}

wait_for_api_health() {
    local url="${HEALTH_URL:-$(default_health_url)}"
    local elapsed=0

    log_info "Waiting for ${url} to report healthy (timeout: ${HEALTH_TIMEOUT}s)..."

    while true; do
        if probe_health "${url}"; then
            log_info "Health check passed."
            return 0
        fi
        if [ "${elapsed}" -ge "${HEALTH_TIMEOUT}" ]; then
            break
        fi
        log_warn "Not healthy yet... (${elapsed}s/${HEALTH_TIMEOUT}s)"
        sleep "${HEALTH_INTERVAL}"
        elapsed=$((elapsed + HEALTH_INTERVAL))
    done

    log_error "Health check failed within ${HEALTH_TIMEOUT} seconds."
    return 1
}

# --- Service Operations ---
action_up() {
    local -a profile_args=()
    if [ "${1:-}" = "with-db" ]; then
        profile_args=(--profile with-db)
    elif [ -n "${1:-}" ]; then
        log_error "Unknown profile: ${1} (supported: with-db)"
        exit 1
    fi

    check_prerequisites
    log_info "Starting services..."
    compose ${profile_args[@]+"${profile_args[@]}"} up -d --remove-orphans
    wait_for_api_health
    log_info "Deployment completed successfully!"
}

action_down() {
    log_info "Stopping container services (persistent volume mariadb_data is PRESERVED)..."
    compose down
    log_info "Services stopped successfully."
}

action_status() {
    log_info "Checking container status and port bindings:"
    compose ps
}

action_health() {
    check_prerequisites
    local url="${HEALTH_URL:-$(default_health_url)}"
    if probe_health "${url}"; then
        echo -e "API + databases (${url}): ${GREEN}HEALTHY${NC}"
    else
        echo -e "API + databases (${url}): ${RED}UNHEALTHY / UNREACHABLE${NC}"
        exit 1
    fi
}

action_logs() {
    local target="${1:-}"
    if [ -n "${target}" ]; then
        log_info "Tailing ${target} logs (last 50 lines)..."
        compose logs --tail=50 -f "${target}"
    else
        log_info "Tailing service logs (last 50 lines)..."
        compose logs --tail=50 -f
    fi
}

# --- Release Lifecycle: pull / update / rollback ---
action_pull() {
    check_prerequisites
    log_info "Pulling images for IMAGE_TAG=$(current_tag)..."
    compose pull "${SERVICES_TO_PULL[@]}"
}

# Switches IMAGE_TAG to the tag recorded in .previous_tag and verifies health.
perform_rollback() {
    if [ ! -s "${PREVIOUS_TAG_FILE}" ]; then
        log_error "No rollback target: ${PREVIOUS_TAG_FILE} is missing or empty."
        return 1
    fi

    local previous
    previous="$(head -n1 "${PREVIOUS_TAG_FILE}" | tr -d '[:space:]')"
    validate_tag "${previous}"

    log_warn "Rolling back to IMAGE_TAG=${previous}..."
    env_set IMAGE_TAG "${previous}"
    compose up -d --remove-orphans
    wait_for_api_health
}

action_rollback() {
    check_prerequisites
    perform_rollback
    log_info "Rollback completed."
}

action_update() {
    check_prerequisites

    local current new_tag
    current="$(current_tag)"
    new_tag="${1:-${current}}"
    validate_tag "${new_tag}"

    # Pull first, with the new tag only in this command's environment: a failed
    # pull aborts before .env or .previous_tag change, so nothing is half-applied.
    log_info "Pulling images for IMAGE_TAG=${new_tag}..."
    IMAGE_TAG="${new_tag}" compose pull "${SERVICES_TO_PULL[@]}"

    # Never overwrite the rollback target with the tag being re-deployed.
    if [ "${new_tag}" != "${current}" ]; then
        printf '%s\n' "${current}" > "${PREVIOUS_TAG_FILE}"
    fi
    env_set IMAGE_TAG "${new_tag}"

    if compose up -d --remove-orphans && wait_for_api_health; then
        log_info "Update to ${new_tag} completed successfully."
        return 0
    fi

    log_error "Update to ${new_tag} failed; reverting to the previous tag."
    if ! perform_rollback; then
        log_error "Automatic rollback also failed; manual intervention required."
    fi
    exit 1
}

# --- Backup ---
dump_databases() {
    local running
    running="$(compose ps --services --status running 2>/dev/null || true)"

    if grep -qx mariadb <<< "${running}"; then
        log_info "Dumping from the bundled MariaDB container..." >&2
        # The root password stays inside the container environment: nothing
        # secret appears in host argv or in this script's environment.
        compose exec -T mariadb sh -c \
            'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" exec mariadb-dump -u root --single-transaction --databases "$@"' \
            sh "${DATABASES[@]}"
        return
    fi

    # External database: needs a client on this host, DB_* components from .env.
    local dump_bin extra=()
    if command -v mariadb-dump &>/dev/null; then
        dump_bin="mariadb-dump"
    elif command -v mysqldump &>/dev/null; then
        dump_bin="mysqldump"
        extra+=(--no-tablespaces)
    else
        log_error "Bundled MariaDB is not running and neither mariadb-dump nor mysqldump is installed." >&2
        return 1
    fi

    case "$(env_get DB_SSL_MODE)" in
        require)
            extra+=(--ssl)
            ;;
        verify-ca)
            extra+=(--ssl)
            if [ -n "$(env_get DB_SSL_CA)" ]; then
                extra+=("--ssl-ca=$(env_get DB_SSL_CA)")
            fi
            ;;
    esac

    log_info "Dumping from external database $(env_get DB_HOST):$(env_get DB_PORT)..." >&2
    MYSQL_PWD="$(env_get DB_PASSWORD)" "${dump_bin}" \
        -h "$(env_get DB_HOST)" -P "$(env_get DB_PORT)" -u "$(env_get DB_USER)" \
        --single-transaction ${extra[@]+"${extra[@]}"} --databases "${DATABASES[@]}"
}

action_backup() {
    check_prerequisites

    mkdir -p -m 700 "${BACKUP_DIR}"
    local target tmp
    target="${BACKUP_DIR}/backup_$(date +%Y%m%d_%H%M%S).sql.gz"
    # mktemp creates the file 0600; a failed dump never leaves a plausible archive.
    tmp="$(mktemp "${BACKUP_DIR}/.backup.XXXXXX")"

    if ! dump_databases | gzip > "${tmp}"; then
        rm -f "${tmp}"
        log_error "Database dump failed; no archive was written."
        exit 1
    fi

    chmod 600 "${tmp}"
    mv "${tmp}" "${target}"
    log_info "Backup written to ${target}"
}

show_usage() {
    cat << EOF
Usage: $(basename "$0") <command> [argument]

Deployment & lifecycle automation for the SaaS Stock Deposit Control stack.

Commands:
  up [with-db]       Start services (with-db adds the bundled MariaDB) and wait for health
  down               Stop containers gracefully (preserves persistent database volume)
  status             Display current container status, health, and port bindings
  health             Probe /api/v1/health through the proxy (API + all 3 databases)
  logs [service]     Follow container output logs (tail 50 lines)
  pull               Pull the images for the current IMAGE_TAG
  update [tag]       Deploy a new IMAGE_TAG; reverts to .previous_tag if not healthy in time
  rollback           Redeploy the tag recorded in .previous_tag and verify health
  backup             Dump db_articles, db_users and db_analytics to backups/backup_<timestamp>.sql.gz
  help               Show this usage documentation

Environment:
  HEALTH_TIMEOUT     Seconds to wait for a healthy deployment before rolling back (default: 60)
  HEALTH_INTERVAL    Seconds between health probes (default: 5)
  HEALTH_URL         Override the probed URL (default derived from SERVER_NAME / HTTP_PORT in .env)

EOF
}

# --- Command Router ---
main() {
    local cmd="${1:-help}"

    case "${cmd}" in
        up)
            action_up "${2:-}"
            ;;
        down)
            action_down
            ;;
        status)
            action_status
            ;;
        health)
            action_health
            ;;
        logs)
            action_logs "${2:-}"
            ;;
        pull)
            action_pull
            ;;
        update)
            action_update "${2:-}"
            ;;
        rollback)
            action_rollback
            ;;
        backup)
            action_backup
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: ${cmd}"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
