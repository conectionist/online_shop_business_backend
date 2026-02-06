# Frontend: Cookie-Based Authentication Migration Guide

This guide describes how to migrate the frontend from storing JWT tokens in `localStorage` to using **httpOnly, Secure, SameSite cookies** for authentication. The goal is to eliminate the XSS risk of token theft (see security assessment: "Sensitive Data in LocalStorage").

**Prerequisite:** The backend must implement cookie-based auth first (see `docs/BACKEND_COOKIE_AUTH_REQUIREMENTS.md`). The frontend changes in this guide assume the backend sets auth cookies on login/refresh and accepts credentials (cookies) on requests.

---

## Table of Contents

1. [Current Behavior Summary](#1-current-behavior-summary)
2. [Target Behavior Summary](#2-target-behavior-summary)
3. [Files to Modify](#3-files-to-modify)
4. [Step-by-Step Implementation](#4-step-by-step-implementation)
5. [Testing and Verification](#5-testing-and-verification)
6. [Rollback and Compatibility](#6-rollback-and-compatibility)

---

## 1. Current Behavior Summary

### Where tokens are stored today

| Token          | Storage location(s)                                                                 |
|----------------|--------------------------------------------------------------------------------------|
| Access token   | Zustand `authStore` state (`token`) → persisted to `localStorage` under key `auth-storage`; also written explicitly as `localStorage.setItem('access_token', token)` in `authStore.ts`. |
| Refresh token  | `localStorage.setItem('refresh_token', refresh_token)` in `authService.ts` and `LoginPage.tsx`. |

### Where tokens are read and used

- **API requests:** `src/services/api.ts` request interceptor reads the access token from `useAuthStore.getState().getCurrentToken()` and sets `Authorization: Bearer <token>`.
- **Token refresh:** `authService.refreshAccessToken()` reads `localStorage.getItem('refresh_token')`, sends it in the request body to `POST /auth/refresh`, then updates the auth store (and localStorage) with the new access token.
- **Auth init:** `authStore.validateTokenOnInit()` uses `authService.getRefreshToken()` (localStorage) and `authService.isTokenExpiringSoon()` (token from store) to decide whether to refresh on app load.
- **Logout:** `authService.logout()` and `authStore.logout()` both remove `access_token` and `refresh_token` from localStorage and clear the auth store.

### Login flow today

- **LoginPage:** Uses raw `fetch()` to `POST /api/v1/auth/login` (no `credentials: 'include'`). On success, reads `access_token`, `refresh_token`, and `admin` from the JSON body, writes refresh token to localStorage, and calls `useAuthStore.getState().login(access_token, userData)`.
- **authService.login():** Used elsewhere (e.g. if login were done via apiClient); same idea: reads tokens and user from response body, stores refresh in localStorage, calls store `login(access_token, userData)`.

### Important detail

- The app uses **cross-origin** API calls: frontend is served from one origin (e.g. `https://shop.example.com`), API from another (e.g. `https://api.example.com`). For cookies to be sent on cross-origin requests, the backend must send proper CORS headers and the frontend must send requests with **credentials** (e.g. `withCredentials: true` in axios, `credentials: 'include'` in fetch).

---

## 2. Target Behavior Summary

After migration:

- **No JWT (access or refresh) must ever be stored in localStorage or in any persisted store that is readable by JavaScript.**
- The backend sets **httpOnly** cookies for access and refresh tokens (or at least refresh; access can be short-lived in a cookie or in memory depending on backend design). The browser sends these cookies automatically on requests when **credentials** are included.
- The frontend:
  - Sends **credentials** on all API requests (so cookies are sent).
  - Does **not** read or write access/refresh tokens from/to localStorage or from response body (for auth purposes).
  - Does **not** set `Authorization: Bearer <token>` if the backend uses a cookie for the access token; if the backend keeps accepting Bearer during a transition period, the frontend can optionally stop sending it once the backend is cookie-only.
  - Derives “logged in” state from: (a) backend setting a cookie and (b) successful response from login or from a “session/me” endpoint that runs on init. User info can still come from the login response body or from a dedicated “me” endpoint.
  - Calls a backend **logout** endpoint that clears the auth cookies (or the frontend clears cookies if same-origin and your app controls the domain). Then clears local UI state (auth store).

---

## 3. Files to Modify

| File | Purpose of changes |
|------|--------------------|
| `src/services/api.ts` | Enable `withCredentials: true` on the axios instance; remove or conditionally stop setting `Authorization: Bearer` when using cookie auth; ensure 401 refresh flow works without reading a token from store (refresh request will send cookie). |
| `src/services/authService.ts` | Remove all localStorage read/write for tokens; change login to use credentials and not store tokens from body; change refresh to POST with credentials and not send refresh_token in body or read from localStorage; add optional call to backend logout endpoint; remove or adapt `getAccessToken`/`getRefreshToken` and `isTokenExpiringSoon` (if access token is no longer in JS). |
| `src/stores/authStore.ts` | Remove token from persisted state and remove all localStorage access for tokens; change `login` to accept only user (no token); remove `updateToken` or use only for in-memory/session use if backend still returns access token in body during transition; change `validateTokenOnInit` to rely on cookie-based session check (e.g. call a “me” or “session” endpoint with credentials). |
| `src/pages/LoginPage.tsx` | Use `credentials: 'include'` on login fetch; stop reading `access_token`/`refresh_token` from response body and stop writing them to localStorage; pass only user data to the auth store (no token). |
| `src/components/AuthInitializer.tsx` | No token in store: initialization should trigger a cookie-based session validation (e.g. call “me” or “session” with credentials); keep loading state until that succeeds or fails. |
| `src/types/api.ts` | Optionally keep or extend types for login/refresh response bodies if backend still returns user/tokens for backward compatibility; document that tokens in body are not used for storage. |
| `src/test/setup.ts` | If tests mock localStorage for auth, switch to mocking cookie presence or mock “session/me” endpoint; ensure persisted auth store no longer contains tokens. |
| Tests that rely on auth | Update any test that sets `localStorage` tokens or reads `getCurrentToken()`/`getRefreshToken()` to use cookie mocks or session endpoint mocks instead. |
| `public/legal/cookies.md` | Update the cookie policy to reflect that the site uses strictly necessary cookies for authentication (httpOnly cookies set by the API when users log in); remove or replace the statement that the site does not use cookies. |

---

## 4. Step-by-Step Implementation

### 4.1 Backend readiness

- Confirm backend implements: login and refresh set httpOnly cookies; refresh reads token from cookie; CORS allows frontend origin with credentials; logout clears auth cookies (see `docs/BACKEND_COOKIE_AUTH_REQUIREMENTS.md`).

### 4.2 Enable credentials on API client

**File:** `src/services/api.ts`

- In `axios.create()` options, set `withCredentials: true` so every request includes cookies for the API origin.
- In the request interceptor: **either** remove the block that sets `Authorization: Bearer ${token}` (if backend uses only cookies for access token), **or** keep it only for a transition period if backend still accepts Bearer. Once backend is cookie-only, remove it.

Example (conceptual):

```ts
export const apiClient = axios.create({
  withCredentials: true,  // send cookies on cross-origin requests
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
});
// In request interceptor: do NOT set Authorization header when using cookie-based access token.
```

### 4.3 Auth service: remove localStorage and token handling

**File:** `src/services/authService.ts`

1. **login()**
   - Use `apiClient.post(...)` with credentials (already enabled on apiClient) so that when the backend sets cookies, they are stored by the browser. Do not read `access_token` or `refresh_token` from `response.data` for storage.
   - Read only **user** (or equivalent) from the response body and call the auth store with that user only, e.g. `useAuthStore.getState().login(userData)` (signature of `login` in the store must be updated to accept only user when in cookie mode).
   - Remove every `localStorage.setItem('refresh_token', ...)` and any `localStorage.setItem('access_token', ...)`.

2. **refreshAccessToken()**
   - Do not read refresh token from localStorage. Send `POST /auth/refresh` with no body (or body without `refresh_token`). Rely on the browser sending the refresh cookie (with credentials). Do not update any in-memory or stored access token if the backend uses an access-token cookie; the next request will automatically send the new cookie. If the backend still returns `access_token` in the body for a transition period and still expects Bearer, you can temporarily call `updateToken(access_token)` for in-memory use only (no localStorage).
   - If the backend sets a new access (and/or refresh) cookie in the refresh response, nothing else is required on the frontend for storage.

3. **logout()**
   - Call the backend logout endpoint with credentials (e.g. `apiClient.post('/auth/logout')`) so the backend can clear the auth cookies. Then clear the auth store (user, token, isAuthenticated). Remove all `localStorage.removeItem('access_token')` and `localStorage.removeItem('refresh_token')`.
   - Keep cleanup of push subscriptions as today.

4. **getAccessToken() / getRefreshToken()**
   - Remove or deprecate. If anything still calls them (e.g. response interceptor that retries with “new token”), refactor so that after refresh the frontend simply retries the request with credentials (the new cookie will be sent automatically). So: remove reading token from store for the retry; just retry the same request.

5. **isTokenExpiringSoon()**
   - If the access token is only in an httpOnly cookie, the frontend cannot read it. Either remove this and rely on the backend returning 401 when expired (then refresh and retry), or keep a minimal in-memory copy of expiration only (e.g. from login/refresh response) if the backend sends it and you want to refresh proactively. Prefer the simpler approach: no token in JS, rely on 401 + refresh.

6. **refreshTokenIfNeeded()**
   - If you no longer have access to the token, you cannot check “expiring soon”. Either remove this and rely only on 401-triggered refresh, or implement a small “session check” request that triggers refresh on the backend if needed.

7. **makeAuthenticatedRequest()**
   - Can remain; it will call the request function which uses credentials. Ensure it does not depend on `getAccessToken()` or `getRefreshToken()`.

### 4.4 Auth store: stop persisting tokens

**File:** `src/stores/authStore.ts`

1. **State**
   - Keep `user`, `isAuthenticated`, `isLoading`. Remove `token` from state, or keep it only as an optional in-memory value for a transition period (never persist it).

2. **persist()**
   - In `partialize`, do **not** include `token`. Include only what is safe for localStorage (e.g. `user`, `isAuthenticated`). If you prefer not to persist “logged in” at all when using cookies (so that every reload re-validates via cookie), you can partialize to an empty object or only `user` for UX (e.g. show name until session check runs).

3. **login(token, user)**
   - Change to `login(user)` when using cookie auth. Remove any `localStorage.setItem('access_token', ...)` and `localStorage.setItem('refresh_token', ...)`. Set `user`, `isAuthenticated: true`, `isLoading: false`.

4. **logout()**
   - Remove `localStorage.removeItem('access_token')` and `localStorage.removeItem('refresh_token')`. Clear `user`, `token`, `isAuthenticated`.

5. **updateToken(token)**
   - Remove or use only in memory during transition. Do not write to localStorage.

6. **getCurrentToken()**
   - Remove or return null when using cookie auth so no code sends Bearer from store.

7. **validateTokenOnInit()**
   - Do not use `authService.getRefreshToken()` or `authService.isTokenExpiringSoon()`. Instead, call a backend “session” or “me” endpoint with credentials (using apiClient). If it returns 200 with user data, set user and `isAuthenticated: true`. If it returns 401, set `isAuthenticated: false` and clear user. This validates that the cookie is still valid and restores user state without ever reading a token in JS.

### 4.5 Login page: credentials and no token storage

**File:** `src/pages/LoginPage.tsx`

1. Use `credentials: 'include'` on the login `fetch()` call so the browser sends and stores cookies.
2. After a successful response, do not read `access_token` or `refresh_token` from the body. Read only user/admin data and call the auth store with that (e.g. `useAuthStore.getState().login(userData)`).
3. Remove every `localStorage.setItem('refresh_token', ...)` and any use of `access_token` for storage.
4. If the login response body no longer contains tokens (backend cookie-only), the type for the response can be updated to reflect only `user`/`admin` (and optionally a message).

### 4.6 Auth initializer

**File:** `src/components/AuthInitializer.tsx`

- No change to structure; the logic inside `validateTokenOnInit()` (in the store) will change to a cookie-based session check as described above. Ensure the store’s `validateTokenOnInit` is called when the user “appears” authenticated (e.g. from persisted `isAuthenticated` or `user`), and that it uses the new session/me endpoint with credentials.

### 4.7 Response interceptor (401 and refresh)

**File:** `src/services/api.ts`

- On 401, call `authService.refreshAccessToken()`. After refresh, do **not** read `authService.getAccessToken()` or set `Authorization` on the retry. Simply retry the original request: `return apiClient(originalRequest)`. With `withCredentials: true`, the new cookie set by the refresh response will be sent on the retry.
- Ensure the refresh request itself uses the same apiClient (with credentials) so the refresh cookie is sent.

### 4.8 Types

**File:** `src/types/api.ts` (and authService/LoginPage types)

- Update `AuthResponse` / login response type so that `access_token` and `refresh_token` are optional or removed if the backend no longer returns them. Keep `user` (or `admin`) as returned by the backend.
- Update `RefreshResponse` if needed (e.g. empty body when tokens are only in cookies).

### 4.9 Tests

**File:** `src/test/setup.ts`

- The in-memory localStorage mock remains useful for other persistence (e.g. cart). For auth, tests should not rely on storing tokens in localStorage. Prefer:
  - Mocking the “session/me” or “login” endpoint to return 200 with user when credentials are present, and 401 otherwise; or
  - Mocking document.cookie if you need to simulate cookie presence (less common).

Update any test that:

- Sets `localStorage.setItem('access_token', ...)` or `refresh_token` to establish “logged in” state. Use a session/me mock or a login mock with credentials instead.
- Asserts on `getCurrentToken()` or `getRefreshToken()`; remove or replace with assertions on “session” request or redirect.

### 4.10 Cookie policy (legal)

**File:** `public/legal/cookies.md`

- Update the policy to reflect the new reality: the site uses **strictly necessary** cookies for authentication. When users log in (admin), the API sets httpOnly, Secure, SameSite cookies (access and refresh tokens); the site does not use cookies for marketing, profiling, or other non-essential purposes.
- Remove or replace the current sentence that says the site does not use cookies (e.g. "În prezent, acest site nu utilizează cookie-uri").
- Keep the existing sections on what cookies are, how to control them in the browser, and analytics (Plausible/Rybbit without cookies). Add a short section describing the essential authentication cookies: purpose (secure login/session), set by the API on login, not readable by JavaScript, no consent required as strictly necessary.

---

## 5. Testing and Verification

- **Login:** Submit credentials; verify no tokens appear in localStorage; verify cookies are set (DevTools → Application → Cookies for the API origin); verify redirect to admin and that subsequent API calls succeed.
- **Refresh:** Expire the access token (or wait); trigger an API call; verify 401 → refresh (with cookie) → retry succeeds and no token in localStorage.
- **Logout:** Click logout; verify backend logout is called and auth cookies are cleared (or cleared by backend); verify auth store is cleared and user is redirected to login.
- **Reload:** Log in, reload the app; verify `validateTokenOnInit` (or equivalent) calls session/me with credentials and restores user state without any token in JS.
- **Cross-origin:** If frontend and API are on different origins, verify CORS and credentials: requests must include cookies and backend must respond with `Access-Control-Allow-Origin: <origin>` (not `*`) and `Access-Control-Allow-Credentials: true`.

---

## 6. Rollback and Compatibility

- If the backend supports both cookie-based and body-based tokens during migration, the frontend can be feature-flagged or deployed after the backend. Once the backend is cookie-only, remove any remaining Bearer or body-token handling from the frontend.
- Do not persist tokens to localStorage at any point after migration; that would reintroduce the XSS risk documented in the security assessment.

---

## Summary Checklist

- [ ] Backend implements cookie-based login, refresh, logout and CORS with credentials (see backend guide).
- [ ] `apiClient` uses `withCredentials: true`; no `Authorization: Bearer` when using cookie auth.
- [ ] `authService`: no localStorage for tokens; login/refresh use credentials only; logout calls backend and clears store.
- [ ] `authStore`: no token in state or in `partialize`; `login(user)` only; `validateTokenOnInit` uses session/me with credentials.
- [ ] `LoginPage`: `credentials: 'include'`, no token read/write from/to body or localStorage.
- [ ] 401 interceptor retries without setting Bearer; refresh uses credentials.
- [ ] Types and tests updated; manual and automated tests pass.
- [ ] `public/legal/cookies.md` updated to describe strictly necessary auth cookies (no banner).
