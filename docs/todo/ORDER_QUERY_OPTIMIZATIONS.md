# Order Query Optimizations

Two order-related query patterns that should be refactored for correctness and performance. Neither is a showstopper at low volume, but both will cause problems at scale and one has a logic bug.

---

## 1. Duplicate Order Detection — Full Table Scan in Python

**Severity: Medium** — Performance degrades linearly with order count per list.

### Current Code

`app/services/order.py` lines 469–499:

```python
def _is_duplicate_order(db: Session, order_in: OrderCreate) -> Optional[OrderModel]:
    normalized_name = _normalize_name_for_matching(order_in.nume_client)
    incoming_items_map = _items_to_quantity_map(order_in.items)

    candidates: List[OrderModel] = (
        db.query(OrderModel)
        .filter(
            and_(
                OrderModel.liste_id == order_in.liste_id,
                OrderModel.is_deleted == False,
                OrderModel.nume_client.isnot(None),
            )
        )
        .all()  # loads ALL non-deleted orders for this list into memory
    )

    for candidate in candidates:
        if _normalize_name_for_matching(candidate.nume_client) != normalized_name:
            continue
        existing_map = _existing_order_items_quantity_map(db, candidate.id)
        # ↑ executes an additional query per candidate with matching name
        if existing_map == incoming_items_map:
            return candidate
    return None
```

### Problems

1. **O(n) query** — Loads every non-deleted order for the list into memory. With 1000 orders per list, this transfers 1000 rows from MySQL on every new order creation.
2. **O(n) additional queries** — For each candidate with a matching normalized name, `_existing_order_items_quantity_map()` runs a separate `SELECT` to fetch that order's items. In the worst case (all orders from the same customer), this is 1 query per order.
3. **Python-side normalization** — Name normalization (diacritics, whitespace collapsing) is done in Python per row because there is no normalized column in the DB. The comment at line 483–485 acknowledges this: `"Since we don't store a normalized column, fetch candidates by same list and filter in Python."`.
4. **Runs in the request path** — All of this happens synchronously inside `create_order()` before the order is committed. The user waits.

### Proposed Fix

**Option A: Add a computed/stored column for normalized name** (recommended)

Add a `nume_client_normalized` column to the `comenzi` table, populated via an Alembic migration and maintained on insert/update (either in the service layer or via a MySQL generated column).

```sql
-- Alembic migration
ALTER TABLE comenzi
ADD COLUMN nume_client_normalized VARCHAR(255)
GENERATED ALWAYS AS (
    LOWER(TRIM(
        REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                nume_client,
                'ă', 'a'), 'â', 'a'), 'î', 'i'), 'ș', 's'), 'ț', 't'),
                'Ă', 'a'), 'Â', 'a'), 'Î', 'i'), 'Ș', 's'), 'Ț', 't')
    ))
) STORED;

CREATE INDEX idx_comenzi_duplicate_check
ON comenzi (liste_id, nume_client_normalized, is_deleted);
```

Then the duplicate check becomes:

```python
def _is_duplicate_order(db: Session, order_in: OrderCreate) -> Optional[OrderModel]:
    normalized_name = _normalize_name_for_matching(order_in.nume_client)
    incoming_items_map = _items_to_quantity_map(order_in.items)

    # Narrow candidates at DB level using the indexed normalized column
    candidates = (
        db.query(OrderModel)
        .filter(
            OrderModel.liste_id == order_in.liste_id,
            OrderModel.is_deleted == False,
            OrderModel.nume_client_normalized == normalized_name,
        )
        .all()
    )

    for candidate in candidates:
        existing_map = _existing_order_items_quantity_map(db, candidate.id)
        if existing_map == incoming_items_map:
            return candidate
    return None
```

This reduces the candidate set from "all orders in this list" to "orders with the same normalized name in this list" — typically 1–5 rows instead of hundreds/thousands.

**Option B: Hash-based dedup** (faster, less flexible)

Compute a deterministic hash of `(normalized_name, sorted_items)` and store it as a column. Duplicate check becomes a single indexed lookup.

```python
import hashlib, json

def _order_fingerprint(name: str, items: list) -> str:
    normalized = _normalize_name_for_matching(name)
    items_sorted = sorted(
        [(it.produse_id, it.cantitate_produs) for it in items],
        key=lambda x: x[0],
    )
    raw = json.dumps({"name": normalized, "items": items_sorted}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()
```

```sql
ALTER TABLE comenzi ADD COLUMN order_fingerprint CHAR(64);
CREATE UNIQUE INDEX idx_comenzi_fingerprint
ON comenzi (liste_id, order_fingerprint)
WHERE is_deleted = 0;  -- partial index (MySQL 8.0+ supports this via generated column trick)
```

Then duplicate check is a single query:

```python
existing = db.query(OrderModel).filter(
    OrderModel.liste_id == order_in.liste_id,
    OrderModel.is_deleted == False,
    OrderModel.order_fingerprint == fingerprint,
).first()
```

**Recommendation:** Option A is simpler and preserves the existing comparison semantics. Option B is faster at very high scale but requires maintaining the hash on every order insert/update.

