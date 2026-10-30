#!/bin/bash
set -e

echo "Starting Online Shop Business Backend..."

# Function to wait for database to be ready
wait_for_db() {
    echo "Waiting for database to be ready..."
    while ! python -c "
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='${DB_HOST}',
        port=${DB_PORT},
        user='${DB_USER}',
        password='${DB_PASSWORD}',
        database='${DB_NAME}'
    )
    conn.close()
    print('Database is ready!')
except Exception as e:
    print(f'Database not ready: {e}')
    exit(1)
"; do
        echo "Database not ready, waiting 5 seconds..."
        sleep 5
    done
}

# Function to initialize Alembic if not already initialized
init_alembic() {
    if [ ! -f "alembic.ini" ]; then
        echo "Initializing Alembic..."
        
        # Copy the pre-configured alembic.ini file
        cp alembic.ini.template alembic.ini
        
        # Update the database URL with environment variables
        sed -i "s|sqlalchemy.url = mysql+pymysql://user:pass@localhost/dbname|sqlalchemy.url = mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}|" alembic.ini
        
        echo "Alembic initialized successfully"
    else
        echo "Alembic already initialized"
    fi
}

# Function to configure Alembic environment
configure_alembic() {
    echo "Configuring Alembic environment..."
    
    # Always copy the template env.py file to ensure it's up to date
    cp migrations/env.py.template migrations/env.py
    
    echo "Alembic environment configured"
}

# Function to run migrations
run_migrations() {
    echo "Running database migrations..."
    
    # Always try to run migrations to head
    alembic upgrade head
    echo "Migrations completed successfully"
}

# Function to seed test data (only in test environment)
seed_test_data() {
    if [ "${ENVIRONMENT}" = "test" ]; then
        echo "Seeding test data..."
        if [ -f "test/test_data/seed_data_complete.sql" ]; then
            # Disable server certificate verification to avoid TLS errors in test environment
            # Also make inserts idempotent to avoid duplicate key errors on existing DBs
            sed -E 's/INSERT[[:space:]]+INTO/INSERT IGNORE INTO/I' test/test_data/seed_data_complete.sql \
              | mysql --ssl-verify-server-cert=OFF -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" || true
            echo "Test data seeding completed"
        else
            echo "No test seed file found; skipping"
        fi
    fi
}

# Main execution
echo "Environment: ${ENVIRONMENT:-development}"
echo "Database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Wait for database to be ready
wait_for_db

# Initialize Alembic if needed
init_alembic

# Configure Alembic environment
configure_alembic

# Run migrations
run_migrations

# Seed data in test environment
seed_test_data

# Configure proxy header handling for Uvicorn
# USE_PROXY_HEADERS controls whether we trust X-Forwarded-* headers at all.
# FORWARDED_ALLOW_IPS is the list of proxy IPs allowed to set those headers.
USE_PROXY_HEADERS="${USE_PROXY_HEADERS:-true}"
FORWARDED_ALLOW_IPS="${FORWARDED_ALLOW_IPS:-127.0.0.1}"

# Normalize USE_PROXY_HEADERS for comparison (true/1/yes are treated as enabled)
USE_PROXY_HEADERS_NORMALIZED=$(echo "${USE_PROXY_HEADERS}" | tr '[:upper:]' '[:lower:]')

if [ "${USE_PROXY_HEADERS_NORMALIZED}" = "true" ] || [ "${USE_PROXY_HEADERS_NORMALIZED}" = "1" ] || [ "${USE_PROXY_HEADERS_NORMALIZED}" = "yes" ]; then
    # An array, so a list with spaces or a "*" reaches Uvicorn as one argument.
    UVICORN_PROXY_FLAGS=(--proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS}")
    echo "Uvicorn proxy headers ENABLED; trusting X-Forwarded-* from: ${FORWARDED_ALLOW_IPS}"
else
    # Uvicorn trusts proxy headers from FORWARDED_ALLOW_IPS unless told not to.
    UVICORN_PROXY_FLAGS=(--no-proxy-headers)
    echo "Uvicorn proxy headers DISABLED; ignoring X-Forwarded-* headers"
fi

# Start the application
echo "Starting FastAPI application with 1 worker..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 "${UVICORN_PROXY_FLAGS[@]}" --log-config logging.ini
