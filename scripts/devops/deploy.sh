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

# --- Health Gates ---
wait_for_mariadb() {
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

wait_for_nginx() {
    local max_wait=30
    local interval=3
    local elapsed=0
    local nginx_port
    nginx_port=$(grep -E "^NGINX_PORT=" "${ENV_FILE}" 2>/dev/null | cut -d '=' -f2 || echo "8080")
    nginx_port="${nginx_port:-8080}"

    log_info "Waiting for NGINX ingress proxy to pass health checks (port: ${nginx_port}, timeout: ${max_wait}s)..."

    while [ ${elapsed} -lt ${max_wait} ]; do
        if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T nginx wget --no-verbose --spider http://127.0.0.1:8080/nginx-health &>/dev/null; then
            log_info "NGINX ingress proxy is healthy and serving requests on port ${nginx_port}!"
            return 0
        fi

        log_warn "NGINX not ready yet... (${elapsed}s/${max_wait}s)"
        sleep ${interval}
        elapsed=$((elapsed + interval))
    done

    log_error "NGINX failed to reach healthy state within ${max_wait} seconds."
    return 1
}

wait_for_health() {
    wait_for_mariadb
    wait_for_nginx
}

# --- Service Operations ---
action_up() {
    check_prerequisites
    log_info "Starting infrastructure services (MariaDB + NGINX ingress)..."
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --remove-orphans
    wait_for_health
    log_info "Deployment completed successfully!"
}

action_down() {
    log_info "Stopping infrastructure container services (persistent volume mariadb_data is PRESERVED)..."
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down
    log_info "Services stopped successfully."
}

action_status() {
    log_info "Checking container status and port bindings:"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" ps
}

action_health() {
    local all_healthy=0
    log_info "Running connectivity checks on infrastructure containers..."

    # MariaDB check
    if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T mariadb mariadb-admin ping -h 127.0.0.1 --silent &>/dev/null; then
        echo -e "MariaDB (saas-stock-mariadb): ${GREEN}HEALTHY${NC}"
    else
        echo -e "MariaDB (saas-stock-mariadb): ${RED}UNHEALTHY / UNREACHABLE${NC}"
        all_healthy=1
    fi

    # NGINX internal container check
    if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T nginx wget --no-verbose --spider http://127.0.0.1:8080/nginx-health &>/dev/null; then
        echo -e "NGINX (saas-stock-nginx): ${GREEN}HEALTHY${NC}"
    else
        echo -e "NGINX (saas-stock-nginx): ${RED}UNHEALTHY / UNREACHABLE${NC}"
        all_healthy=1
    fi

    # Host-level NGINX port probe
    local nginx_port
    nginx_port=$(grep -E "^NGINX_PORT=" "${ENV_FILE}" 2>/dev/null | cut -d '=' -f2 || echo "8080")
    nginx_port="${nginx_port:-8080}"
    if command -v curl &>/dev/null; then
        if curl -fs "http://127.0.0.1:${nginx_port}/nginx-health" &>/dev/null; then
            echo -e "NGINX Ingress Host Port (${nginx_port}): ${GREEN}ACCESSIBLE${NC}"
        else
            echo -e "NGINX Ingress Host Port (${nginx_port}): ${YELLOW}PORT NOT BOUND OR INACCESSIBLE${NC}"
        fi

        # Probe backend through NGINX proxy
        if curl -fs "http://127.0.0.1:${nginx_port}/api/v1/health" &>/dev/null; then
            echo -e "Backend Proxy via NGINX (/api/v1/health): ${GREEN}HEALTHY (200 OK)${NC}"
        else
            echo -e "Backend Proxy via NGINX (/api/v1/health): ${YELLOW}BACKEND OFFLINE (run backend on host port 8000)${NC}"
        fi
    fi

    if [ ${all_healthy} -ne 0 ]; then
        exit 1
    fi
}

action_logs() {
    local target="${1:-}"
    if [ -n "${target}" ]; then
        log_info "Tailing ${target} logs (last 50 lines)..."
        ${COMPOSE_CMD} -f "${COMPOSE_FILE}" logs --tail=50 -f "${target}"
    else
        log_info "Tailing infrastructure logs (last 50 lines)..."
        ${COMPOSE_CMD} -f "${COMPOSE_FILE}" logs --tail=50 -f
    fi
}

show_usage() {
    cat << EOF
Usage: $(basename "$0") <command> [service]

Single-File Deployment & Lifecycle Automation for MariaDB Consolidated Infrastructure & NGINX Ingress Proxy.

Commands:
  up                 Start infrastructure containers (MariaDB + NGINX)
  down               Stop containers gracefully (preserves persistent database volume)
  status             Display current container status, health, and port bindings
  health             Execute instant health check probes (MariaDB and NGINX)
  logs [service]     Follow container output logs (tail 50 lines; optional: mariadb, nginx)
  help               Show this usage documentation

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
            action_logs "${2:-}"
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
