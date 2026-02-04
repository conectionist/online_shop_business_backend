## Security Assessment – Online Shop Business Backend

### Overview

This document captures the security posture of the FastAPI backend as of the current analysis. The goal is to determine whether the service is ready for public exposure and to highlight any gaps that require remediation before deployment to a cloud environment.

### Findings by Severity

#### Medium

3. **Refresh tokens are non-revocable** – no allow/deny list or rotation.

