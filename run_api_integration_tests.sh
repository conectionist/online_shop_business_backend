#!/bin/bash

# Set default values
REPORT_DIR="./test-reports/integration"
KEEP_CONTAINERS=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --keep-containers)
      KEEP_CONTAINERS=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Make sure the report directory exists
mkdir -p "$REPORT_DIR"

# Stop and remove any existing containers
echo "🧹 Cleaning up any existing test containers..."
docker-compose -f docker-compose.test.yml --env-file .env.test down -v --remove-orphans

# Build and start the test containers
echo "🏗️ Building test containers..."
docker-compose -f docker-compose.test.yml --env-file .env.test build

# Start the MySQL service
echo "🚀 Starting MySQL test environment..."
docker-compose -f docker-compose.test.yml --env-file .env.test up -d mysql_test

echo "⏳ Waiting for MySQL to be ready..."
# Display a countdown
TOTAL_WAIT=15
for (( i=$TOTAL_WAIT; i>=1; i-- ))
do
  echo -ne "\r⌛ MySQL starting... Should be ready in about $i seconds"
  sleep 1
done
echo -ne "\r✅ MySQL should be ready now!                         \n"

# Start the API service
echo "🚀 Starting API test environment..."
docker-compose -f docker-compose.test.yml --env-file .env.test up -d api_server_test

# Wait for API server to be ready
echo "⏳ Waiting for API server to be ready..."
sleep 2

# Run the tests
echo "🧪 Running API integration tests..."
docker-compose -f docker-compose.test.yml --env-file .env.test run --rm api_integration_tests
TEST_EXIT_CODE=$?

# Clean up containers unless --keep-containers is specified
if [ "$KEEP_CONTAINERS" = false ]; then
  echo "🧹 Cleaning up test containers..."
  docker-compose -f docker-compose.test.yml --env-file .env.test down -v
else
  echo "🔍 Containers kept running for inspection"
fi

# Show location of test reports
echo "📊 Test reports available in ${REPORT_DIR}"

# Show information about the JSON report
if [ -f "${REPORT_DIR}/integration_test_report.json" ]; then
  echo "📄 JSON test report generated: ${REPORT_DIR}/integration_test_report.json"
fi

# Exit with the test exit code
exit $TEST_EXIT_CODE
