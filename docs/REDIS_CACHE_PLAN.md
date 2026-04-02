# Redis Cache Plan (Backend)

## Context / Goals
This project serves catalog/list data that is expensive to compute on every request due to:
1. DB reads + assembling nested response payloads.
2. Filesystem checks to compute image `image_versions` (paths) at serialization time.

We want to add Redis as a cache layer to reduce backend CPU + DB load.

Assumptions (based on current expectations):
- Traffic: a few dozen concurrent customers.
- Admins: at most ~3 concurrent admins.
- Writes: extremely rare.
- Most frequently occurring writes are order placement flows (and related order create/read calls).
- Read operations dominate; caching is expected to help most on customer-facing “catalog/list” reads.

Cache strategy:
- Prefer caching "whole responses" for the highest-ROI endpoints.
- Optionally add a second-layer cache for computed `image_versions` if needed later.
- No TTL for cached responses (values live until explicit invalidation on writes).
- Prevent cache stampedes using short-lived per-key locks.

## Whole Responses vs Computed `image_versions`

### Whole responses (recommended starting point)
Cache the entire JSON body returned by an API call.

Example:
- Request: `GET /api/v1/liste/12/products/ordered`
- Redis key: `cache:resp:v1:list_products_ordered:list_id=12:...`
- Value: the full JSON response body (as a JSON string or equivalent).

On a cache hit:
1. Backend reads the JSON from Redis.
2. Backend returns it directly.
3. Backend skips DB queries, loops, and filesystem checks entirely for that request.

Invalidation is required when underlying data changes.

### Computed `image_versions` (optional second layer)
Cache the computed mapping:
`{ original: "...", medium: "...", thumbnail: "..." }`

This computation currently happens repeatedly via filesystem checks in:
- `app/schemas/product_image.py` (computed `image_versions`)
- `app/schemas/category.py` (computed `image_versions`)
- list-building logic that also calls image-version helpers, e.g.:
  - `app/services/list_product.py`
  - `app/services/list_product_ordered.py`

Example:
- Cache entry key: `cache:imgver:v1:<image_path>`
- Cached value: the `{original, medium, thumbnail}` mapping.

On a cache hit:
1. Backend still assembles the response (DB + loops still happen).
2. But filesystem checks are avoided for each image.

This is typically a smaller win than whole-response caching, but can be valuable if:
- whole-response caching is too complex for some endpoints, or
- you still see CPU usage on cache misses.

## Endpoints to Cache (Whole Responses)

Start by caching the most expensive customer-facing reads:
1. `GET /api/v1/liste/{list_id}/products/ordered`
2. `GET /api/v1/liste/{list_id}/products`
3. `GET /api/v1/products/{product_id}`
4. `GET /api/v1/categories` (if the frontend uses it frequently)
5. `GET /api/v1/categories/{category_id}`

These are the ones most likely to benefit because the response payload is nested and image `image_versions` may require filesystem checks during serialization.

Optional follow-up endpoints (lower risk / smaller payloads):
- `GET /api/v1/unitati` and `GET /api/v1/unitati/{id}`
- `GET /api/v1/tipuri-livrare` and `GET /api/v1/tipuri-livrare/{id}`
- `GET /api/v1/orare-livrari` and `GET /api/v1/orare-livrari/{id}`
- `GET /api/v1/payment-types`
- `GET /api/v1/modalitati-plata` and `GET /api/v1/modalitati-plata/{id}`
- `GET /api/v1/detalii-business`
- `GET /api/v1/system/config`
- `GET /api/v1/system/next-delivery-date`

## Redis Key Naming
Use explicit namespaces and always include the API version.

Suggested keys:
- Whole response cache:
  - `cache:resp:v1:<route>:<path_params>:<query_hash>`
  - Examples:
    - `cache:resp:v1:list_products_ordered:list_id=12:query=none`
    - `cache:resp:v1:list_products:list_id=12:query=none`
    - `cache:resp:v1:product_detail:product_id=99:query=none`
    - `cache:resp:v1:category_detail:category_id=5:query=none`
    - `cache:resp:v1:categories_all:limit=100:offset=0&search=...`

- Computed image versions (optional second layer):
  - `cache:imgver:v1:<image_path>`

Implementation note:
- For query params, normalize by sorting the query string, then hash it (to keep keys short and stable).
- If an endpoint has no query params, use `query=none`.

## Cache Stampede Prevention (Recommended)
Even with a few dozen concurrent customers, key expiry / invalidation can cause a thundering herd:
many requests miss Redis simultaneously and all recompute.

Approach:
1. On cache miss for key `K`, attempt to acquire a short lock key:
   - `cache:lock:v1:<K>` (or `cache:lock:v1:<route>:<...hash...>`)
2. Lock acquisition should:
   - use `SET lock_key value NX EX <seconds>` semantics
   - have a very short expiry (e.g. 3-10 seconds)
3. If lock is acquired:
   - compute the response
   - `SET cache_key value` (no TTL for cached value per policy)
   - release lock (optional) or let expiry handle it
4. If lock is not acquired:
   - wait briefly and retry reading the cache key
   - do this with a small backoff, e.g. up to 2-3 retries

Policy on cached value TTL:
- Per your preference: no TTL on cached response values.
- Lock keys still need TTL; otherwise a crashed process could hold locks indefinitely.

