## Orders (Comenzi) API Implementation Plan — Fact-Based

This plan is derived strictly from the existing database schema in `db/schema.sql` to avoid assumptions.

### Database Facts (from db/schema.sql)
- Table `online_shop.comenzi`:
  - Columns: `id` (PK, INT, AI), `nume_client` (VARCHAR(50), NOT NULL), `data_plasarii` (DATETIME, NOT NULL), `liste_id` (INT, NOT NULL, FK → `liste.id`), `order_notes` (VARCHAR(500), NULL), `created_at` (TIMESTAMP, default now), `updated_at` (TIMESTAMP, default now on update)
  - Indexes: by `liste_id`, `data_plasarii`, `nume_client`
  - No status column, no soft-delete, no payment/delivery linkage, no customer contact fields beyond `nume_client`

- Table `online_shop.comenzi_au_produse`:
  - Composite PK: (`comenzi_id`, `produse_id`)
  - Columns: `comenzi_id` (FK → `comenzi.id`), `produse_id` (FK → `produse.id`), `pret_produs` (SMALLINT, NOT NULL), `cantitate_produs` (SMALLINT, NOT NULL), `unitati_id` (FK → `unitati.id`, NOT NULL)
  - No standalone row `id`

- Related schema details:
  - `liste_au_produse_ordered` includes `stoc_produs` per list-product; stock is managed at list-product level, not on `produse`.
  - No direct FKs from `comenzi` to payment/delivery tables.

Implications:
- No order status workflow in scope (no `status` field). Filtering will be by `data_plasarii`, `nume_client`, `liste_id`.
- Deletion is hard delete (no `is_deleted`).
- Order items must be addressed by `produse_id` (composite PK).
- Price is captured per item (`pret_produs`) at order time (snapshot).

---

### Phase 1: SQLAlchemy Models
- [ ] Add `app/models/order.py`:
  - [x] `Order` maps to `comenzi` with columns: `id`, `nume_client`, `data_plasarii`, `liste_id`, `order_notes`, `created_at`, `updated_at`.
  - [x] Relationship to `List` via `liste_id`.
  - [x] Relationship to `OrderItem` as `items`.

- [ ] Add `app/models/order_item.py`:
  - [x] `OrderItem` maps to `comenzi_au_produse` with composite PK (`comenzi_id`, `produse_id`).
  - [x] Columns: `pret_produs`, `cantitate_produs`, `unitati_id`.
  - [x] Relationships: `order` (→ `Order`), `product` (→ `Product`), `unit` (→ `Unitati`).

- [x] Update `app/models/__init__.py` to export `Order`, `OrderItem`.

Notes:
- [x] Use explicit `__table_args__` for composite PK, indexes as needed.

### Phase 2: Pydantic Schemas
- [ ] Add `app/schemas/order.py`:
  - [x] `OrderItemBase`: `produse_id`, `pret_produs`, `cantitate_produs` (>0), `unitati_id`.
  - [x] `OrderCreate`: `nume_client`, `data_plasarii`, `liste_id`, `order_notes`?, `items: list[OrderItemBase]` (optional).
  - [x] `OrderUpdate`: updatable fields: `nume_client`, `order_notes` (do not allow changing `data_plasarii` or `liste_id` by default; see Validation policy below).
  - [x] `OrderRead`: include `id`, timestamps, and nested `items`.
  - [x] `OrderFilterParams`: optional `nume_client` (substring), `liste_id`, date range (`data_plasarii_start`, `data_plasarii_end`), pagination (skip/limit), sort options.

- [x] Add `app/schemas/__init__.py` exports.

Validation policy:
- [x] Quantities must be positive; `pret_produs` must be ≥ 0. (Pydantic validators)
- [x] `unitati_id` must exist; `produse_id` must exist and not deleted. (validated in services)
- [ ] Optional: enforce item unit compatibility with product unit. (not implemented)

