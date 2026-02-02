# Debugging Setup Guide

This guide explains how to set up and use step-by-step debugging with breakpoints for the FastAPI application.

## Overview

The debugging setup uses `debugpy` to enable remote debugging of the FastAPI application running in Docker. When `DEBUG=1`, the application will start a debug server on port 5678 that allows you to connect with your IDE's debugger.

## Prerequisites

- VS Code with Python extension
- Docker and Docker Compose installed
- The application code cloned locally

## Quick Start

1. **Start the debug environment:**
   ```bash
   ./start_debug.sh
   ```

2. **Connect your debugger in VS Code:**
   - Open VS Code
   - Go to Run and Debug (Ctrl+Shift+D)
   - Select "Debug FastAPI (Docker)" from the dropdown
   - Click the play button or press F5

3. **Set breakpoints:**
   - Open any Python file in the `app/` directory
   - Click in the left margin next to line numbers to set breakpoints
   - Make API requests to trigger the breakpoints

## Manual Setup

If you prefer to start the debug environment manually:

```bash
# Build and start the debug environment
docker compose -f docker-compose.debug.yml build
docker compose -f docker-compose.debug.yml up -d

# View logs
docker compose -f docker-compose.debug.yml logs -f api_debug

# Stop the debug environment
docker compose -f docker-compose.debug.yml down
```

## Configuration Details

### Environment Variables

- `DEBUG=1`: Enables debugpy and starts the debug server
- `ENVIRONMENT=development`: Sets the environment to development mode
- `USE_PROXY_HEADERS`: When `true` (default), Uvicorn will trust `X-Forwarded-*` headers from configured proxy IPs.
- `FORWARDED_ALLOW_IPS`: Comma-separated list of proxy IPs allowed to set `X-Forwarded-*` headers (defaults to `127.0.0.1`).
- `ALLOWED_HOSTS`: Comma-separated host list for TrustedHostMiddleware. In production this must be set to explicit host(s), not `*`, for host-header protection.

### Service Names

- `api_debug`: API service (different from production `api` and test `api_server_test`)
- `db_debug`: Database service (different from production `db` and test `mysql_test`)
- `debug_frontend` and `debug_backend`: Isolated networks

### Ports

- `8002`: FastAPI application (different from production 8000 and test 8001)
- `5678`: debugpy debug server
- `3307`: MySQL database (different from production 3306)

### Volumes

The debug configuration mounts the `./app` directory to `/app/app` in the container, allowing for live code changes without rebuilding the container.

## VS Code Configuration

The `.vscode/launch.json` file contains the debug configuration:

```json
{
    "name": "Debug FastAPI (Docker)",
    "type": "python",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": 5678
    },
    "pathMappings": [
        {
            "localRoot": "${workspaceFolder}",
            "remoteRoot": "/app"
        }
    ],
    "justMyCode": false
}
```

### Path Mappings

The `pathMappings` configuration maps your local workspace to the `/app` directory in the container, ensuring that breakpoints work correctly.

## Debugging Features

### Breakpoints

- Set breakpoints in any Python file in the `app/` directory
- Breakpoints will be hit when the corresponding code is executed
- You can inspect variables, step through code, and evaluate expressions

### Hot Reload

Since the `app/` directory is mounted as a volume, you can make code changes and they will be reflected immediately without rebuilding the container.

### Debug Console

Use the VS Code debug console to evaluate expressions and inspect variables during debugging sessions.

## Troubleshooting

### Debugger Won't Connect

1. Ensure the debug environment is running:
   ```bash
   docker compose -f docker-compose.debug.yml ps
   ```

2. Check if debugpy is listening:
   ```bash
   docker compose -f docker-compose.debug.yml logs api_debug | grep debugpy
   ```

3. Verify port 5678 is accessible:
   ```bash
   netstat -an | grep 5678
   ```

### Breakpoints Not Hit

1. Ensure you're setting breakpoints in files within the `app/` directory
2. Check that the path mappings in `.vscode/launch.json` are correct
3. Verify that the code path you're testing actually executes the code with breakpoints

### Code Changes Not Reflected

1. Ensure the `app/` directory is properly mounted as a volume
2. Check that you're editing files in the correct location
3. Restart the container if necessary:
   ```bash
   docker compose -f docker-compose.debug.yml restart api_debug
   ```

## Alternative IDEs

### PyCharm

To use PyCharm for debugging:

1. Go to Run → Edit Configurations
2. Add a new Python Debug Server configuration
3. Set the host to `localhost` and port to `5678`
4. Configure path mappings: local path → `/app`

### Other IDEs

Most Python IDEs support remote debugging via debugpy. Refer to your IDE's documentation for specific configuration instructions.

## Security Notes

- The debug configuration is for development only
- Never use `DEBUG=1` in production
- The debugpy server listens on all interfaces (`0.0.0.0:5678`) - ensure your firewall is configured appropriately
- Consider using `debugpy.wait_for_client()` if you want the application to wait for a debugger to attach before starting