## Invalidation on Writes (No TTL on Cached Responses)
Because you asked for “no cache TTL anywhere”, correctness depends on invalidating affected cache entries when admin writes occur.

This plan uses invalidation-on-write rather than TTL-based expiry.

Implementation strategy:
- Identify the write endpoints (admin actions) that change:
  - list composition / ordering / stock shown in list payloads
  - product details and/or product images
  - category details and/or category images
- On those writes, delete affected cache keys immediately.

### Cache invalidation targets by write type

#### A) List composition / ordering / product availability inside list
Write endpoints that affect `GET /liste/{list_id}/products` and `GET /liste/{list_id}/products/ordered`:
- `PUT /api/v1/liste/{list_id}/products` (replace all products in list)
- `PATCH /api/v1/liste/{list_id}/products` (add multiple products)
- `PUT /api/v1/liste/{list_id}/positions` (bulk update positions)
- `PATCH /api/v1/liste/{list_id}/products/{product_id}` (update `stoc_produs` shown to customers)
- `POST /api/v1/liste/{list_id}/products/{product_id}` (add product)
- `DELETE /api/v1/liste/{list_id}/products/{product_id}` (remove product)
- Category ordering inside list:
  - `GET` endpoints depend on `liste_category` ordering; writes to category/list composition should invalidate:
    - `DELETE/POST` under `/api/v1/liste/{list_id}/categories/...`
    - `PATCH /api/v1/liste/{list_id}/categories/{category_id}/position`

Invalidate keys (whole responses):
- Delete:
  - all `cache:resp:v1:list_products:list_id=<id>:*`
  - all `cache:resp:v1:list_products_ordered:list_id=<id>:*`

Note:
- If your list endpoints depend on categories ordering, also invalidate `categories`-related cache only if you cache list-derived category details separately.

#### B) Product edits / product image changes
Write endpoints that affect `GET /api/v1/products/{product_id}`:
- `PATCH /api/v1/products/{product_id}`
- `DELETE /api/v1/products/{product_id}`
- Image endpoints:
  - `POST /api/v1/products/{product_id}/images`
  - `DELETE /api/v1/products/{product_id}/images/{image_id}`
  - `PUT /api/v1/products/{product_id}/images/{image_id}/primary`
  - `PUT /api/v1/products/{product_id}/images/{image_id}/position`
  - `PUT /api/v1/products/{product_id}/images/reorder`
- Staging upload:
  - `POST /api/v1/uploads/images` (indirect; only invalidates final cache once linked images are created/updated)

Invalidate keys:
- Delete:
  - `cache:resp:v1:product_detail:product_id=<id>:*`

If you also cache list payloads that include products:
- Correct invalidation would require knowing which lists reference that product.
- To keep this plan implementable, prefer:
  - TTL-less caching of list responses with invalidation driven by list write endpoints, OR
  - invalidate list caches opportunistically on product writes (trade-off: more invalidations).

Recommended for simplicity (given your rare-write assumption):
- Start TTL-less cache for list endpoints invalidated only on list write endpoints.
- Product edits invalidate product detail caches immediately; list caches refresh on their next list-related write invalidation.
- If this leads to stale list product details (e.g., name/image changes), you can later add reverse indexing product -> lists to invalidate precisely.

#### C) Category edits / category image changes
Write endpoints that affect:
- `GET /api/v1/categories` (list)
- `GET /api/v1/categories/{category_id}` (detail)
- List endpoints where categories are presented

Invalidate keys:
- Delete:
  - `cache:resp:v1:categories_all:*`
  - `cache:resp:v1:category_detail:category_id=<id>:*`
- And, if list endpoints embed category names/images, invalidate list caches for lists known to contain that category (reverse indexing), OR fall back to TTL-less list invalidation only on list composition writes.

### Implementation detail: how to delete many keys
You may need to invalidate whole namespaces by prefix.
Options:
- Use a maintained mapping from `<list_id>` to cached keys, and delete them directly (preferred).
- Or use Redis `SCAN` on key prefixes and delete matches (safe but can be heavier operationally).

Given this project’s small admin concurrency, maintained key tracking is feasible.

## Stock / Freshness Considerations
List responses include `stoc_produs` (stock/availability shown in list payloads).

Because you requested invalidation-on-write with no TTL:
- Ensure `PATCH /api/v1/liste/{list_id}/products/{product_id}` invalidates list caches for that `list_id`.

Order placement:
- Your order placement flow checks stock (in `app/services/order.py`), but based on the code reviewed so far, it does not appear to be a frequent stock decrement write into `stoc_produs`.
- If later you add stock decrement on order placement, you must also invalidate list caches accordingly on order create.

## Rollout Plan (Suggested)
1. Implement whole-response caching for:
   - `liste/{list_id}/products/ordered`
   - `liste/{list_id}/products`
   - `products/{product_id}`
   - `categories` (+ optional category detail)
2. Add invalidation hooks only for list write endpoints that affect stock, ordering, or membership.
3. Add stampede locks with short TTL for lock keys.
4. Measure CPU/DB load improvement.
5. If CPU is still high due to image version computation, add the optional `image_versions` cache second layer.

## Relevant Code Hotspots (for future implementation)
- Image version computation:
  - `app/schemas/product_image.py`
  - `app/schemas/category.py`
- List response assembly (nested payloads + per-image version logic):
  - `app/services/list_product.py`
  - `app/services/list_product_ordered.py`
- Stock validation in order placement:
  - `app/services/order.py`

