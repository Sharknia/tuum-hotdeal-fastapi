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

    echo "Waiting for database at $DB_HOST:$DB_PORT (from DATABASE_URL)..."
    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 1
    done
    echo "Database $DB_HOST:$DB_PORT is ready."
}

# Wait for the database to be ready
wait_for_db

# Run database migrations
echo "Running database migrations..."
PYTHONPATH=/app alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@" 