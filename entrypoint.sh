#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to check if database is ready
wait_for_db() {
    # Default values if DATABASE_URL is not set
    local db_uri=${DATABASE_URL:-postgresql://db:5432/default_db}

    # Extract host and port from DATABASE_URL
    local db_conn_info=$(echo $db_uri | sed -e 's%^[^:]*://%%')
    db_conn_info=$(echo $db_conn_info | sed -e 's%^[^@]*@%%')
    local db_host=$(echo $db_conn_info | sed -e 's%:[^:]*$%%' -e 's%/.*$%%')
    local db_port=$(echo $db_conn_info | sed -e 's%^.*:%%' -e 's%/.*$%%')

    # Use defaults if extraction fails (e.g., URL format is unexpected)
    DB_HOST=${db_host:-db}
    DB_PORT=${db_port:-5432}

    DB_WAIT_TIMEOUT=${DB_WAIT_TIMEOUT:-180}
    elapsed=0

    echo "Waiting for database at $DB_HOST:$DB_PORT (from DATABASE_URL, timeout=${DB_WAIT_TIMEOUT}s)..."
    while ! nc -z $DB_HOST $DB_PORT; do
        if [ "$elapsed" -ge "$DB_WAIT_TIMEOUT" ]; then
            echo "Database wait timeout after ${DB_WAIT_TIMEOUT}s: $DB_HOST:$DB_PORT"
            exit 1
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    echo "Database $DB_HOST:$DB_PORT is ready."
}

# Wait for the database to be ready
wait_for_db

if [ "${RUN_DB_MIGRATIONS:-0}" = "1" ]; then
    echo "Running database migrations..."
    PYTHONPATH=/app alembic upgrade head
else
    echo "Skipping database migrations (RUN_DB_MIGRATIONS=${RUN_DB_MIGRATIONS:-0})"
fi

# Start the application
echo "Starting application..."
exec "$@" 
