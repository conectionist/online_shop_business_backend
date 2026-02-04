## Security Assessment – Online Shop Business Backend

### Overview

This document captures the security posture of the FastAPI backend as of the current analysis. The goal is to determine whether the service is ready for public exposure and to highlight any gaps that require remediation before deployment to a cloud environment.

### Summary

- **Medium findings:** 5
- **Low findings / informational:** 2

### Findings by Severity

#### Medium

1. **No brute-force protection on admin login** (`/auth/login`).
2. **Refresh tokens are non-revocable** – no allow/deny list or rotation.
3. **OpenAPI docs enabled by default** – must be disabled explicitly in production.
4. **Public exposure of uploaded files** at `/api/v1/static/uploads` without validation hardening.
5. **Docker image hardening gaps** – container runs as root, copies entire context, and lacks a `.dockerignore`.

#### Low / Informational

1. **`/db-test` endpoint leaks table counts** to unauthenticated users.
2. **Admin login notifications** include usernames; ensure push infrastructure is trusted.

### Recommended Remediation Steps

6. Disable OpenAPI docs and the `/db-test` endpoint in production deployments.
7. Add a `.dockerignore`, run containers as non-root, and pin dependency versions.
8. Review push notification payloads for sensitive information; guard the channel appropriately.
