## Frontend Guide: Using the Orders (Comenzi) API

This guide shows how a frontend app can authenticate and interact with the Orders API. It uses the base path `/api/v1` and assumes the API is reachable at `http://localhost:8000`.

### Authentication
- Obtain an access token via `POST /api/v1/auth/login` and send it as `Authorization: Bearer <token>` for all protected endpoints.

Example (fetch):
```javascript
async function login(username, password) {
  const res = await fetch(`/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.access_token; // store securely (e.g., httpOnly cookie or memory)
}
```

### List Orders (with filters, pagination, sorting)
Endpoint: `GET /api/v1/orders`
- Query params (all optional):
  - `nume_client`: substring match on customer name
  - `liste_id`: list id filter
  - `data_plasarii_start`, `data_plasarii_end`: ISO 8601 datetimes
  - `skip`, `limit`: pagination (defaults 0, 100)
  - `sort_by`: `data_plasarii` | `nume_client` | `liste_id` (default `data_plasarii`)
  - `sort_order`: `asc` | `desc` (default `desc`)

Example (fetch):
```javascript
async function listOrders(token, params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`/api/v1/orders/?${qs}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json(); // array of orders (items included)
}
```

### Create Order (with or without items)
Endpoint: `POST /api/v1/orders`

Body:
```json
{
  "nume_client": "John Doe",
  "data_plasarii": "2025-01-01T10:00:00.000Z",
  "liste_id": 1,
  "order_notes": "Optional notes",
  "items": [
    {
      "produse_id": 123,
      "pret_produs": 100,
      "cantitate_produs": 2,
      "unitati_id": 1
    }
  ]
}
```

Example (fetch):
```javascript
async function createOrder(token, order) {
  const res = await fetch(`/api/v1/orders/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(order)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json(); // created order
}
```

### Get Order by ID
Endpoint: `GET /api/v1/orders/{id}`
```javascript
async function getOrder(token, id) {
  const res = await fetch(`/api/v1/orders/${id}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

### Update Order (PATCH)
Endpoint: `PATCH /api/v1/orders/{id}`
- Updatable fields: `nume_client`, `order_notes`
- The `liste_id` and `data_plasarii` are not meant to be changed.

```javascript
async function patchOrder(token, id, payload) {
  const res = await fetch(`/api/v1/orders/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

### Delete Order
Endpoint: `DELETE /api/v1/orders/{id}`
```javascript
async function deleteOrder(token, id) {
  const res = await fetch(`/api/v1/orders/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok && res.status !== 204) throw new Error(await res.text());
}
```

### List Order Items
Endpoint: `GET /api/v1/orders/{id}/products`
```javascript
async function listOrderItems(token, orderId) {
  const res = await fetch(`/api/v1/orders/${orderId}/products`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

### Add Item to Order
Endpoint: `POST /api/v1/orders/{id}/products`
```javascript
async function addOrderItem(token, orderId, item) {
  const res = await fetch(`/api/v1/orders/${orderId}/products`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(item)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

### Update Item in Order
Endpoint: `PATCH /api/v1/orders/{id}/products/{produse_id}`
```javascript
async function updateOrderItem(token, orderId, productId, item) {
  const res = await fetch(`/api/v1/orders/${orderId}/products/${productId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(item)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

### Remove Item from Order
Endpoint: `DELETE /api/v1/orders/{id}/products/{produse_id}`
```javascript
async function removeOrderItem(token, orderId, productId) {
  const res = await fetch(`/api/v1/orders/${orderId}/products/${productId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!res.ok && res.status !== 204) throw new Error(await res.text());
}
```

### Notes & Constraints
- All write operations require a valid admin token.
- `produse_id` and `unitati_id` must be valid; quantities must be > 0.
- `pret_produs` is captured at order-time (snapshot). If omitted, backend may fill from product price depending on configuration.
- `liste_id` is immutable after creation.
- Filtering by date uses full ISO timestamps (UTC suggested).

### Example UI Flow
1) Admin logs in and stores the access token.
2) Fetch current orders with optional filters.
3) Create a new order (optionally with items) for the current `liste_id`.
4) Manage items: add, update quantity/price/unit, or remove.
5) Patch order metadata like `nume_client` or `order_notes`.
6) Delete orders when necessary.


