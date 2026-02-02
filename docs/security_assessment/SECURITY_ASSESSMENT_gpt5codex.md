## Security Assessment – Online Shop Business Backend

### Overview

This document captures the security posture of the FastAPI backend as of the current analysis. The goal is to determine whether the service is ready for public exposure and to highlight any gaps that require remediation before deployment to a cloud environment.

### Summary

- **High findings:** 4
- **Medium findings:** 5
- **Low findings / informational:** 2

### Findings by Severity

#### High

4. **Arbitrary file uploads** *(addressed)*
   - Product image uploads skip extension/MIME/size checks and read entire files into memory, permitting storage abuse and potential DoS.
   - Files referenced: `app/api/endpoints/product_images.py`, `app/core/image_processing.py`
   - **Remediation**: Extension, MIME (when present), and size are validated before processing (`is_valid_image` in product and category upload endpoints). Upload read is size-capped (`MAX_IMAGE_SIZE_MB`, default 15 MB). Image content is validated with PIL before save; invalid content returns 400.

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

4. Harden file uploads: enforce size caps, verify MIME/extension, stream to disk, and sanitize content.
5. Add login throttling and refresh-token revocation/rotation.
6. Disable OpenAPI docs and the `/db-test` endpoint in production deployments.
7. Add a `.dockerignore`, run containers as non-root, and pin dependency versions.
8. Review push notification payloads for sensitive information; guard the channel appropriately.

### Next Steps

1. Prioritize fixes for critical and high findings; retest once implemented.
2. Re-run the assessment focusing on authentication flows, file uploads, and deployment hardening.
3. After remediation, proceed with staged rollout (internal testing → limited beta → full public release).


