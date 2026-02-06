# Backend: Cookie-Based Authentication Requirements

This document describes **what** the backend must do to support secure, cookie-based authentication so the frontend can stop storing JWT tokens in `localStorage` (see security assessment: "Sensitive Data in LocalStorage"). The focus is on requirements and behavior, not on implementation details or code. The frontend migration is described in `docs/FRONTEND_COOKIE_AUTH_MIGRATION_GUIDE.md`.

---

## Table of Contents

1. [Goals](#1-goals)
2. [Login](#2-login)
3. [Refresh](#3-refresh)
4. [Authenticated Requests](#4-authenticated-requests)
5. [Logout](#5-logout)
6. [CORS and Credentials](#6-cors-and-credentials)
7. [Cookie Attributes](#7-cookie-attributes)
8. [Response Bodies (Optional)](#8-response-bodies-optional)
9. [Summary Checklist](#9-summary-checklist)

---

## 1. Goals

- **Stop exposing tokens to JavaScript.** The frontend must not receive access or refresh tokens in response bodies for the purpose of storing them, and must not need to send tokens in request bodies or headers. The browser should be the only party that sends and receives tokens, via **httpOnly** cookies.
- **Preserve existing semantics.** Authenticated API behavior (who can call what, 401 on invalid/expired token, refresh flow) should remain; only the transport of tokens moves from JSON body/Authorization header to cookies.
- **Support cross-origin frontend.** The frontend is served from a different origin than the API (e.g. SPA on `https://shop.example.com`, API on `https://api.example.com`). The backend must allow credentialed requests and set cookies in a way the browser will send back on subsequent requests to the API origin.

---

## 2. Login

**Endpoint:** Same as today (e.g. `POST /api/v1/auth/login` with username/password in the body).

**Required behavior:**

- Validate credentials. If invalid, return the same error response as today (e.g. 401 or 422).
- If valid:
  - Issue an **access token** and a **refresh token** (same semantics as today: short-lived access, longer-lived refresh).
  - **Set two cookies** in the response:
    - One cookie for the **access token** (e.g. name `access_token` or `session`).
    - One cookie for the **refresh token** (e.g. name `refresh_token`).
  - Both cookies must be **httpOnly**, **Secure** (in production), and **SameSite** (e.g. `Strict` or `Lax`). Path and domain must be set so the browser sends them on subsequent requests to the API (see [Cookie attributes](#7-cookie-attributes)).
  - Optionally, include **user info** in the response body (e.g. `user` or `admin` with id, email, name, role) so the frontend can update its UI without an extra request. The frontend will **not** store any token from the body.

**What the backend must not do:**

- Rely on the frontend to send back the access or refresh token in the body or in a header for normal authenticated requests. After login, the backend should rely on the cookie for those tokens (or on the cookie for refresh and a new access-token cookie after refresh).

---

## 3. Refresh

**Endpoint:** Same as today (e.g. `POST /api/v1/auth/refresh`).

**Required behavior:**

- **Read the refresh token from the cookie** that was set at login (or from the previous refresh if you rotate refresh tokens). Do **not** require or use a `refresh_token` field in the request body.
- If the cookie is missing or the refresh token is invalid/expired, return 401 (and optionally clear the auth cookies).
- If valid:
  - Issue a new access token (and optionally a new refresh token if you rotate).
  - **Set the cookie(s)** again in the response (same names and attributes as login). Overwrite the access-token cookie with the new value; if you rotate the refresh token, overwrite the refresh-token cookie as well.
  - Response body can be empty or contain only non-sensitive data (e.g. `expires_in`). The frontend will **not** read or store any token from the body; it will rely on the browser to store the updated cookies.

**What the backend must not do:**

- Require the client to send the refresh token in the JSON body. The only way the client sends the refresh token is via the cookie (with credentialed requests).

---

## 4. Authenticated Requests

**Required behavior:**

- For endpoints that require authentication (e.g. admin-only, or “me”):
  - **Read the access token from the cookie** that was set at login or refresh. Do **not** require an `Authorization: Bearer <token>` header for cookie-based clients. Optionally, you can still accept Bearer for backward compatibility during a transition period; if both are present, decide a clear precedence (e.g. cookie over Bearer or vice versa).
  - If the cookie is missing or the access token is invalid/expired, return **401**. The frontend will then call refresh (sending the refresh cookie) and retry. If refresh fails, the frontend will treat the user as logged out.
- Same authorization rules as today (e.g. role checks, resource ownership); only the source of the token changes from header to cookie.

---

## 5. Logout

**Endpoint:** A dedicated logout endpoint is strongly recommended (e.g. `POST /api/v1/auth/logout`).

**Required behavior:**

- The client will call this endpoint **with credentials** (cookies sent). The backend should:
  - Invalidate the refresh token (and optionally the session) on the server side if you keep a server-side record (e.g. blocklist or delete from DB).
  - **Clear the auth cookies** by sending `Set-Cookie` headers that remove or expire the access and refresh cookies (same names, path, and domain as when they were set, with `Max-Age=0` or `Expires` in the past).
- Return 200 or 204. The frontend will then clear its local state (user, isAuthenticated) and redirect to login.

**If you do not add a logout endpoint:**

- The frontend cannot ask the backend to clear the cookies. The user would remain “cookie-logged-in” until the refresh token expires or the user clears cookies manually. So implementing a logout endpoint that clears the auth cookies is required for a good UX and consistent security.

---

## 6. CORS and Credentials

Because the frontend is on a different origin than the API, the browser will only send cookies on cross-origin requests if:

1. The client sends the request **with credentials** (e.g. `fetch(..., { credentials: 'include' })` or axios `withCredentials: true`).
2. The server responds with:
   - `Access-Control-Allow-Origin: <origin>` set to the **exact** frontend origin (e.g. `https://shop.example.com`), **not** `*`.
   - `Access-Control-Allow-Credentials: true`.
   - Other CORS headers as needed (e.g. `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers` for preflight).

**Required behavior:**

- For all auth-related and authenticated endpoints (login, refresh, logout, and every API that uses the auth cookies), the backend must include the CORS headers above so that credentialed requests from the frontend origin succeed and cookies are sent and received.

---

## 7. Cookie Attributes

The following attributes are required for security and correct behavior:

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

---

## 8. Response Bodies (Optional)

- **Login:** The backend may continue to return user (or admin) info in the body so the frontend can show the user’s name and role without an extra “me” request. The backend should **not** return access_token or refresh_token in the body once the frontend has migrated (or can return them only for legacy clients during transition).
- **Refresh:** The response body can be empty or minimal (e.g. `{}` or `{ "expires_in": 900 }`). Tokens should be delivered only via Set-Cookie.
- **Session/me:** If the frontend uses a “session” or “me” endpoint on load to validate the cookie and get the current user, that endpoint should read the access token from the cookie, validate it, and return user info (and 401 if invalid/expired). No tokens in the body.

---

## 9. Summary Checklist

The backend must:

- [ ] **Login:** On successful auth, set httpOnly (and Secure, SameSite) cookies for access and refresh tokens; optionally return user in body; do not require the client to send tokens back in body/header for normal requests.
- [ ] **Refresh:** Read refresh token from cookie only; issue new token(s) and set/overwrite cookies; do not require refresh_token in body.
- [ ] **Authenticated requests:** Read access token from cookie; return 401 when missing or invalid; do not require Authorization: Bearer for cookie-based clients (or support both during transition).
- [ ] **Logout:** Provide an endpoint that invalidates the session and clears the auth cookies via Set-Cookie.
- [ ] **CORS:** Allow the frontend origin with credentials (`Access-Control-Allow-Origin: <origin>`, `Access-Control-Allow-Credentials: true`).
- [ ] **Cookie attributes:** HttpOnly, Secure (in prod), SameSite (Strict or Lax), appropriate Path and expiration.

After the backend meets these requirements, the frontend can be migrated using `docs/FRONTEND_COOKIE_AUTH_MIGRATION_GUIDE.md`.
