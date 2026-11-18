# Code quality review

A review of the backend as of 6.4.0 (commit `07011c4`, November 2026): what is good, what gets in
the way, and what to change first.

**Verdict: 5 out of 10.** On a scale where 1 is AI slop and 10 is a codebase others should copy.
The structure is sound, production refuses unsafe settings, and the login is built with care. What
pulls it down is error handling that sends exception text to clients, two gaps in session handling,
no linter, tests that only go through HTTP, and a lot of leftover files and stale documentation.

## Fixed before this review was published

The review found two problems someone could exploit on the live shop. They were fixed and deployed
first, in [#40](https://github.com/conectionist/online_shop_business_backend/pull/40):

- **Orders stored the price the customer sent.** Placing an order needs no login, and each item was
  stored at the price in the request. New orders now store each item at the product's current price.
- **The rate limits keyed on `X-Forwarded-For`,** which any client can set, so a different value on
  each request got past both the login and the order limit. They now key on the client IP Uvicorn
  resolves, and production refuses to start unless `FORWARDED_ALLOW_IPS` names the proxy.

Three follow-ups from reviewing that fix are open: [#41](https://github.com/conectionist/online_shop_business_backend/issues/41) (tell the customer when a price changed),
[#42](https://github.com/conectionist/online_shop_business_backend/issues/42) (orders accept deleted or unlisted products) and
[#43](https://github.com/conectionist/online_shop_business_backend/issues/43) (small cleanups).

## How this was measured

- Read `app/` (117 files, about 19,600 lines), `tests/`, the Dockerfiles, both compose files, both
  CI workflows, the README and `docs/`.
- Ran the integration suite against MySQL 8 and Redis, with the API outside Docker: 407 passed and
  1 skipped. The unit tests in `tests/` passed too. CI is green on `master`.
- Ran `ruff` with a few rules (unused imports and variables, broad and silent `except`,
  `== True`). The project has no linter of its own.
- Counted lines of code against comments and docstrings, function lengths, and comments about the
  project's history.
- Reproduced both problems above on a local copy before fixing them, and tested the fix the same way.

## Strengths

### The structure is clear

`models/`, `schemas/`, `services/` and `api/endpoints/` keep the database, the API's shapes, the
business rules and the routes apart, and each entity has one file in each. The schema is managed by
22 Alembic migrations.

### Production refuses unsafe settings

`app/core/config.py` stops the API at startup in production when `ALLOWED_HOSTS` is missing or `*`,
when `FRONTEND_URL` or `PUBLIC_API_URL` is not a public https URL, when `COOKIE_SAMESITE` is not
`lax` or `strict`, when Redis has no credentials, when metrics need a token and have none, and now
when the proxy is not trusted. A wrong `.env` fails loudly instead of running insecurely.

### The login is careful

- Passwords are hashed with Argon2.
- Tokens are sent as HttpOnly cookies, so scripts in the page cannot read them.
- Refresh tokens are rotated on every use and stored as hashes (`hash_refresh_token()`), so a
  database leak does not leak live tokens. An admin can list and revoke sessions.
- Login attempts are rate-limited per IP.

### The rest of the edges are handled

- Uploads are checked for content type and size and stored under random names
  (`app/core/file_upload.py`).
- `/metrics` needs a bearer token, compared with `hmac.compare_digest` (`app/main.py:233`).
- Redis caches the public reads, and Prometheus metrics are exported.
- Dependencies are pinned, the container runs as a non-root user, compose has health checks, the
  database and Redis sit on an internal network, and the database port is not published.

### The newer code is better

The statistics (`app/services/statistics.py`) and the Google Merchant feed
(`app/services/product_feed.py`) explain their rules in docstrings: what a period is, how a sold-out
product is detected, why prices are whole lei. Overall there are about 2 comment or docstring lines
per 10 lines of code, which is about right.

## Weaknesses

### 1. Exception text is sent to clients

187 responses put the exception's text in `detail`. One of them is on order creation, which is
public (`app/services/order.py:703`):

```python
raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
```

A database error's text can include the SQL, table and column names and the values sent. The
pattern is copied into almost every module: `categories.py` has 13, `order.py`, `unitati.py` and
`modalitati_plata.py` 11 each.

### 2. Two gaps in session handling

- **A revoked session keeps working.** `get_current_admin_from_cookie()` checks the session only
  when the refresh cookie comes with the request (`app/services/auth.py:192`). The comment says the
  fallback is for test helpers. A stolen access token sent without the refresh cookie skips the
  check, so revoking the session does not stop it until the token expires, 30 minutes by default.
- **Two refreshes at once both succeed.** `refresh_access_token()` reads the token row without a lock
  (`app/services/auth.py:414`). Two requests with the same refresh token both see it unrevoked, and
  both get a new pair, so one session becomes two. A rotated token used again is rejected, but its
  successors are not revoked: `replaced_by_token_id` is written (`auth.py:488`) and never read.

### 3. Error handling is broad and tied to HTTP

- Services raise `HTTPException` 329 times in 17 modules, so the business rules can only be used
  from a request, and a test of a rule has to read HTTP status codes.
- 145 `except Exception` blocks, 31 of them silent (`try`/`except`/`pass`). Many catch the
  `HTTPException` raised a few lines above and raise it again.
- `ruff` also finds 70 unused imports, 11 unused variables and 18 comparisons with `== True`.
  Nothing checks for these, and there is no formatter.

### 4. Some functions are very long

`create_product_endpoint()` is 366 lines (`app/api/endpoints/products.py:267`). It takes the price,
quantity and unit as strings ("Changed to str to handle validation manually") and parses them by
hand, which is what FastAPI and Pydantic would do from the parameter types. `create_order()` is 162
lines, `order.py` is 1,170, and 18 functions are over 100 lines.

### 5. Naming and units are inconsistent

- Names mix Romanian and English: `nume`, `pret`, `cantitate` and `unitati_id` sit next to
  `description` and `category_id`, and the endpoints `unitati` and `modalitati_plata` next to
  `delivery_types`.
- The schemas say prices are in cents (`app/schemas/product.py:27`, `:85`,
  `app/schemas/order.py:42`, `app/schemas/list_product.py:28`), and so does a comment in
  `products.py:432`. Prices are stored in whole lei (`product_feed.py:124`). A client that believes
  the API docs is off by a factor of 100.

### 6. Smaller bugs

- `PUT /delivery-types/reorder` is defined twice (`app/api/endpoints/delivery_types.py:86` and
  `:240`). The second is never reached.
- `system_config.py:19`, `:99` and `:103` hardcode `/app/config/placeholders` and `/app/uploads`,
  ignoring `UPLOAD_FOLDER`.
- Startup and shutdown use the deprecated `@app.on_event` (`app/main.py:149`, `:198`).
- The daily prune task (`app/main.py:179`) calls the synchronous database code inside the event
  loop, which blocks every request while it runs. Its task is created without keeping a reference,
  and asyncio keeps only a weak one.

### 7. The tests only go through HTTP

- 408 integration tests, all against a running server. Pure logic, such as unit pricing or
  the statistics periods, is only tested end to end.
- CI runs no unit tests: `Dockerfile.test:16` copies only `tests/integration/`.
- `tests/integration/test_product_overrides_api.py:13` hardcodes the host `api_server_test`, so
  that file fails anywhere else.
- `run_api_integration_tests.sh:43` and `:53` wait with fixed `sleep`s instead of polling `/health`.
- There are two test folders, `test/` (an empty `conftest.py`, some data) and `tests/`.

### 8. Clutter and stale documentation

- **README:** the badge points to `api-tests.yml`, which does not exist, and the project structure
  (`README.md:16`) lists folders that do not exist (`app/api/v1/`, `app/core/config/`,
  `db/docker-entrypoint-initdb.d/`).
- **Leftover files:** `step7_validation_summary.md` and `test_cors_validation.py` in the root;
  `plans/` next to `docs/todo/` and `docs/archive/`; rule folders for both Cursor and Windsurf; three
  documents named after the AI model that wrote them; `db/migrations/001_add_delivery_payment_to_orders.sql`
  and `db/schema.sql` next to Alembic.
- **Dependencies:** two MySQL drivers, `mysql-connector-python` for the app and `PyMySQL` for
  Alembic (`requirements.txt:5-6`); `debugpy` in the production requirements (`:11`); `passlib`,
  which is no longer maintained (`:10`).
- **CI:** two workflows, automatic and manual, whose test jobs are identical.
- **Comments about history:** 11, such as "Changed to str to handle validation manually"
  (`products.py:269`) and "Legacy primary_image_path field handling has been completely removed"
  (`app/services/product.py:487`).

## Suggestions, most important first

### 1. Stop sending exception text to clients

Handle database and unexpected errors once, in `main.py`, and log the details there:

```python
@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Database error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

Then delete the `try`/`except` blocks whose only job is to turn an error into a 500 with its text.
That removes most of the 187 leaks and most of the 145 `except Exception` blocks. Start with the
public endpoints: orders, products, lists, the feed.

### 2. Close the two session gaps

Put the session in the access token: when a token pair is issued, add the refresh token row's id as
a `sid` claim, and check that session on every request, whether or not the cookie came with it.
Tests that build tokens by hand then create a session first. Lock the refresh token row while it is
rotated:

```python
token_row = (
    db.query(RefreshToken)
    .filter(RefreshToken.token_hash == token_hash)
    .with_for_update()
    .one_or_none()
)
```

The second of two simultaneous refreshes then waits, sees the token revoked, and is rejected. When a
revoked token that has a `replaced_by_token_id` is used again, revoke its successors too: someone
else has a copy of it.

### 3. Add a linter and a formatter to CI

Configure `ruff` in `pyproject.toml`, apply the 76 automatic fixes, and run `ruff check` and
`ruff format --check` in CI. Turn on `BLE001` (broad `except`) once suggestion 1 has removed most
of the existing ones.

### 4. Run unit tests in CI, and write them for the logic

Copy all of `tests/` into the test image and run `pytest tests --ignore=tests/integration` before
the integration suite. Then add unit tests for the pure logic: unit pricing, the statistics periods,
duplicate detection. Make the hardcoded host a fixture, poll `/health` instead of sleeping, and
merge `test/` into `tests/`.

### 5. Let FastAPI validate, and split the long functions

Declare form fields with their types and limits, and the hand parsing goes:

```python
pret: int = Form(..., gt=0, description="The price in whole lei"),
cantitate: int = Form(..., ge=0),
unitati_id: int = Form(...),
```

Then split `create_product_endpoint()` and `create_order()` into steps: validate, resolve the
related rows, write, notify.

### 6. Key IPv6 clients by network

An IPv6 customer usually has a whole `/64` to themselves, so changing the address within it gets a
fresh rate limit. If the proxy accepts IPv6, key those clients by their `/64`:

```python
def _rate_limit_key(host: str) -> str:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return host
    if address.version == 6:
        return str(ipaddress.ip_network(f"{address}/64", strict=False))
    return host
```

### 7. Fix the smaller bugs

- Remove the second `/reorder` endpoint.
- Build the paths in `system_config.py` from `UPLOAD_FOLDER` and a `PLACEHOLDER_FOLDER` setting.
- Replace `on_event` with a `lifespan` handler. Run the prune with `await asyncio.to_thread(...)`,
  keep its task, and cancel it at shutdown.
- Correct "cents" to "whole lei" in the schemas.

### 8. Clear out the clutter

- Update the README's badge and project structure.
- Delete or move into `docs/archive/` the root leftovers, `plans/`, `db/migrations/` and
  `db/schema.sql`. Keep one AI rules folder, and name documents after their subject.
- Use one MySQL driver for both the app and Alembic, move `debugpy` to a development requirements
  file, and replace `passlib` with `argon2-cffi`, which it already uses underneath.
- Make one workflow with both a `push` and a `workflow_dispatch` trigger.
- Pick one language for identifiers in new code. Renaming the existing columns and fields is not
  worth the churn, but the API's public names can be listed in one place with their meaning.

## What would make it a 7

Suggestions 1 to 4. The first two close the remaining security gaps, and the linter and unit tests
stop the same problems from coming back.
