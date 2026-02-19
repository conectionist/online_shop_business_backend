# Frontend: Cookie-Based Authentication Implementation Plan

This document describes **what** the frontend must do to use the new backend cookie-based authentication model securely.

It intentionally focuses on **behavior**, not code structure, and avoids assumptions about your specific framework, state management, or folder layout. Concrete implementation details (files, functions, hooks, components) are up to the frontend codebase.

This plan assumes the backend has implemented cookie-based auth as described in the backend cookie-auth design and implementation docs.

In particular, the backend:

- Login, refresh, and logout set/clear httpOnly cookies on the **API origin**.
- Authenticated requests read the access token from a cookie, not from an `Authorization` header.
- A `session/me`-style endpoint exists to validate the session and return current user/admin info.
- Session management endpoints (`/auth/sessions*`) exist for listing and revoking sessions.

---

## 1. Goals and Constraints

### 1.1 Security goals

- **No access or refresh tokens stored in JavaScript-readable locations.**
  - No `localStorage`, `sessionStorage`, IndexedDB, or in-memory token values that are intended for reuse across page loads.
- **Use only httpOnly cookies managed by the backend for authentication.**
  - The browser automatically attaches cookies on requests; frontend code never reads or writes the raw tokens.
- **Minimize attack surface for XSS and CSRF.**
  - Removing tokens from JS significantly reduces the impact of XSS.
  - Relying on `SameSite` cookies and proper HTTP methods reduces CSRF risk.

### 1.2 Behavioral constraints

- The frontend calls an API running on a **different origin** (e.g. `https://api.example.com`).
- All API calls that rely on authentication must:
  - Send requests with **credentials included** so cookies are attached.
  - Expect the backend to use cookies for authentication.
- The frontend is responsible for:
  - Tracking **UI-level auth state** (e.g. “user is logged in”, “current admin info”).
  - Correctly handling login, logout, and session expiration from a UX perspective.

---

## 2. Target Authentication Model (Frontend View)

### 2.1 Core principles

1. **Cookies handle authentication, not JavaScript.**
   - The browser stores access and refresh tokens in httpOnly cookies.
   - Frontend code neither reads nor writes these tokens.

2. **Frontend tracks only non-sensitive session state.**
   - Examples: `isAuthenticated`, current user/admin profile, loading flags.
   - This state is derived from:
     - Successful login responses.
     - Successful `session/me` responses on app initialization.

3. **All API calls that depend on auth:**
   - Are made with credentials so cookies are sent.
   - Treat a 401 response as a signal to:
     - Attempt a refresh, then retry once; or
     - Log the user out if refresh fails.

4. **No tokens in storage.**
   - No writing access or refresh tokens to any persistent or semi-persistent store.

### 2.2 Required backend endpoints (from frontend perspective)

The frontend expects the following behavior from the API (exact paths may differ):

- `POST /auth/login`
  - Request: username + password.
  - Response:
    - Sets access and refresh cookies on the API origin.
    - Returns current admin/user info in JSON (no tokens).

- `POST /auth/refresh`
  - Request: no tokens in body; cookies are sent automatically.
  - Response:
    - If refresh succeeds: sets new access **and rotated refresh** cookies.
    - If refresh fails: returns 401; cookies may be cleared.

- `GET /auth/me` (or similar)
  - Request: no tokens in URL or headers; cookies are sent automatically.
  - Response:
    - If the session is valid: returns current user/admin info.
    - If not: returns 401.

- `POST /auth/logout`
  - Request: no tokens in body; cookies are sent automatically.
  - Response:
    - Clears auth cookies on the API origin.
    - Returns a success status (e.g. 204).

- `POST /auth/logout-all`
  - Request: no tokens in body; cookies are sent automatically.
  - Response:
    - Revokes all sessions for the current admin and clears cookies.

- Session management endpoints (`/auth/sessions*`)
  - `GET /auth/sessions` to list active sessions.
  - `GET /auth/sessions/current` for current session.
  - `GET /auth/sessions/{id}` and `DELETE /auth/sessions/{id}` to inspect/revoke another session.

---

## 3. Required Frontend Behaviors

This section describes **what** the frontend must do, without prescribing specific implementation details.

### 3.1 HTTP client configuration

All API requests to the backend that:

- Need auth, or
- Might set / clear cookies

must be sent with credentials included.

**Requirements:**

- Configure the HTTP client so that:
  - Cookies are sent on **every** request to the API origin.
  - Cookies from `Set-Cookie` headers are accepted for that origin.

**Conceptual example (using fetch):**

```ts
fetch("https://api.example.com/...", {
  method: "GET",
  credentials: "include", // critical for cookie auth
});
```

If using another client (e.g. axios), achieve the same effect (e.g. `withCredentials: true`).

### 3.2 Login flow

**Behavior:**

1. Collect credentials (e.g. username + password) from the user.
2. Send a login request to the backend:
   - Include credentials so cookies can be set.
