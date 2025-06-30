#!/bin/bash
set -e

# Function to check if the database is already populated
check_db_populated() {
  local db_name="$1"
  # Using root user for initial checks as the regular user might not have sufficient privileges yet
  local table_count=$(mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "SELECT COUNT(TABLE_NAME) FROM information_schema.TABLES WHERE TABLE_SCHEMA = '$db_name';" --skip-column-names)
  
  if [ "$table_count" -gt 0 ]; then
    return 0 # True, database has tables
  else
    return 1 # False, database is empty
  fi
}

# Main script
echo "Checking if database $MYSQL_DATABASE is already populated..."

if check_db_populated "$MYSQL_DATABASE"; then
  echo "Database $MYSQL_DATABASE already contains tables. Skipping initialization."
else
  echo "Database $MYSQL_DATABASE is empty. Initializing with schema..."
  # Apply the schema - using root user for initial setup
  mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" < /docker-entrypoint-initdb.d/schema.sql
  echo "Schema initialized successfully!"
fi
