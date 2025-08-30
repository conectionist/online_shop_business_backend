## Frontend Guide: Using the Orders (Comenzi) API

This guide shows how a frontend app can authenticate and interact with the Orders API. It uses the base path `/api/v1` and assumes the API is reachable at `http://localhost:8000`.

## ⚠️ BREAKING CHANGES - Frontend Updates Required

**This API has been updated with breaking changes that require frontend modifications:**

### New Required Fields
- `delivery_type_id`: **MANDATORY** - Must be provided when creating orders
- `payment_method_id`: **MANDATORY** - Must be provided when creating orders

### New Optional Fields
- `delivery_address`: Optional delivery address (max 150 chars)

### Frontend Migration Requirements
1. **Update order creation forms** to include delivery and payment method selection
2. **Handle new validation errors** for missing required fields
3. **Update order display components** to show new fields
4. **Implement delivery address logic** (frontend responsibility for home delivery validation)
5. **Update any hardcoded order structures** to include new fields

### Migration Strategy
- **No backward compatibility**: This is a breaking change by design
- **Frontend must be updated** before deploying backend changes
- **Test in staging environment** before production deployment
- **Coordinate deployment** of frontend and backend changes

### Authentication

**Order creation is public** (no authentication required) - customers can place orders without admin access.

**All other operations require admin authentication** - obtain an access token via `POST /api/v1/auth/login` and send it as `Authorization: Bearer <token>`.

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
  - `delivery_type_id`: filter by delivery method ID ⚠️ **NEW**
  - `payment_method_id`: filter by payment method ID ⚠️ **NEW**
  - `data_plasarii_start`, `data_plasarii_end`: ISO 8601 datetimes
  - `skip`, `limit`: pagination (defaults 0, 100)
  - `sort_by`: `data_plasarii` | `nume_client` | `liste_id` | `delivery_type_id` | `payment_method_id` (default `data_plasarii`) ⚠️ **NEW OPTIONS**
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
Endpoint: `POST /api/v1/orders` - **No authentication required**

**⚠️ BREAKING CHANGE**: This endpoint now requires `delivery_type_id` and `payment_method_id` fields.

Body:
```json
{
  "nume_client": "John Doe",
  "data_plasarii": "2025-01-01T10:00:00.000Z",
  "liste_id": 1,
  "delivery_type_id": 1,
  "payment_method_id": 1,
  "delivery_address": "Optional address for home delivery",
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

**Required Fields:**
- `nume_client`: Customer name (string, 1-50 chars)
- `data_plasarii`: Order placement datetime (ISO 8601)
- `liste_id`: Related list ID (integer > 0)
- `delivery_type_id`: Delivery method ID (integer > 0) ⚠️ **NEW REQUIRED**
- `payment_method_id`: Payment method ID (integer > 0) ⚠️ **NEW REQUIRED**

**Optional Fields:**
- `delivery_address`: Delivery address for home delivery (string, max 150 chars)
- `order_notes`: Order notes (string, max 500 chars)
- `items`: Array of order items

Example (fetch):
```javascript
async function createOrder(order) {
  const res = await fetch(`/api/v1/orders/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
- Updatable fields: `nume_client`, `order_notes`, `delivery_type_id`, `payment_method_id`, `delivery_address`
- The `liste_id` and `data_plasarii` are not meant to be changed.

**⚠️ BREAKING CHANGE**: You can now update delivery and payment methods after order creation.

**New Updatable Fields:**
- `delivery_type_id`: Change delivery method (must be available in the list)
- `payment_method_id`: Change payment method
- `delivery_address`: Update delivery address (required if switching to home delivery)

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

### New Business Logic & Validation Rules
- **`delivery_type_id`**: Must be a valid delivery type that is available for the selected list (check `GET /api/v1/liste/{list_id}/delivery-types`)
- **`payment_method_id`**: Must be a valid payment method from the system
- **`delivery_address`**: 
  - Optional field in the backend
  - **Frontend responsibility**: Should enforce that address is provided when home delivery is selected
  - Business rule: Home delivery (typically ID 3) requires a delivery address
- **Order updates**: Can now modify delivery and payment methods after creation

### Available Delivery Types and Payment Methods

#### Delivery Types (`GET /api/v1/tipuri-livrare/`)
Common delivery types include:
- **ID 1**: Ridicare de la sediu (Pickup from office)
- **ID 2**: Ridicare de la punct fix (Pickup from fixed point)  
- **ID 3**: Livrare la domiciliu (Home delivery)

#### Payment Methods (`GET /api/v1/modalitati-plata/`)
Common payment methods include:
- **ID 1**: Cash
- **ID 2**: Card
- **ID 3**: Transfer bancar (Bank transfer)
- **ID 4**: Transfer Revolut

#### List-Specific Delivery Types
Use `GET /api/v1/liste/{list_id}/delivery-types` to get delivery types available for a specific list.

### Example UI Flow
1) Admin logs in and stores the access token.
2) Fetch current orders with optional filters (now including delivery/payment method filters).
3) Create a new order with **required** delivery and payment method selection.
4) **NEW**: Optionally provide delivery address for home delivery orders.
5) Manage items: add, update quantity/price/unit, or remove.
6) Patch order metadata including delivery and payment method changes.
7) Delete orders when necessary.


