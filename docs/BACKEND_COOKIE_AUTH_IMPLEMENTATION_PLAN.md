# Backend: Cookie-Based Authentication Implementation Plan

This document describes **how** to implement secure, cookie-based authentication on the backend, starting from the current JWT‑over‑`Authorization`‑header design.

It is backend‑only and assumes the frontend will be migrated according to `FRONTEND_COOKIE_AUTH_MIGRATION_GUIDE.md`.

The goal is to end up with:

- Admin JWTs stored **only** in `HttpOnly` cookies for the API origin.
- Frontend never seeing or storing tokens (no `localStorage`, no `Authorization: Bearer`).
- A simple, robust flow that’s easy to maintain and extend later if needed.

---

## 1. Problem Statement

### 1.1 Current behavior (backend + frontend)

- `POST /auth/login`
  - Validates credentials.
  - Returns `access_token` and `refresh_token` in JSON.
  - The frontend stores these in `localStorage` and sends `Authorization: Bearer <access_token>` on every request.

- `POST /auth/refresh`
  - Accepts a `refresh_token` in the **request body**.
  - Returns a new `access_token` in JSON.

- Protected endpoints
  - Depend on `get_current_admin`, which reads the JWT from the **Authorization header** (via `custom_security` / `HTTPBearer`).

**Issues:**

- Tokens are readable by JavaScript (frontend) and stored in `localStorage`, which is vulnerable to XSS‑driven token theft.
- The backend requires explicit `Authorization` headers and `refresh_token` bodies, tying the API contract to the current frontend implementation.
- There is no cookie‑based flow yet; frontend cannot migrate away from `localStorage` safely.

### 1.2 Requirements recap

From our cookie-based auth requirements and the frontend migration guide:

- Tokens must be sent and stored **only via httpOnly cookies**, not in JSON bodies for client storage.
- The browser must send cookies automatically on credentialed requests (`withCredentials` / `credentials: 'include'`).
- The backend must:
  - Set cookies on **login** and **refresh**.
  - Read tokens from cookies for **authenticated requests**.
  - Provide a **logout** endpoint that clears cookies.
  - Provide a **session/me**‑style endpoint so the frontend can restore logged‑in state on app load.
  - Support proper **CORS with credentials** for the SPA origin.

We do **not** need backward compatibility with the current header/body‑token scheme. We can move directly to the new model.

---

## 2. Target Design (Backend Auth Model)

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

- **Refresh (`POST /auth/refresh`):**
  - Reads the `refresh_token` from cookies only.
  - If valid, issues a new `access_token` (and optionally a new `refresh_token`).
  - Updates the cookies via `Set-Cookie`.
  - Response body is empty or minimal, without tokens.

- **Session check (`GET /auth/me`):**
  - Reads `access_token` from cookie, validates it, and returns current admin info.
  - Returns 401 if not authenticated.

- **Logout (`POST /auth/logout`):**
  - Called with credentials (cookies).
  - Clears both `access_token` and `refresh_token` cookies.
  - Optionally invalidates refresh tokens server‑side if we later introduce token storage.

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

**Current:**

- `POST /auth/login`:
  - Returns `LoginResponse` with `access_token`, `refresh_token`, `token_type`, `expires_in`, `admin`.
  - No cookies are set.

- `POST /auth/refresh`:
  - Accepts `TokenRefreshRequest` with `refresh_token` in the body.
  - Returns `TokenRefreshResponse` with a new `access_token`.

**Target:**

1. **`POST /auth/login`**
   - Keep request schema (`LoginRequest`) as is.
   - After successful `authenticate_admin` + `create_admin_tokens`:
     - Use `Response` / `JSONResponse` to:
       - Set `access_token` and `refresh_token` cookies with proper attributes.
       - Return JSON body containing **only** admin info (and optional non‑sensitive metadata).
   - Update `LoginResponse` schema (see 3.2) to reflect no tokens in the body.

2. **`POST /auth/refresh`**
   - Change implementation to:
     - Read `refresh_token` from `request.cookies`.
     - Call a modified `refresh_access_token` that accepts just the token string.
     - Set new cookies (at least `access_token`, optionally `refresh_token`) on success.
   - Update `TokenRefreshRequest` and `TokenRefreshResponse` schemas (see 3.2):
     - Request body no longer needs a `refresh_token` field.
     - Response body can be empty or minimal (e.g. `{ "expires_in": ... }`).

3. **New `GET /auth/me` endpoint**
   - Dependencies:
     - A cookie‑based auth dependency (see 3.3) that extracts and validates `access_token` from cookies.
   - Behavior:
     - If authenticated, return admin info (`id`, `username`).
     - If not authenticated, return 401.

4. **New `POST /auth/logout` endpoint**
   - Called with credentials (cookies attached).
   - Sends `Set-Cookie` headers that:
     - Clear `access_token` and `refresh_token` (same name/path/domain, `Max-Age=0` or expired date).
   - Returns 200/204.

### 3.2 Schemas (`app/schemas/auth.py`)

**Current:**

- `LoginResponse` includes `access_token`, `refresh_token`, `token_type`, `expires_in`, `admin`.
- `TokenRefreshRequest` contains `refresh_token`.
- `TokenRefreshResponse` returns `access_token`, `token_type`, `expires_in`.

**Target:**

1. **`LoginResponse`**
   - Remove `access_token` and `refresh_token` fields.
   - Keep `admin` and, if desired, `expires_in` or other non‑sensitive metadata.
   - Optionally define a dedicated `AdminLoginResponse` / `AdminInfo` model for clarity.

2. **`TokenRefreshRequest`**
   - Either:
     - Remove this schema and accept an empty body; or
     - Keep it as an empty model (if you want explicit structure).
   - The refresh token will **not** be read from the body anymore.

