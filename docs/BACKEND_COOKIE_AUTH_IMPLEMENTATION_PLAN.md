# Backend: Cookie-Based Authentication Implementation Plan

This document describes **how** secure, cookie-based authentication is implemented on the backend and the expected behaviors for frontend integration.

It is backend‑only and assumes the frontend will be migrated according to `FRONTEND_COOKIE_AUTH_IMPLEMENTATION_PLAN.md`.

The goal is to end up with:

- Admin JWTs stored **only** in `HttpOnly` cookies for the API origin.
- Frontend never seeing or storing tokens (no `localStorage`, no `Authorization: Bearer`).
- A simple, robust flow that’s easy to maintain and extend later if needed.

---

## 1. Problem Statement

### 1.1 Current behavior (backend)

- `POST /auth/login`
  - Validates credentials.
  - Issues access + refresh JWTs.
  - Sets `access_token` and `refresh_token` as **httpOnly cookies**.
  - Returns admin info + `expires_in` (no tokens in body).

- `POST /auth/refresh`
  - Reads `refresh_token` from **cookies only**.
  - Rotates refresh token, revokes previous one, sets new cookies.
  - Returns minimal body (`expires_in`).

- Protected endpoints
  - Use `get_current_admin_from_cookie`, which reads the **access token cookie**.
  - If a `refresh_token` cookie is present, it enforces an active, non‑revoked, non‑expired session that matches the access token.
  - If no refresh cookie exists (legacy/non‑browser clients), it falls back to access‑token‑only validation.

- Sessions and revocation
  - Refresh tokens are stored server‑side (hashed) with metadata.
  - Revocation is supported per session and per admin (logout‑all / change‑password).
  - Session management endpoints are available under `/auth/sessions*`.

### 1.2 Requirements recap

From our cookie-based auth requirements and the frontend migration plan:

- Tokens must be sent and stored **only via httpOnly cookies**, not in JSON bodies for client storage.
- The browser must send cookies automatically on credentialed requests (`withCredentials` / `credentials: 'include'`).
- The backend must:
  - Set cookies on **login** and **refresh**.
  - Read tokens from cookies for **authenticated requests**.
  - Provide a **logout** endpoint that clears cookies.
  - Provide a **session/me**‑style endpoint so the frontend can restore logged‑in state on app load.
  - Support proper **CORS with credentials** for the SPA origin.

We do **not** require `Authorization: Bearer` for browser clients. A limited access‑token‑only fallback exists for legacy/non‑browser use.

---

## 2. Current Design (Backend Auth Model)

### 2.1 High‑level flow

- **Login (`POST /auth/login`):**
  - Input: username + password (as today).
  - On success:
    - Issue **access** and **refresh** JWTs using existing helpers.
    - Set two cookies on the response:
      - `access_token` – short‑lived; used for API authorization.
      - `refresh_token` – longer‑lived; used only for refreshing access tokens.
    - Return admin info in JSON (no tokens in body).

- **Authenticated requests:**
  - Protected endpoints read the `access_token` **from cookies**, validate it, and return 401 on invalid/missing/expired token.
  - They no longer require `Authorization: Bearer` for the SPA.
  - If a `refresh_token` cookie is present, the access token must map to a valid, active session (non‑revoked, non‑expired).

- **Refresh (`POST /auth/refresh`):**
  - Reads the `refresh_token` from cookies only.
  - If valid, issues a new `access_token` **and rotates the refresh token**.
  - Updates the cookies via `Set-Cookie`.
  - Response body is empty or minimal, without tokens.

- **Session check (`GET /auth/me`):**
  - Reads `access_token` from cookie, validates it, and returns current admin info.
  - Returns 401 if not authenticated.

- **Logout (`POST /auth/logout`):**
  - Called with credentials (cookies).
  - Clears both `access_token` and `refresh_token` cookies.
  - Revokes the current refresh token server‑side if present.

- **Logout all (`POST /auth/logout-all`):**
  - Revokes all refresh tokens for the admin.
  - Clears auth cookies.

- **Session management:**
  - `GET /auth/sessions` lists active sessions.
  - `GET /auth/sessions/current` returns the current session (based on refresh token).
  - `GET /auth/sessions/{id}` returns a specific session.
  - `DELETE /auth/sessions/{id}` revokes another session.

### 2.2 Cookie attributes

For both `access_token` and `refresh_token` cookies:

