#!/bin/bash

# MySQL Docker Backup Script
# Place this file in the same directory as your docker-compose.yml

set -e  # Exit on error

# Configuration
COMPOSE_SERVICE_NAME="pcma-db"  # Change this to match your service name in docker-compose.yml
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/mysql_backup_${TIMESTAMP}.sql"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Starting MySQL backup..."

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Get the container name using docker compose
CONTAINER_NAME=$(docker compose ps -q "$COMPOSE_SERVICE_NAME")

if [ -z "$CONTAINER_NAME" ]; then
    echo -e "${RED}Error: Container for service '$COMPOSE_SERVICE_NAME' not found or not running${NC}"
    exit 1
fi

echo "Found container: $CONTAINER_NAME"
echo "Backing up to: $BACKUP_FILE"

# Perform backup using docker compose exec (non-interactive)
# The password is passed via MYSQL_PWD environment variable
docker compose exec -T "$COMPOSE_SERVICE_NAME" \
    sh -c "MYSQL_PWD=\$MYSQL_ROOT_PASSWORD mysqldump -u root --all-databases" > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ] && [ -s "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ Backup completed successfully!${NC}"
    echo "  File: $BACKUP_FILE"
    echo "  Size: $BACKUP_SIZE"
    
    # Optional: Keep only last 10 backups
    echo "Cleaning old backups (keeping last 10)..."
    ls -t ${BACKUP_DIR}/mysql_backup_*.sql | tail -n +11 | xargs -r rm
    echo -e "${GREEN}✓ Cleanup completed${NC}"
else
    echo -e "${RED}✗ Backup failed!${NC}"
    rm -f "$BACKUP_FILE"  # Remove failed backup file
    exit 1
fi