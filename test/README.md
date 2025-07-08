# API Testing Pipeline

This directory contains test data and configurations for automated API testing using Schemathesis.

## Overview

The testing pipeline uses Schemathesis to perform property-based testing of the API endpoints defined in the OpenAPI schema. The test environment runs in Docker containers to ensure consistency and isolation.

## Test Structure

- `test_data/`: Contains test fixtures and seed data for the test database
- `test_data/seed_data.sql`: SQL scripts to populate the test database with test data

## Running Tests

To run the API tests, use the provided script:

```bash
./run_api_contract_tests.sh
```

### Options

- `--keep-containers`: Keep containers running after tests for debugging
- `--test-pattern=<pattern>`: Run specific tests matching the pattern

Example:
```bash
./run_api_contract_tests.sh --keep-containers --test-pattern="GET /api/products*"
```

## Test Reports

After running tests, reports will be available in the `test_reports` directory:

- `api_test_report.html`: HTML report with detailed test results
- `report.xml`: JUnit XML report for CI integration

## CI/CD Integration

The testing pipeline is integrated with GitHub Actions. Tests run automatically on:
- Every push to `master` or `develop` branches
- Every pull request targeting `master` or `develop` branches

Test artifacts are uploaded to GitHub Actions for review.
