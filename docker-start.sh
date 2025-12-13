#!/bin/bash
set -e

# =============================================================================
# RECIPEZ DOCKER START SCRIPT
# =============================================================================
# Convenience script for building and running Recipez in Docker.
#
# Usage:
#   ./docker-start.sh start              Start with bundled database
#   ./docker-start.sh start --init       First-time setup with seed data
#   ./docker-start.sh start-external     Use external database
#   ./docker-start.sh stop               Stop all containers
#   ./docker-start.sh logs               View container logs
#   ./docker-start.sh clean              Remove everything (DESTRUCTIVE)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_header() { echo -e "\n${BLUE}=== $1 ===${NC}\n"; }

# =============================================================================
# USAGE
# =============================================================================
usage() {
    cat << EOF
Recipez Docker Management Script

Usage: $0 <command> [options]

Commands:
    start           Start Recipez with bundled PostgreSQL
    start-external  Start Recipez with external database only
    stop            Stop all containers
    restart         Restart all containers
    logs            View container logs (follow mode)
    logs-app        View only application logs
    logs-db         View only database logs
    build           Build/rebuild the Docker image
    clean           Stop containers and remove volumes (DESTRUCTIVE)
    status          Show container status
    shell           Open a shell in the app container
    db-shell        Open psql shell in the database container
    migrate         Run database migrations manually
    backup          Backup database to local file

Options:
    --init          Initialize database with seed data (for fresh installs)
    --build         Force rebuild of images before starting
    -d, --detach    Run in detached mode (background)
    -h, --help      Show this help message

Examples:
    $0 start                    # Start with bundled database
    $0 start --init -d          # First-time setup, run in background
    $0 start-external           # Use external database (set DATABASE_URL)
    $0 logs                     # View all logs
    $0 clean                    # Remove everything (fresh start)
EOF
}

# =============================================================================
# CHECKS
# =============================================================================
check_env_file() {
    if [ ! -f ".env.docker" ]; then
        log_error ".env.docker file not found!"
        log_info "Create it from the example template:"
        echo ""
        echo "    cp .env.docker.example .env.docker"
        echo ""
        log_info "Then edit .env.docker with your configuration."
        exit 1
    fi
}

setup_directories() {
    # Create persistent data directories with proper permissions
    # Use RECIPEZ_DATA_DIR from env or default to ~/.recipez
    # shellcheck disable=SC1091
    source .env.docker 2>/dev/null || true
    local data_dir="${RECIPEZ_DATA_DIR:-$HOME/.recipez}"

    if [ ! -d "$data_dir" ]; then
        log_info "Creating data directories in $data_dir"
        mkdir -p "$data_dir"/{uploads,certs,pgdata}
        chmod 777 "$data_dir/uploads" "$data_dir/certs"
        # pgdata needs postgres user ownership (UID 70 in alpine)
        if command -v sudo &> /dev/null; then
            sudo chown 70:70 "$data_dir/pgdata" 2>/dev/null || log_warn "Could not set pgdata ownership (may need sudo)"
        fi
        log_info "Data directories created"
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        log_info "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        log_info "Start Docker and try again"
        exit 1
    fi

    # Check for docker-compose (v1) or docker compose (v2)
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        log_error "Docker Compose is not installed"
        log_info "Install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# =============================================================================
# COMMANDS
# =============================================================================
cmd_start() {
    local detach=""
    local build_flag=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --init)
                export INIT_DB=true
                log_warn "Database initialization enabled (INIT_DB=true)"
                shift
                ;;
            --build)
                build_flag="--build"
                shift
                ;;
            -d|--detach)
                detach="-d"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    check_env_file
    setup_directories

    log_header "Starting Recipez with bundled PostgreSQL"

    $COMPOSE_CMD --profile default up $build_flag $detach
}

