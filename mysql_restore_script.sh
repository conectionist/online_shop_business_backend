#!/bin/bash

# MySQL Docker Restore Script
# Place this file in the same directory as your docker-compose.yml

set -e  # Exit on error

# Configuration
COMPOSE_SERVICE_NAME="db"  # Change this to match your service name in docker-compose.yml
BACKUP_DIR="./backups"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Usage: $0 [backup_file]"
    echo ""
    echo "Options:"
    echo "  backup_file    Path to the backup file to restore"
    echo "                 If not provided, will list available backups"
    echo ""
    echo "Examples:"
    echo "  $0 ./backups/mysql_backup_20250101_120000.sql"
    echo "  $0  # Will show list of available backups"
    exit 1
}

# Function to list available backups
list_backups() {
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR/*.sql 2>/dev/null)" ]; then
        echo -e "${RED}No backup files found in $BACKUP_DIR${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Available backup files:${NC}"
    echo ""
    local count=1
    local backups=()
    for backup in $(ls -t ${BACKUP_DIR}/mysql_backup_*.sql 2>/dev/null); do
        local size=$(du -h "$backup" | cut -f1)
        local date=$(stat -c %y "$backup" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
        printf "  %2d. %s\n" "$count" "$(basename $backup)"
        printf "      Size: %s, Date: %s\n" "$size" "$date"
        backups+=("$backup")
        ((count++))
    done
    echo ""
    echo -n "Enter the number of the backup to restore (or 'q' to quit): "
    read selection
    
    if [ "$selection" = "q" ] || [ "$selection" = "Q" ]; then
        echo "Restore cancelled."
        exit 0
    fi
    
    if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -gt "${#backups[@]}" ]; then
        echo -e "${RED}Invalid selection${NC}"
        exit 1
    fi
    
    RESTORE_FILE="${backups[$((selection-1))]}"
}

# Determine which backup file to use
if [ $# -eq 0 ]; then
    # No argument provided, list available backups
    list_backups
elif [ $# -eq 1 ]; then
    # Backup file provided as argument
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        usage
    fi
    
    RESTORE_FILE="$1"
    
    # If relative path, check if it's in BACKUP_DIR
    if [[ ! "$RESTORE_FILE" = /* ]]; then
        # Not an absolute path
        if [[ ! "$RESTORE_FILE" = ./* ]] && [[ ! "$RESTORE_FILE" = ../* ]]; then
            # Assume it's in BACKUP_DIR
            RESTORE_FILE="${BACKUP_DIR}/${RESTORE_FILE}"
        fi
    fi
else
    usage
fi

# Check if backup file exists
if [ ! -f "$RESTORE_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $RESTORE_FILE${NC}"
    exit 1
fi

# Check if backup file is not empty
if [ ! -s "$RESTORE_FILE" ]; then
    echo -e "${RED}Error: Backup file is empty: $RESTORE_FILE${NC}"
    exit 1
fi

echo "Starting MySQL restore..."
echo "Backup file: $RESTORE_FILE"
echo ""

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
echo ""

# Warning and confirmation
echo -e "${YELLOW}WARNING: This will replace all data in the database!${NC}"
echo -e "${YELLOW}Make sure you have a current backup before proceeding.${NC}"
echo ""
echo -n "Are you sure you want to continue? (yes/no): "
read confirmation

if [ "$confirmation" != "yes" ] && [ "$confirmation" != "YES" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "Restoring database..."

# Drop and recreate the schema to ensure a clean slate before restoring.
# This removes any tables that exist in the DB but were not in the backup.
docker compose exec -T "$COMPOSE_SERVICE_NAME" \
    sh -c "MYSQL_PWD=\$MYSQL_ROOT_PASSWORD mysql -u root -e \"DROP DATABASE IF EXISTS \$MYSQL_DATABASE; CREATE DATABASE \$MYSQL_DATABASE;\""

# Perform restore using docker compose exec
# The password is passed via MYSQL_PWD environment variable
docker compose exec -T "$COMPOSE_SERVICE_NAME" \
    sh -c "MYSQL_PWD=\$MYSQL_ROOT_PASSWORD mysql -u root $MYSQL_DATABASE" < "$RESTORE_FILE"

# Check if restore was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Restore completed successfully!${NC}"
    echo "  Restored from: $RESTORE_FILE"
else
    echo -e "${RED}✗ Restore failed!${NC}"
    exit 1
fi
