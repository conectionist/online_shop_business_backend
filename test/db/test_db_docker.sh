#!/bin/bash

set -e  # Exit on error

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Make sure the database container is running
echo "🔍 Checking if database container is running..."
if ! docker ps | grep -q online_shop_mysql; then
  echo "⚠️  Database container not running. Starting it..."
  docker-compose up -d db
  
  echo "⏳ Waiting for MySQL to be ready..."
  # Display a countdown
  TOTAL_WAIT=15
  for (( i=$TOTAL_WAIT; i>=1; i-- ))
  do
    echo -ne "\r⌛ MySQL starting... $i seconds remaining "
    sleep 1
  done
  echo -ne "\r✅ MySQL should be ready now!             \n"
else
  echo "✅ Database container is already running"
fi

# Step 2: Get the database container's network
NETWORK=$(docker inspect online_shop_mysql --format '{{range $net,$v := .NetworkSettings.Networks}}{{$net}}{{end}}')
echo "🌐 Database is running on network: $NETWORK"

# Step 3: Build the test image
echo "🏗️  Building test image..."
docker build -t db-connection-test -f test/db/Dockerfile.test .

# Step 4: Run the test container with the necessary environment variables
echo "🧪 Running database connection test..."
docker run --rm \
  --network="$NETWORK" \
  -e DB_HOST=online_shop_mysql \
  -e DB_PORT=3306 \
  -e DB_USER=root \
  -e DB_PASSWORD="$(grep MYSQL_ROOT_PASSWORD .env | cut -d= -f2)" \
  -e DB_NAME=online_shop \
  db-connection-test

# Check the exit code
if [ $? -eq 0 ]; then
  echo "\n🎉 Database connection test successful!"
else
  echo "\n❌ Database connection test failed!"
  exit 1
fi