- `HttpOnly`: **required** (prevents JS from reading tokens).
- `Secure`: enabled in production (HTTPS only); may be disabled in local dev if needed.
- `SameSite`: `Lax` or `Strict` (sufficient for admin SPA use case; prevents most CSRF).
- `Path`: `/` or the API prefix (e.g. `/api`), so the cookie is sent on all API routes.
- `Domain`: API host only (e.g. `api.example.com`) or omitted to default to the host.
- `Max-Age` / `Expires`:
  - Access cookie lifetime ~= access token expiration.
  - Refresh cookie lifetime ~= refresh token expiration (longer).

These requirements can be summarized as:

| Attribute   | Requirement |
|------------|-------------|
| **HttpOnly** | Set so that JavaScript cannot read the cookie (prevents XSS from stealing the token). |
| **Secure**   | Set in production (HTTPS only). In local development over HTTP, you may omit it if your stack allows; in production it must be set. |
| **SameSite** | Set to `Strict` or `Lax`. `Strict` is more secure; `Lax` allows cookies to be sent on top-level navigations from external sites (e.g. link from email). Choose based on your UX (e.g. links to the SPA that then call the API). |
| **Path**     | Typically `/` or the API path prefix (e.g. `/api`) so the cookie is sent on all (or all API) requests to the same host. |
| **Domain**   | Omit (same host only) or set to the API host (e.g. `api.example.com`) so the cookie is not sent to other domains. For cross-origin SPA, the cookie is for the API origin; the browser will send it only to that origin. |
| **Max-Age or Expires** | Set so the refresh cookie expires at the desired session length; the access-token cookie can have a shorter lifetime matching the access token. |

Example (conceptual):

`Set-Cookie: access_token=<value>; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=900`  
`Set-Cookie: refresh_token=<value>; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=2592000`

### 2.3 CORS and credentials

For all auth‑related and authenticated routes:

- Responses must include:
  - `Access-Control-Allow-Origin: <frontend-origin>` (no `*`).
  - `Access-Control-Allow-Credentials: true`.
  - Appropriate `Access-Control-Allow-Methods` and `Access-Control-Allow-Headers` for preflight.
- The frontend will send requests with credentials (`withCredentials: true` / `credentials: 'include'`), causing the browser to:
  - Attach auth cookies on requests to the API origin.
  - Accept `Set-Cookie` headers from the API.

---

## 3. Detailed Changes by Area

### 3.1 Auth endpoints (`app/api/endpoints/auth.py`)

**Current (implemented):**

1. **`POST /auth/login`**
   - Sets `access_token` + `refresh_token` cookies.
   - Stores refresh token server‑side (hashed) with session metadata.
   - Returns admin info and `expires_in` (no tokens in body).

2. **`POST /auth/refresh`**
   - Reads `refresh_token` from cookies.
   - Rotates refresh token and revokes the previous one.
   - Sets new cookies and returns `expires_in`.

3. **`GET /auth/me`**
   - Uses cookie‑based auth to return current admin info.
   - Returns 401 if unauthenticated.

4. **`POST /auth/logout`**
   - Revokes the current refresh token (if present) and clears cookies.

5. **`POST /auth/logout-all`**
   - Revokes all refresh tokens for the admin and clears cookies.

6. **Session management**
   - `GET /auth/sessions`
   - `GET /auth/sessions/current`
   - `GET /auth/sessions/{id}`
   - `DELETE /auth/sessions/{id}`

### 3.2 Schemas (`app/schemas/auth.py`)

**Current (implemented):**

1. **`LoginResponse`**
   - Contains `admin` and `expires_in` only.
   - No tokens in the body.

2. **`TokenRefreshRequest`**
   - Empty body (schema exists only for OpenAPI clarity).

3. **`TokenRefreshResponse`**
   - Contains `expires_in` only.

### 3.3 Auth service / dependencies (`app/services/auth.py`)

**Current (implemented):**

- `get_current_admin_from_cookie`:
  - Reads `access_token` from `request.cookies`.
  - Validates token and ensures type is `"access"`.
  - If a `refresh_token` cookie is present:
    - Ensures a matching active session exists (not revoked/expired).
  - If no refresh cookie exists:
    - Falls back to access‑token‑only validation (for legacy/non‑browser clients).

- `refresh_access_token`:
  - Accepts a refresh token string (from cookies).
  - Verifies token type (`"refresh"`), checks expiry, then issues a new access token.
  - Supports refresh token rotation + revocation in the calling flow.

### 3.4 CORS / configuration (`app/core/config.py` and related)

**Requirements:**

- Ensure all routes that:
  - Set cookies (login, refresh, logout), or
  - Expect cookies (all authenticated endpoints)
  send:
  - `Access-Control-Allow-Origin: <frontend-origin>`
  - `Access-Control-Allow-Credentials: true`