3. On success:
   - Do **not** read or store any tokens from the response body.
   - Read only the user/admin data (e.g. `id`, `username`, `role`).
   - Update frontend auth state to reflect:
     - `isAuthenticated: true`
     - `user: <user-info-from-response>`
   - Navigate to the appropriate authenticated area (e.g. admin dashboard).
4. On failure:
   - Show a meaningful error (e.g. invalid credentials).
   - Ensure auth state remains unauthenticated.

**Constraints:**

- The login flow must never call `localStorage.setItem` or similar with access/refresh tokens.
- The presence of cookies is not directly observable from JS; success is inferred from:
  - A successful login response, and
  - Subsequent authenticated requests succeeding.

### 3.3 Auth state management

Regardless of state management choice (global store, context, simple variables), the frontend should maintain:

- A representation of the current user/admin (or `null`).
- An `isAuthenticated` flag (or equivalent).
- Optional flags like `isAuthLoading` or `isInitializingAuth`.

**Requirements:**

- **No token fields** in this state that are intended for reuse (e.g. `accessToken`, `refreshToken`).
- Persisting user info locally (e.g. for UX) is allowed, as long as:
  - Tokens are never persisted.
  - The app still validates the session via the API when needed (e.g. on page load).

### 3.4 Application initialization / session restoration

On app startup (or when the app first needs to know whether a user is logged in), the frontend must **not** assume that:

- Presence of any local state means the session is valid, or
- A previous login remains valid across sessions.

**Behavior:**

1. Optionally show a loading state while determining auth status.
2. Call the backend `session/me`-style endpoint with credentials included.
3. Handle results:
   - If response is 200:
     - Parse user/admin info from the response.
     - Set `isAuthenticated: true` and store user info in state.
   - If response is 401:
     - Set `isAuthenticated: false` and clear any stored user info.
4. Proceed to render the app (e.g. show admin area or redirect to login).

This ensures the UI reflects the actual cookie-based session state.

### 3.5 Authenticated API requests

Any request that requires authentication should:

- Be made with credentials included.
- Not manually attach `Authorization: Bearer` headers.

**Behavior:**

1. Send the request with credentials (cookies automatically included).
2. If the response is successful (e.g. 200 / 2xx):
   - Use the data as normal.
3. If the response is 401:
   - Treat this as a potential session expiration or invalid token.
   - Trigger the **token refresh flow** (see 3.6), then retry the original request once if refresh succeeds.
   - If refresh fails (still 401), treat the user as logged out.

### 3.6 Token refresh flow (from frontend perspective)

The frontend never sees the refresh token; it only triggers a refresh request.

**Behavior:**

1. When a 401 is encountered on an authenticated API call:
   - Send a refresh request to the backend with credentials.
2. Handle refresh response:
   - If refresh succeeds:
     - The backend updates cookies.
     - Retry the original request once, with credentials.
   - If refresh returns 401:
     - Consider the session invalid (e.g. refresh token expired or revoked).
     - Clear any local auth state and redirect to login.

**Constraints:**

- Do not send any token in the refresh request body.
- Do not read tokens from the refresh response body.

### 3.7 Logout flow

**Behavior:**

1. On explicit logout (e.g. user clicks “Logout”):
   - Send a logout request to the backend with credentials.
2. After the backend clears cookies:
   - Clear all local auth state (`user`, `isAuthenticated`, any cached profile).
   - Redirect the user to the login page or a public route.

**Optional additional behavior:**

- Clear any non-auth persistent state that should not survive logout (e.g. admin-only settings cached locally).

### 3.8 Optional: Session management UI

If the frontend exposes session/device management:

- Use `GET /auth/sessions` to show active sessions.
- Use `GET /auth/sessions/current` to display the current session details.
- Use `DELETE /auth/sessions/{id}` to revoke another session.
- After revocation, refresh the list; a revoked session should lose access and receive 401s.

**Constraints:**

- Do not attempt to manipulate auth cookies directly from frontend code (they should be httpOnly).

---

## 4. Error Handling and Edge Cases

The frontend should be prepared for the following scenarios and behave predictably:

### 4.1 Expired or invalid access token

- Symptom:
  - An authenticated request returns 401, but the user believes they are logged in.
- Expected behavior:
  - Trigger the refresh flow.
  - If refresh succeeds, retry the request transparently.
  - If refresh fails, treat the user as logged out and inform them that the session expired.

### 4.2 Expired or invalid refresh token

- Symptom:
  - Refresh request returns 401.
- Expected behavior:
  - Clear auth state.
  - Redirect to login.
  - Optionally show a message such as “Your session has expired, please log in again.”

### 4.3 Backend or network errors

- For non-401 errors (e.g. 500, network failures):
  - Do not immediately log the user out.
  - Show an appropriate error and allow retry.

### 4.4 Frontend reload during authenticated session

- Symptom:
  - User reloads the page while logged in.
- Expected behavior:
  - App initialization calls `session/me`.
  - If cookies are still valid, user is considered authenticated and can continue without re-entering credentials.
  - If cookies are invalid/expired, user is treated as logged out.

