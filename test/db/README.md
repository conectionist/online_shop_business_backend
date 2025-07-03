# Database Connection Testing Scripts

This directory contains scripts to test the SQLAlchemy database connection in an isolated Docker environment. These scripts help validate that the database connection is properly configured and working without installing dependencies on your development machine.

## Scripts Overview

We have three files that work together for database testing:

### 1. `docker_test_db_connection.py`

This is the main Python test script that runs inside the Docker container. It:
- Connects to the MySQL database using SQLAlchemy
- Runs test queries to verify connectivity
- Reports success or failure with detailed information

### 2. `Dockerfile.test`

This Dockerfile defines how to build the test container. It:
- Uses a Python base image
- Installs the required dependencies from requirements.txt
- Sets up the test script to run when the container starts

### 3. `test_db_docker.sh`

This shell script orchestrates the testing process. It:
- Ensures the MySQL database container is running
- Builds the test Docker image
- Runs the test container in the same network as the database
- Sets up the necessary environment variables
- Reports the test results

## Why Three Separate Files?

We use three separate files because each serves a specific purpose in our testing approach:

1. **Separation of Concerns**: 
   - `docker_test_db_connection.py` focuses on the actual testing logic
   - `Dockerfile.test` handles the container configuration
   - `test_db_docker.sh` manages the orchestration and environment setup

2. **Isolation**: Using Docker ensures we test in an environment similar to production without affecting the development machine.

3. **Reproducibility**: This approach ensures tests run consistently regardless of the developer's local setup.

## How to Use

### Testing the Database Connection

From the project root directory, run:

```bash
./test/db/test_db_docker.sh
```

This will:
1. Start the MySQL container if it's not already running
2. Build the test Docker image
3. Run the test and display the results

### Expected Output

On success, you should see output similar to:

```
🔍 Testing database connection with these settings:
  - Host: online_shop_mysql
  - Port: 3306
  - User: root
  - Password: ************
  - Database: online_shop

✅ Database connection successful!
   Result of test query: 1
✅ There are 6 units in the unitati table

✅ TEST PASSED: Database connection successful!
```

## Troubleshooting

If the test fails, check the following:

1. Ensure the MySQL container is running:
   ```bash
   docker ps | grep online_shop_mysql
   ```

2. Verify the environment variables in `.env` match the MySQL container configuration

3. Make sure the network settings allow the test container to connect to the MySQL container
