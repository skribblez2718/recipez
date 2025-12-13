#!/bin/sh
set -e

# =============================================================================
# RECIPEZ POSTGRESQL INITIALIZATION SCRIPT
# =============================================================================
# This script runs inside the PostgreSQL container during first initialization.
# It creates the 'recipez' schema required by the application.
#
# Note: This script only runs when the database data directory is empty
# (i.e., on first container start with a fresh volume).

SCHEMA_NAME="${DB_SCHEMA:-recipez}"

echo "=== Recipez PostgreSQL Initialization ==="
echo "Creating schema '${SCHEMA_NAME}' if it doesn't exist..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create the recipez schema
    CREATE SCHEMA IF NOT EXISTS ${SCHEMA_NAME};

    -- Grant all privileges on the schema to the application user
    GRANT ALL PRIVILEGES ON SCHEMA ${SCHEMA_NAME} TO ${POSTGRES_USER};

    -- Set default search path to include the schema
    ALTER DATABASE ${POSTGRES_DB} SET search_path TO ${SCHEMA_NAME}, public;

    -- Ensure future tables are created in the correct schema
    ALTER ROLE ${POSTGRES_USER} SET search_path TO ${SCHEMA_NAME}, public;

    -- Grant usage on public schema (needed for extensions like gen_random_uuid)
    GRANT USAGE ON SCHEMA public TO ${POSTGRES_USER};

    -- Output confirmation
    \echo 'Schema ${SCHEMA_NAME} created and configured successfully'
EOSQL

echo "=== PostgreSQL initialization complete ==="