cmd_start_external() {
    local detach=""
    local build_flag=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --init)
                export INIT_DB=true
                log_warn "Database initialization enabled (INIT_DB=true)"
                shift
                ;;
            --build)
                build_flag="--build"
                shift
                ;;
            -d|--detach)
                detach="-d"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    check_env_file

    # Verify DATABASE_URL is set
    # shellcheck disable=SC1091
    source .env.docker 2>/dev/null || true
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL must be set in .env.docker for external database mode"
        log_info "Example:"
        echo '    DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname?options=-c%20search_path=recipez'
        exit 1
    fi

    setup_directories

    log_header "Starting Recipez with external database"
    log_info "Using DATABASE_URL from .env.docker"

    $COMPOSE_CMD --profile external-db up $build_flag $detach
}

cmd_stop() {
    log_header "Stopping Recipez containers"
    $COMPOSE_CMD --profile default --profile external-db down
}

cmd_restart() {
    cmd_stop
    cmd_start "$@"
}

cmd_logs() {
    $COMPOSE_CMD --profile default --profile external-db logs -f
}

cmd_logs_app() {
    $COMPOSE_CMD logs -f app 2>/dev/null || $COMPOSE_CMD logs -f app-external
}

cmd_logs_db() {
    $COMPOSE_CMD logs -f postgres
}

cmd_build() {
    log_header "Building Recipez Docker image"
    $COMPOSE_CMD build --no-cache
}

cmd_clean() {
    log_header "Cleaning up Recipez Docker resources"
    log_warn "This will remove all containers, networks, and volumes!"
    log_warn "All data (database, uploads) will be PERMANENTLY DELETED!"
    echo ""
    read -p "Are you sure? Type 'yes' to confirm: " -r
    echo ""
    if [[ $REPLY == "yes" ]]; then
        $COMPOSE_CMD --profile default --profile external-db down -v --remove-orphans
        log_info "Cleanup complete"
    else
        log_info "Cleanup cancelled"
    fi
}

cmd_status() {
    log_header "Recipez Container Status"
    $COMPOSE_CMD --profile default --profile external-db ps
}

cmd_shell() {
    log_info "Opening shell in app container..."
    $COMPOSE_CMD exec app /bin/bash 2>/dev/null || $COMPOSE_CMD exec app-external /bin/bash
}

cmd_db_shell() {
    log_info "Opening psql shell in database container..."
    # shellcheck disable=SC1091
    source .env.docker 2>/dev/null || true
    $COMPOSE_CMD exec postgres psql -U "${DB_USER:-recipez}" -d "${DB_NAME:-recipez}"
}

cmd_migrate() {
    log_info "Running database migrations..."
    $COMPOSE_CMD exec app flask db upgrade 2>/dev/null || $COMPOSE_CMD exec app-external flask db upgrade
}

cmd_backup() {
    log_header "Backing up database"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="recipez_backup_${timestamp}.sql"

    # shellcheck disable=SC1091
    source .env.docker 2>/dev/null || true

    log_info "Creating backup: ${backup_file}"
    $COMPOSE_CMD exec -T postgres pg_dump -U "${DB_USER:-recipez}" -d "${DB_NAME:-recipez}" > "$backup_file"

    if [ -f "$backup_file" ]; then
        log_info "Backup created successfully: ${backup_file}"
        log_info "Size: $(du -h "$backup_file" | cut -f1)"
    else
        log_error "Backup failed"
        exit 1
    fi
}

# =============================================================================
# MAIN
# =============================================================================
check_docker

case "${1:-}" in
    start)
        shift
        cmd_start "$@"
        ;;
    start-external)
        shift
        cmd_start_external "$@"
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        shift
        cmd_restart "$@"
        ;;
    logs)
        cmd_logs
        ;;
    logs-app)
        cmd_logs_app
        ;;
    logs-db)
        cmd_logs_db
        ;;
    build)
        cmd_build
        ;;
    clean)
        cmd_clean
        ;;
    status)
        cmd_status
        ;;
    shell)
        cmd_shell
        ;;
    db-shell)
        cmd_db_shell
        ;;
    migrate)
        cmd_migrate
        ;;
    backup)
        cmd_backup
        ;;
    -h|--help|help)
        usage
        ;;
    "")
        usage
        exit 1
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        usage
        exit 1
        ;;
esac