---

## 2. Order Merge — Double Pagination Bug

**Severity: High (logic bug)** — Pagination produces incorrect/inconsistent results.

### Current Code

`app/services/order.py` lines 839–887:

```python
def list_orders_merged(db: Session, filters: Optional[OrderFilterParams] = None) -> List[Dict[str, Any]]:
    raw = list_orders(db=db, filters=filters)  # ← applies skip/limit at DB level
    if not raw:
        return []

    groups: Dict[Tuple[int, str], List[OrderModel]] = {}
    for o in raw:
        key = (o.liste_id, _normalize_name_for_matching(o.nume_client))
        groups.setdefault(key, []).append(o)

    merged_results: List[Dict[str, Any]] = []
    for _, group_orders in groups.items():
        if len(group_orders) == 1:
            # ... convert to dict ...
        else:
            merged_results.append(_merge_order_group(group_orders))

    merged_results.sort(key=lambda d: d['data_plasarii'], reverse=True)
    # ← applies skip/limit AGAIN on the already-paginated result
    skip = filters.skip if filters else 0
    limit = filters.limit if filters else 100
    return merged_results[skip: skip + limit]
```

### Problems

1. **Double pagination** — `list_orders()` at line 844 applies `skip` and `limit` at the SQL level (line 700: `query.offset(filters.skip).limit(filters.limit).all()`). Then lines 885–887 apply the same `skip` and `limit` again on the merged result. This means:
   - Page 1 (`skip=0, limit=20`): SQL returns rows 0–19, merge produces ≤20 groups, then Python slices `[0:20]` → probably correct by accident.
   - Page 2 (`skip=20, limit=20`): SQL returns rows 20–39, merge produces ≤20 groups, then Python slices `[20:20]` → **returns empty list** because the merged result has at most 20 items and we're skipping 20.

   In other words, **only page 1 ever returns data when merge is enabled**. All subsequent pages return empty.

2. **Merging on a page boundary splits groups** — If customer "Ion Popescu" has orders #10 and #25, and the page boundary falls between them (e.g., order #10 on page 1 and #25 on page 2), they will never be merged. The merge only sees orders within the current SQL page.

3. **Count mismatch** — The total count of merged results differs from the total count of raw orders, but there's no way for the frontend to know the correct total for pagination controls.

### Proposed Fix

**Option A: Remove DB-level pagination for merged queries** (simplest, fine for moderate scale)

When `merge_similar=true`, fetch all matching orders (no `skip`/`limit` at SQL level), merge in Python, then apply pagination on the merged result only:

```python
def list_orders_merged(db: Session, filters: Optional[OrderFilterParams] = None) -> List[Dict[str, Any]]:
    # Clone filters without pagination for the DB query
    unpaginated_filters = OrderFilterParams(
        **{
            k: v for k, v in (filters or OrderFilterParams()).__dict__.items()
            if k not in ("skip", "limit")
        },
        skip=0,
        limit=999999,  # or remove limit entirely
    )
    raw = list_orders(db=db, filters=unpaginated_filters)
    if not raw:
        return []

    # ... existing merge logic ...

    merged_results.sort(key=lambda d: d['data_plasarii'], reverse=True)
    skip = filters.skip if filters else 0
    limit = filters.limit if filters else 100
    return merged_results[skip: skip + limit]
```

**Tradeoff:** This loads all orders for the list into memory. For lists with thousands of orders, this could be slow. But it's correct.

**Option B: Materialized merge view** (better for scale, more complex)

Pre-compute merged groups in a background job (Celery task) and store results in a dedicated table or Redis cache. The API reads from the pre-computed view with standard SQL pagination.

This is a natural fit if Celery is introduced (see `CELERY_KAFKA_IMPLEMENTATION_PLAN.md` item 3).

**Option C: DB-level grouping** (best performance, most complex)

Move the grouping logic to SQL using `GROUP BY` on the normalized name column (requires the `nume_client_normalized` column from fix #1 above):

```sql
SELECT
    MIN(id) AS id,
    nume_client_normalized,
    liste_id,
    MAX(data_plasarii) AS data_plasarii,
    GROUP_CONCAT(id) AS merged_order_ids,
    COUNT(*) AS order_count
FROM comenzi
WHERE liste_id = :list_id AND is_deleted = 0
GROUP BY liste_id, nume_client_normalized
ORDER BY data_plasarii DESC
LIMIT :limit OFFSET :skip;
```

Then fetch full details only for the groups on the current page.

**Recommendation:** Start with Option A (correct and simple). If performance becomes an issue at scale, move to Option C, which requires the normalized column from fix #1. The two fixes complement each other.

---

## Summary

| Issue | Type | Impact | Fix complexity | Dependencies |
|-------|------|--------|---------------|--------------|
| Duplicate detection full scan | Performance | O(n) queries per order creation | Low–Medium | Alembic migration for normalized column |
| Order merge double pagination | Logic bug | Pages 2+ return empty when merge is enabled | Low | None (Option A) |