---

## 5. Security Considerations

### 5.1 XSS

- Removing tokens from JavaScript-read/write storage greatly reduces the impact of XSS.
- The frontend should still follow general XSS best practices (e.g. avoiding dangerous HTML injection), but token theft via XSS becomes significantly harder.

### 5.2 CSRF

- When using cookie-based auth, CSRF must be considered.
- Mitigations expected from the combined system:
  - Backend uses `SameSite` cookies (`Lax` or `Strict`).
  - Mutating operations are not exposed via public HTML forms on other sites.
  - (Optional, for higher assurance) Backend validates `Origin`/`Referer` on sensitive operations.

From the frontend perspective:

- Avoid patterns that make it easy for third-party pages to trigger state-changing requests on the user’s behalf (e.g. automatic form submissions to the API from other origins).

### 5.3 Debugging cookies

- During development, developers can verify behavior using browser DevTools:
  - Cookies appear only for the API origin.
  - Cookies are marked as `HttpOnly` and `Secure` (in production).
  - Authenticated requests include cookies when `credentials`/`withCredentials` is enabled.

---

## 6. Implementation Roadmap (Frontend Perspective)

This roadmap describes **what to implement in which order**, not how to structure the code.

1. **Ensure HTTP client supports credentials**
   - Configure the HTTP client to:
     - Include credentials on all API requests.
     - Not set `Authorization: Bearer` headers based on stored tokens.

2. **Update login behavior**
   - Send login requests with credentials.
   - On success:
     - Do not read or store tokens from the body.
     - Store only user/admin info and auth flags.

3. **Introduce session initialization using `session/me`**
   - On app startup, call the session endpoint with credentials.
   - Use response to set `isAuthenticated` and user info.
   - Handle 401 by treating user as logged out.

4. **Adapt authenticated API request flow**

   - Ensure all authenticated calls:
     - Use credentials.
     - On 401:
       - Trigger refresh, then retry once if refresh succeeds.
       - Log out user if refresh fails.

5. **Implement logout behavior**
   - Call backend logout endpoint with credentials.
   - After success:
     - Clear all local auth state.
     - Redirect to login or a public route.

6. **(Optional) Add logout-all and session management UI**
   - Call `POST /auth/logout-all` for "log out everywhere".
   - Use `/auth/sessions*` endpoints to list and revoke sessions if the UI needs it.

7. **Remove legacy token handling**
   - Remove any usage of:
     - `localStorage` / `sessionStorage` for access or refresh tokens.
     - `Authorization: Bearer` headers derived from stored tokens.
     - Helper functions specifically designed to read/write tokens in JS storage.

8. **Review tests and documentation**
   - Update automated tests to:
     - Reflect cookie-based auth (e.g. mocking `session/me` and login success).
     - Avoid setting tokens directly in storage to simulate auth.
   - Update developer documentation to:
     - Explain the new cookie-based auth model.
     - Describe how to debug auth issues locally.
    - If your project has a public cookie or privacy policy, update it to mention the strictly necessary authentication cookies (httpOnly, Secure, SameSite) used for login sessions, and to remove or adjust any statement that claims the site does not use cookies.

---

## 7. Testing and Verification

The frontend should verify the following scenarios once the migration is implemented:

- **Login**
  - Submitting valid credentials results in:
    - No tokens in `localStorage` / `sessionStorage`.
    - Auth cookies present for the API origin (visible in DevTools).
    - Authenticated API calls succeeding when made with credentials.

- **Refresh**
  - When an access token expires:
    - An authenticated request returning 401 triggers a refresh call.
    - After refresh, the original request is retried once and succeeds.
    - No tokens are written to JS storage at any point.

- **Logout**
  - Clicking logout:
    - Calls the backend logout endpoint with credentials.
    - Results in auth cookies being cleared.
    - Clears local auth state and navigates the user to the login/public area.

- **Logout-all / Sessions (if implemented)**
  - Calling logout-all:
    - Revokes all sessions and clears cookies.
    - Subsequent requests from other devices return 401.
  - Revoking a specific session:
    - That device loses access (401 on next request).

- **Reload**
  - Reloading the app while “logged in”:
    - Calls the `session/me` endpoint with credentials.
    - Restores auth state if cookies are still valid, or treats the user as logged out if not.

- **Cross-origin behavior**
  - For SPA and API on different origins:
    - Requests include cookies when credentials are enabled.
    - The backend responds with the appropriate `Access-Control-Allow-Origin` (not `*`) and `Access-Control-Allow-Credentials: true`.

---

## 8. Summary

By following this plan, the frontend will:

- Stop handling raw access and refresh tokens in JavaScript.
- Rely entirely on secure, httpOnly cookies for authentication.
- Maintain a clear, robust model for:
  - Login, logout, and session restoration.
  - Handling expired tokens and errors.
  - Synchronizing UI state with the actual backend session.

This aligns with the backend’s cookie-based authentication model and significantly improves the overall security posture of the application without imposing unnecessary complexity on the frontend codebase.