3. **`TokenRefreshResponse`**
   - Remove `access_token` (and `token_type`) if tokens are delivered only via cookies.
   - Keep `expires_in` only if you want the frontend to know when the new access token expires (optional).
   - Alternatively, make it an empty response if the frontend doesn’t need any data.

### 3.3 Auth service / dependencies (`app/services/auth.py`, `app/core/dependencies.py`)

**Current:**

- `get_current_admin`:
  - Uses `custom_security` / `HTTPBearer` to get the token from the **Authorization header**.
  - Validates it via `verify_token` and `is_token_expired`.
  - Ensures token type is `"access"`.

- `refresh_access_token`:
  - Accepts a `refresh_token` string (from request body).
  - Verifies token and type (`"refresh"`), checks expiry, then issues a new access token.

**Target:**

1. **Cookie‑based auth dependency**
   - Introduce a new dependency, e.g. `get_current_admin_from_cookie`, that:
     - Reads `access_token` from `request.cookies["access_token"]`.
     - Uses `verify_token` + `is_token_expired` as today.
     - Validates token type is `"access"`.
     - Loads the admin from DB by `sub` (same as existing logic).

   - Use this dependency in:
     - All protected admin endpoints.
     - `GET /auth/me`.

2. **Optional: transitional support for `Authorization: Bearer`**
   - If you want to keep compatibility with non‑browser clients, add a hybrid dependency that:
     - Prefers cookie if present, else falls back to header.
   - Since we don’t require backward compatibility for the SPA, this is **optional** and can be added later if needed.

3. **`refresh_access_token`**
   - Keep the core logic:
     - Verify token.
     - Ensure type is `"refresh"`.
     - Check expiry.
     - Load admin from DB.
     - Issue a new `"access"` token.
   - Usage will change:
     - It will be called from `/auth/refresh` with `refresh_token` read from cookies, not from the body.
     - It can remain a pure function that just takes a token string and DB session.

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

### Step 3 – Implement cookie‑based `POST /auth/refresh`

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

### Step 4 – Add `GET /auth/me`

- Implement a simple endpoint that:
  - Uses the cookie‑based auth dependency.
  - Returns admin info if authenticated.
  - Returns 401 if not.
- Tests:
  - With valid `access_token` cookie: returns 200 and correct admin.
  - Without cookie or with invalid/expired token: returns 401.

### Step 5 – Add `POST /auth/logout`

- Implement endpoint that:
  - Sends `Set-Cookie` clear instructions for `access_token` and `refresh_token`.
  - Returns 204 or a simple JSON message.
- Tests:
  - With cookies set: response clears both cookies (check `Set-Cookie`).
  - Idempotent behavior: calling logout when already “logged out” is safe.

### Step 6 – Switch protected endpoints to cookie‑based auth

- Update all admin‑protected routes to use the new cookie‑based dependency (`get_current_admin_from_cookie`).
- Ensure:
  - No SPA code depends on `Authorization: Bearer` anymore.
  - Integration tests that use `Authorization` headers can either:
    - Keep using the old dependency in tests only, or
    - Be updated to simulate cookie auth (preferred for end‑to‑end realism).

Given the small admin user base, it is acceptable for tests to still use header‑based auth temporarily, but for full alignment, they should be migrated to cookies as a later step.

### Step 7 – CORS and environment validation

- Confirm:
  - CORS is configured with the correct frontend origin and `allow_credentials=True`.
  - In development:
    - Cookies are visible in browser DevTools under the API origin.
    - Login sets cookies correctly; authenticated calls send cookies; refresh and logout behave as expected.
  - In production:
    - `Secure` is enabled.
    - Origins match the deployed frontend domain.

### Step 8 – Cleanup and hardening

- Remove or deprecate:
  - Unused token fields from schemas.
  - Any code paths that still expect tokens in JSON bodies or `Authorization` headers for the SPA.
- Optional security improvements (depending on appetite):
  - Add Origin/Referer checks on mutating endpoints as a lightweight CSRF mitigation.
  - Introduce a server‑side store for refresh tokens (DB or cache) to support token revocation and stricter logout semantics.

---

## 5. Checklist

The implementation should satisfy the following checklist:

- [ ] **Login:** On successful auth, set httpOnly (and Secure, SameSite) cookies for access and refresh tokens; return admin info in the body; do not require the client to send tokens back in body/header for normal requests.
- [ ] **Refresh:** Read the refresh token from the cookie only; issue new token(s) and set/overwrite cookies; do not require `refresh_token` in the body.
- [ ] **Authenticated requests:** Read the access token from the cookie; return 401 when missing or invalid; do not require `Authorization: Bearer` for the SPA.
- [ ] **Logout:** Provide an endpoint that clears the auth cookies via `Set-Cookie` (and optionally invalidates server-side state if added later).
- [ ] **CORS:** Allow the frontend origin with credentials (`Access-Control-Allow-Origin: <origin>`, `Access-Control-Allow-Credentials: true`) on all auth-related and authenticated endpoints.
- [ ] **Cookie attributes:** Use HttpOnly, Secure (in prod), SameSite (Strict or Lax), appropriate Path and expiration for both access and refresh cookies.

---

## 6. Summary

By following this plan, the backend will:

- Move from **header/body JWT transport** to **cookie‑only JWT transport**.
- Eliminate frontend storage of sensitive tokens while reusing existing JWT creation/verification logic.
- Provide a clean, future‑proof API surface for:
  - Login (`/auth/login`),
  - Refresh (`/auth/refresh`),
  - Session check (`/auth/me`),
  - Logout (`/auth/logout`),
  - And all protected admin operations using cookie‑based auth.

This enables the frontend to migrate away from `localStorage` entirely and rely on secure, httpOnly cookies for admin authentication.