- Confirm:
  - Your global CORS middleware / configuration includes the correct frontend origin(s).
  - Preflight requests (`OPTIONS`) for auth endpoints are handled correctly (methods + headers).

If the CORS setup is currently centralized (e.g. via FastAPI’s `CORSMiddleware`), adjust it there rather than per‑route.

---

## 4. Roadmap & Implementation Steps

This is a suggested sequence to implement and validate the new auth model with minimal risk.

### Step 1 – Add cookie helpers and constants (Completed)

- Define:
  - Cookie names: e.g. `ACCESS_TOKEN_COOKIE_NAME = "access_token"`, `REFRESH_TOKEN_COOKIE_NAME = "refresh_token"`.
  - Common cookie options based on environment:
    - `secure = not settings.DEBUG` (or equivalent).
    - `samesite = "strict"` or `"lax"`.
    - `path`, `domain`.
    - `max_age` for access and refresh.
- Optionally centralize cookie setting/clearing in small utility functions to avoid duplication.

### Step 2 – Implement cookie‑setting in `POST /auth/login` (Completed)

- Modify `login` endpoint to:
  - After `create_admin_tokens`, set both cookies on the response.
  - Change the response body to return only admin info (update `LoginResponse` accordingly).
- Update / add tests to:
  - Assert `Set-Cookie` headers are present with correct attributes.
  - Assert response JSON no longer includes tokens.

### Step 3 – Implement cookie‑based `POST /auth/refresh` (Completed)

- Modify `refresh_token` endpoint to:
  - Read `refresh_token` from `request.cookies`.
  - Return 401 if cookie is missing or invalid.
  - Call `refresh_access_token` with the cookie value.
  - Set new `access_token` cookie (and optionally rotate `refresh_token`) on success.
  - Adjust response schema to no longer expose tokens.
- Update tests to:
  - Simulate presence of refresh cookie.
  - Assert new cookies are set.
  - Assert correct 401 behavior when cookie is invalid/missing.

### Step 4 – Add `GET /auth/me` (Completed)

- Implement a simple endpoint that:
  - Uses the cookie‑based auth dependency.
  - Returns admin info if authenticated.
  - Returns 401 if not.
- Tests:
  - With valid `access_token` cookie: returns 200 and correct admin.
  - Without cookie or with invalid/expired token: returns 401.

### Step 5 – Add `POST /auth/logout` (Completed)

- Implement endpoint that:
  - Sends `Set-Cookie` clear instructions for `access_token` and `refresh_token`.
- Tests:
  - With cookies set: response clears both cookies (check `Set-Cookie`).
  - Idempotent behavior: calling logout when already "logged out" is safe.

### Step 6 – Switch protected endpoints to cookie-based auth (Completed)

- Migrate all admin-protected endpoints from `get_current_admin` to `get_current_admin_from_cookie`.
- Update test utilities to use cookies instead of Authorization headers.
- Keep public endpoints (e.g., payment types) without authentication requirements.
- Tests:
  - All 332 integration tests pass with cookie-based authentication.
  - Authentication flow works: login → protected endpoints → logout.
  - Public endpoints remain accessible without authentication.

### Step 7 – CORS and environment validation (Completed)

- Confirm:
  - ✅ CORS is configured with the correct frontend origin and `allow_credentials=True`.
  - ✅ In development:
    - Cookies are visible in browser DevTools under the API origin.
    - Login sets cookies correctly; authenticated calls send cookies; refresh and logout behave as expected.
  - ✅ In testing:
    - All 332 integration tests pass with cookie-based authentication.
    - CORS validation script confirms proper cookie behavior.
  - ✅ Production-ready configuration:
    - `Secure` flag automatically enabled in production environment.
    - Origins configured via environment variables for flexibility.

### Step 8 – Cleanup ✅ COMPLETED

#### 8.1 Legacy Code Cleanup ✅ COMPLETED
**Objective**: Remove all header-based authentication code that is no longer needed

**Completed Tasks**:
- ✅ **Removed `get_current_admin()` function**: Deleted legacy header-based authentication function from `app/services/auth.py`
- ✅ **Deleted `app/core/dependencies.py`**: Removed entire file containing `CustomHTTPBearer` and `custom_security` 
- ✅ **Cleaned imports**: Removed `HTTPAuthorizationCredentials`, `custom_security` imports from auth service
- ✅ **Updated service exports**: Removed `get_current_admin` from `app/services/__init__.py`
- ✅ **Removed commented code**: Deleted commented-out admin creation endpoint that used legacy auth
- ✅ **Fixed missing imports**: Added `verify_password` and `get_password_hash` imports to resolve errors

**Validation**: All 332 integration tests pass, confirming no functionality was broken

