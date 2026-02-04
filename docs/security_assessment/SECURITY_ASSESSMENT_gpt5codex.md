## Security Assessment – Online Shop Business Backend

### Overview

This document captures the security posture of the FastAPI backend as of the current analysis. The goal is to determine whether the service is ready for public exposure and to highlight any gaps that require remediation before deployment to a cloud environment.

### Summary

- **Medium findings:** 3

### Findings by Severity

#### Medium

2. **Docker image hardening gaps** – container runs as root, copies entire context, and lacks a `.dockerignore`.
3. **Refresh tokens are non-revocable** – no allow/deny list or rotation.

### Recommended Remediation Steps

2. Add a `.dockerignore`, run containers as non-root, and pin dependency versions.

