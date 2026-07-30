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
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Project Paths & Constants ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

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
    if command -v docker-compose &>/dev/null; then
        echo "docker-compose"
    elif docker compose version &>/dev/null; then
        echo "docker compose"
    else
        log_error "Neither 'docker-compose' nor 'docker compose' was found on system PATH."
        exit 1
    fi
}

COMPOSE_CMD=$(get_compose_cmd)

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

# --- MariaDB Health Gate ---
wait_for_health() {
    local max_wait=60
    local interval=5
    local elapsed=0

    log_info "Waiting for MariaDB container engine to pass health checks (timeout: ${max_wait}s)..."

    while [ ${elapsed} -lt ${max_wait} ]; do
        if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T mariadb mariadb-admin ping -h 127.0.0.1 --silent &>/dev/null; then
            log_info "MariaDB is healthy and responding to connection probes!"
            
            # Additional DB verification probe
            log_info "Verifying multi-database consolidation schemas:"
            ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T mariadb mariadb -u root -p"$(grep MARIADB_ROOT_PASSWORD "${ENV_FILE}" | cut -d '=' -f2)" -e "SHOW DATABASES LIKE 'db_%';" 2>/dev/null || true
            return 0
        fi

        log_warn "Database not ready yet... (${elapsed}s/${max_wait}s)"
        sleep ${interval}
        elapsed=$((elapsed + interval))
    done

    log_error "MariaDB failed to reach healthy state within ${max_wait} seconds."
    return 1
}

# --- Service Operations ---
action_up() {
    check_prerequisites
    log_info "Starting MariaDB consolidated service..."
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --remove-orphans
    wait_for_health
    log_info "Deployment completed successfully!"
}

action_down() {
    log_info "Stopping MariaDB container service (persistent volume mariadb_data is PRESERVED)..."
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down
    log_info "Services stopped successfully."
}

action_status() {
    log_info "Checking container status and port bindings:"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" ps
}

action_health() {
    log_info "Running connectivity check on MariaDB container..."
    if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T mariadb mariadb-admin ping -h 127.0.0.1 --silent &>/dev/null; then
        echo -e "${GREEN}Status: HEALTHY${NC}"
    else
        echo -e "${RED}Status: UNHEALTHY / UNREACHABLE${NC}"
        exit 1
    fi
}

action_logs() {
    log_info "Tailing MariaDB logs (last 50 lines)..."
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" logs --tail=50 -f mariadb
}

show_usage() {
    cat << EOF
Usage: $(basename "$0") <command>

Single-File Deployment & Lifecycle Automation for MariaDB Consolidated Infrastructure.

Commands:
  up        Start MariaDB multi-database container (runs initialization on first boot)
  down      Stop containers gracefully (preserves persistent database volume)
  status    Display current container status and health
  health    Execute instant health check probe
  logs      Follow container output logs (tail 50 lines)
  help      Show this usage documentation

EOF
}

# --- Command Router ---
main() {
    local cmd="${1:-help}"

    case "${cmd}" in
        up)
            action_up
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
            action_logs
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