#### 8.2 Testing and Validation (Completed)
**Goal**: Ensure cleanup does not break existing functionality

**Tasks**:
1. **Regression Testing** ✅ COMPLETED
   - ✅ Run full integration test suite (332 tests) - PASSED
   - ✅ Verify all authentication flows still work - CONFIRMED
   - ✅ Test error handling for removed functionality - CONFIRMED


### Step 9 – Hardening (Partially Completed)

#### 9.1 Security Hardening Implementation (Partially Completed)
**Overview**: Three distinct security features to enhance cookie-based authentication system

##### 9.1.1 CSRF Protection Enhancement ✅ COMPLETED
**Current Protection**: SameSite=lax cookies provide basic CSRF protection

**Implementation**: ✅ Documented current protection as adequate
- ✅ Created comprehensive security documentation at `/docs/SECURITY_ENHANCEMENTS.md`
- ✅ Analyzed current security measures and future enhancement options
- ✅ Provided implementation details and risk assessment
- ✅ Documented testing strategies and recommendations

##### 9.1.2 Token Revocation Support ✅ COMPLETED
**Implementation**: ✅ Database-backed refresh token storage + revocation

**Completed Capabilities**:
- **Database Storage**: Refresh tokens are stored server-side as SHA-256 hashes with `admin_id`, `expires_at`, `revoked_at`, `ip_address`, `user_agent`.
- **Refresh Rotation**: `POST /auth/refresh` rotates the refresh token and revokes the previous one.
- **Device-Specific Logout**: `POST /auth/logout` clears cookies and revokes the current refresh token.
- **Global Token Revocation**: `POST /auth/logout-all` and `POST /auth/change-password` revoke all refresh tokens for the admin and clear cookies.

##### 9.1.3 Enhanced Session Management ✅ COMPLETED
**Current Behavior**: Database-backed refresh tokens with session metadata

**Completed Capabilities**:
- **Session Tracking**: Active sessions stored with device/user-agent/IP metadata.
- **Session Management**: Endpoints to list, view current, fetch by ID, and revoke sessions.
- **Automatic Cleanup**: Expired sessions are filtered from active views; optional cleanup utilities exist.

##### 9.1.4 Security Headers Documentation 📝
**Current Status**: ✅ DOCUMENTED
- **Current Headers**: Appropriate cache controls for auth endpoints
- **Future Enhancements**: Document additional security headers (CSP, HSTS, etc.)

#### 9.2 Testing and Validation (In Progress)
**Goal**: Ensure security hardening improvements work correctly and do not break existing functionality

**Tasks**:
1. **Security Testing** (Pending)
   - Test device-specific logout functionality
   - Test global logout ("Logout All Devices") 
   - Test session tracking accuracy
   - Verify token revocation effectiveness

2. **Performance Testing** (Pending)
   - Measure impact of additional security checks
   - Verify database performance with token storage
   - Test session management overhead

---

## 5. Checklist

The implementation should satisfy the following checklist:

- [x] **Login:** On successful auth, set httpOnly (and Secure, SameSite) cookies for access and refresh tokens; return admin info in the body; do not require the client to send tokens back in body/header for normal requests.
- [x] **Refresh:** Read the refresh token from the cookie only; issue new token(s) and set/overwrite cookies; do not require `refresh_token` in the body.
- [x] **Authenticated requests:** Read the access token from the cookie; return 401 when missing or invalid; do not require `Authorization: Bearer` for the SPA.
- [x] **Logout:** Provide an endpoint that clears the auth cookies via `Set-Cookie` and revokes refresh tokens server-side.
- [x] **CORS:** Allow the frontend origin with credentials (`Access-Control-Allow-Origin: <origin>`, `Access-Control-Allow-Credentials: true`) on all auth-related and authenticated endpoints.
- [x] **Cookie attributes:** Use HttpOnly, Secure (in prod), SameSite (Strict or Lax), appropriate Path and expiration for both access and refresh cookies.

---

## 6. Summary

By following this plan, the backend will:

- Move from **header/body JWT transport** to **cookie‑only JWT transport**.
- Eliminate frontend storage of sensitive tokens while reusing existing JWT creation/verification logic.
- Provide a clean, future‑proof API surface for:
  - Login (`/auth/login`),
  - Refresh (`/auth/refresh`),
  - Session check (`/auth/me`),
  - Logout (`/auth/logout`) and logout‑all (`/auth/logout-all`),
  - Session management (`/auth/sessions*`),
  - And all protected admin operations using cookie‑based auth.

This enables the frontend to migrate away from `localStorage` entirely and rely on secure, httpOnly cookies for admin authentication.
