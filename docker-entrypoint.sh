#!/bin/bash
set -e

# =============================================================================
# RECIPEZ DOCKER ENTRYPOINT
# =============================================================================
# Container startup orchestration script that:
# 1. Builds DATABASE_URL from components if not provided
# 2. Waits for database readiness
# 3. Runs Flask-Migrate migrations
# 4. Optionally initializes database with seed data
# 5. Starts the application server

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# DATABASE_URL CONSTRUCTION
# =============================================================================
# Priority: Use DATABASE_URL if provided, otherwise build from components

if [ -z "$DATABASE_URL" ]; then
    log_info "DATABASE_URL not set, building from components..."

    # Required variables
    if [ -z "$DB_HOST" ]; then
        log_error "DB_HOST is required when DATABASE_URL is not set"
        exit 1
    fi
    if [ -z "$DB_USER" ]; then
        log_error "DB_USER is required when DATABASE_URL is not set"
        exit 1
    fi
    if [ -z "$DB_PASSWORD" ]; then
        log_error "DB_PASSWORD is required when DATABASE_URL is not set"
        exit 1
    fi
    if [ -z "$DB_NAME" ]; then
        log_error "DB_NAME is required when DATABASE_URL is not set"
        exit 1
    fi

    # Optional with defaults
    DB_PORT="${DB_PORT:-5432}"
    DB_SCHEMA="${DB_SCHEMA:-recipez}"

    # Build the URL with schema in search_path
    # Format: postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE?options=-c%20search_path=SCHEMA
    export DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?options=-c%20search_path=${DB_SCHEMA}"

    log_info "DATABASE_URL constructed for host: ${DB_HOST}:${DB_PORT}/${DB_NAME} (schema: ${DB_SCHEMA})"
else
    log_info "Using provided DATABASE_URL"
fi

# =============================================================================
# WAIT FOR DATABASE
# =============================================================================
wait_for_db() {
    local max_attempts="${DB_WAIT_TIMEOUT:-30}"
    local attempt=1

    log_info "Waiting for database to be ready (max ${max_attempts} attempts)..."

    # Extract host and port from DATABASE_URL for connection check
    # Use Python to parse since bash regex is limited
    local db_check
    db_check=$(python3 -c "
import os
from urllib.parse import urlparse
url = os.environ.get('DATABASE_URL', '')
parsed = urlparse(url.replace('+psycopg', ''))
print(f'{parsed.hostname}:{parsed.port or 5432}')
" 2>/dev/null || echo "localhost:5432")

    local db_host="${db_check%:*}"
    local db_port="${db_check#*:}"

    log_info "Checking database connectivity at ${db_host}:${db_port}..."

    while [ $attempt -le $max_attempts ]; do
        if python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(('${db_host}', ${db_port}))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
            log_info "Database is accepting connections!"
            return 0
        fi

        log_warn "Database not ready (attempt ${attempt}/${max_attempts}), waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_error "Database did not become ready in time"
    return 1
}

# =============================================================================
# DATABASE MIGRATIONS
# =============================================================================
run_migrations() {
    log_info "Running database migrations..."

    # Set environment variable to skip DB bootstrap during migration CLI
    export SKIP_DB_BOOTSTRAP=1

    # Run migrations
    if flask db upgrade; then
        log_info "Migrations completed successfully"
    else
        log_error "Migration failed!"
        return 1
    fi

    unset SKIP_DB_BOOTSTRAP
}

# =============================================================================
# INITIAL DATA SETUP (Optional)
# =============================================================================
init_database() {
    if [ "${INIT_DB:-false}" = "true" ]; then
        log_info "Running database initialization (INIT_DB=true)..."
        export SKIP_DB_BOOTSTRAP=1
        if flask init-db; then
            log_info "Database initialization complete"
        else
            log_warn "Database initialization had issues (may already be initialized)"
        fi
        unset SKIP_DB_BOOTSTRAP
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================
main() {
    log_info "Starting Recipez container..."

    # Wait for database
    if ! wait_for_db; then
        exit 1
    fi

    # Run migrations
    if ! run_migrations; then
        exit 1
    fi

    # Optional: Initialize database with seed data
    init_database

    log_info "Starting application server..."

    # Execute the command passed to the container
    exec "$@"
}

main "$@"