### Phase 3: Service Layer
- [x] Add `app/services/order.py` with functions:
  - [x] `create_order(db, order_in)`: create order and optional items atomically.
  - [x] `get_order_by_id(db, id)`: include items.
  - [x] `list_orders(db, filters, skip, limit, sort)`: filter by `nume_client` (ILIKE/LIKE), `liste_id`, `data_plasarii` range.
  - [x] `update_order(db, id, order_update)`: allow updates to `nume_client`, `order_notes`.
  - [x] `delete_order(db, id)`: hard delete (remove items then order).
  - [x] Items:
    - [x] `list_order_items(db, order_id)`
    - [x] `add_order_item(db, order_id, item_in)`
    - [x] `update_order_item(db, order_id, produse_id, item_update)`
    - [x] `remove_order_item(db, order_id, produse_id)`

Business rules:
- [x] Accept client-provided `pret_produs` but validate/fill from product/override if missing; document snapshot semantics.
- [x] Optional stock check against `liste_au_produse_ordered.stoc_produs` for (`liste_id`, `produse_id`).
- [x] Disallow changing `liste_id` after creation to keep FK semantics predictable.

### Phase 4: API Endpoints (FastAPI)
- [x] Add `app/api/endpoints/orders.py` with routes:
  - [x] `GET /api/v1/orders`: filters (nume_client, liste_id, date range), pagination, sorting.
  - [x] `POST /api/v1/orders`: create order (with optional embedded items).
  - [x] `GET /api/v1/orders/{id}`: order details with items.
  - [x] `PATCH /api/v1/orders/{id}`: update `nume_client`, `order_notes` only.
  - [x] `DELETE /api/v1/orders/{id}`: hard delete.
  - [x] `GET /api/v1/orders/{id}/products`: list items.
  - [x] `POST /api/v1/orders/{id}/products`: add item.
  - [x] `PATCH /api/v1/orders/{id}/products/{produse_id}`: update item (qty/price/unit).
  - [x] `DELETE /api/v1/orders/{id}/products/{produse_id}`: remove item.

- [x] Wire into `app/api/api.py`:
  - [x] `api_router.include_router(orders.router, prefix="/orders", tags=["orders"])`

Notes:
- [x] No status endpoints (no status column in schema).
- [x] Consistent error handling with `HTTPException`.

### Phase 5: Security
- [x] Require admin authentication for all write operations.
- [x] Read operations: default to admin-only (consistent with current backend posture). Adjust later if business rules change.

### Phase 6: Integration Tests (Dockerized)
- [ ] Add tests under `tests/integration/orders/`:
  - [x] Create order (with items) and read basics; auth enforcement.
  - [x] Create order with items using discovered product/unit IDs.
  - [x] Create order without items.
  - [x] Patch and delete order.
  - [x] Items CRUD lifecycle.
  - [x] Filters: by `nume_client` (substring), `liste_id`, date range. (pagination/sorting covered implicitly by service; skip dedicated tests)
  - [x] Auth: 401 for unauthenticated write requests.
  - [x] Validation: non-existent product/unit, invalid quantities/prices, attempts to change `liste_id`.
  - [ ] Optional test for stock check behavior if enabled. (keeping optional)

- [ ] Use existing scripts and compose files:
  - [ ] Build and run tests via Docker: `docker compose -f docker-compose.test.yml --env-file .env.test up --build -d` then `./run_api_integration_tests.sh`.

### Phase 7: Performance & Indexes
- [ ] Leverage existing indexes on `comenzi` for `data_plasarii`, `nume_client`, and `liste_id`.
- [ ] Ensure efficient queries in `list_orders` with filters and pagination.

### Phase 8: Documentation
- [ ] Update `docs/REST_API_IMPLEMENTATION_PLAN.md` to reference orders implementation status.
- [ ] Provide `docs/ORDERS_API.md` with endpoint examples and request/response schemas once implemented.

### Phase 9: Observability & Quality
- [ ] Add structured logging in services for create/update/delete and item operations.
- [ ] Ensure type hints and linter compliance across new files.

### Phase 10: Final Verification
- [ ] Rebuild containers and run full test suite (contract + integration) via Docker.
- [ ] Verify OpenAPI docs render correctly.


