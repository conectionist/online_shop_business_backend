# MCP Server Implementation Plan — Online Shop Admin Query Tool

## 1. Overview

### What We're Building

An MCP (Model Context Protocol) server that allows an admin to ask natural-language questions about the online shop's data — and get answers by having an LLM (Claude) call the existing REST API on the admin's behalf.

**Example questions the admin could ask:**

- "What was the most expensive order ever placed?"
- "How many orders did we receive last week?"
- "Which customer has ordered the most times?"
- "Show me all products in the 'Lactate' category"
- "What delivery types are available?"
- "Which list has the most orders?"
- "What's the average order value for orders with home delivery?"

### Architecture

```
                               Docker Compose Network
                        ┌─────────────────────────────────────────────────┐
                        │                                                 │
┌──────────────┐  HTTP  │  ┌──────────────────┐  HTTP   ┌──────────────┐ │  ┌───────────┐
│ Claude       │  :3001 │  │  MCP Server      │  :8000  │  FastAPI     │ │  │           │
│ (Desktop/    │◄──────►│  │  (TypeScript)    │────────►│  Backend     │─┼─►│   MySQL   │
│  CLI/IDE)    │  MCP   │  │  Streamable HTTP │ cookies │  (existing)  │ │  │  Database  │
└──────────────┘        │  └──────────────────┘         └──────────────┘ │  └───────────┘
                        │        mcp-server                 backend      │
                        └─────────────────────────────────────────────────┘
```

**Key design decisions:**

- **Transport:** Streamable HTTP (stateless JSON mode — no SSE streaming, no sessions). The MCP server runs as a persistent Docker service and clients connect via `http://localhost:3001/mcp`
- **Deployment:** Docker Compose — the MCP server runs alongside the existing backend in the same compose network, communicating over internal DNS (`http://backend:8000`)
- **Language:** TypeScript (recommended by MCP best practices, strong SDK support, Zod validation)
- **Auth:** The MCP server authenticates once via `POST /auth/login`, stores the cookies in memory, and refreshes automatically when the access token expires
- **Read-only:** All tools are read-only (`readOnlyHint: true`). No data mutation through the MCP server.
- **Approach A:** Calls the existing REST API — no backend modifications required

---

## 2. Technology Stack

| Component         | Choice                              | Reason                                         |
|-------------------|-------------------------------------|-------------------------------------------------|
| Language          | TypeScript (Node.js)                | Best MCP SDK support, Zod schemas, type safety  |
| MCP SDK           | `@modelcontextprotocol/server`, `/node`, `/express` | Official MCP server SDK (split packages)  |
| Validation        | `zod` (v4, import via `zod/v4`)     | Runtime input validation, peer dep of SDK       |
| HTTP Client       | Built-in `fetch` (Node 18+)        | No extra deps, cookie management via headers    |
| Transport         | Streamable HTTP (stateless JSON)    | Natural fit for Docker, persistent service      |
| Containerization  | Docker + Docker Compose             | Runs alongside backend, shared network          |
| Build             | `tsc` (TypeScript compiler)         | Simple, no bundler needed                       |
| Runtime Image     | `node:24-alpine`                    | Small footprint, Active LTS                     |

---

## 3. Project Structure

The MCP server lives in a `mcp-server/` directory at the project root:

```
online_shop_business_backend/
├── app/                          # (existing backend)
├── docs/
│   └── MCP_SERVER_IMPLEMENTATION_PLAN.md   # (this file)
├── mcp-server/                   # NEW — MCP server project
│   ├── package.json
│   ├── tsconfig.json
│   ├── Dockerfile                # Multi-stage build (build → runtime)
│   ├── .dockerignore
│   ├── src/
│   │   ├── index.ts              # Entry point — server setup + streamable HTTP transport
│   │   ├── constants.ts          # Shared constants (CHARACTER_LIMIT, defaults)
│   │   ├── types.ts              # Shared TypeScript types
│   │   ├── services/
│   │   │   └── api-client.ts     # HTTP client with auth, cookie management, refresh logic
│   │   ├── schemas/
│   │   │   └── common.ts         # Shared Zod schemas (pagination, response format)
│   │   └── tools/
│   │       ├── orders.ts         # Order-related tools
│   │       ├── products.ts       # Product-related tools
│   │       ├── categories.ts     # Category-related tools
│   │       ├── lists.ts          # List-related tools
│   │       └── reference.ts      # Reference data tools (delivery types, payment methods, units, etc.)
│   └── dist/                     # Compiled JS output (built inside Docker)
├── docker-compose.mcp.yml        # Compose file for the MCP server (can be merged into existing compose)
└── ...
```

---

## 4. Authentication & Session Management

### 4.1 Login Flow

The MCP server authenticates as an admin when it first needs to make an API call (lazy initialization).

```
MCP Server starts (HTTP on :3001)
       │
       ▼
First tool call received via POST /mcp
       │
       ▼
POST /api/v1/auth/login
  Body: { "username": "...", "password": "..." }
       │
       ▼
Store cookies from response:
  - access_token  (httpOnly cookie, 30 min TTL)
  - refresh_token (httpOnly cookie, 7 day TTL)
       │
       ▼
Use cookies for all subsequent API calls
```

### 4.2 Token Refresh

The access token expires after 30 minutes. The MCP server handles this transparently:

```
API call returns 401 Unauthorized
       │
       ▼
POST /api/v1/auth/refresh
  (sends refresh_token cookie)
       │
       ▼
Store new cookies from response
       │
       ▼
Retry the original API call with new cookies
```

### 4.3 Cookie Management

Since we're using Node.js `fetch` (which doesn't natively manage cookies across requests like a browser), we'll implement a lightweight cookie jar:

- Parse `set-cookie` headers from login/refresh responses
- Store `access_token` and `refresh_token` values in memory
- Attach them as `Cookie: access_token=...; refresh_token=...` header on every request
- Update stored values whenever new `set-cookie` headers arrive

### 4.4 Configuration

Credentials, API URL, and server port are provided via environment variables:

| Variable          | Description                        | Example                      |
|-------------------|------------------------------------|------------------------------|
| `API_BASE_URL`    | Base URL of the FastAPI backend    | `http://backend:8000`        |
| `ADMIN_USERNAME`  | Admin username for authentication  | `admin`                      |
| `ADMIN_PASSWORD`  | Admin password for authentication  | `(secret)`                   |
| `MCP_PORT`        | Port the MCP server listens on     | `3001`                       |

Inside Docker Compose, `API_BASE_URL` uses the service name (`backend`) as the hostname, since both containers share the same Docker network. From outside Docker, the MCP server is exposed on `http://localhost:3001/mcp`.

---

## 5. MCP Tools — Complete Specification

### Naming Convention

All tools use the prefix `shop_` to avoid conflicts with other MCP servers. Names are `snake_case`.

---

### 5.1 Order Tools

#### `shop_list_orders`

**Purpose:** List and filter orders. This is the primary tool for answering order-related questions.

**Input Schema (Zod):**

| Parameter              | Type     | Required | Default   | Description                                      |
|------------------------|----------|----------|-----------|--------------------------------------------------|
| `customer_name`        | string   | no       | —         | Filter by customer name (substring match)        |
| `list_id`              | number   | no       | —         | Filter by list ID                                |
| `delivery_type_id`     | number   | no       | —         | Filter by delivery type                          |
| `payment_method_id`    | number   | no       | —         | Filter by payment method                         |
| `date_from`            | string   | no       | —         | Start date (ISO 8601)                            |
| `date_to`              | string   | no       | —         | End date (ISO 8601)                              |
| `include_deleted`      | boolean  | no       | false     | Include soft-deleted orders                      |
| `sort_by`              | enum     | no       | "data_plasarii" | One of: data_plasarii, nume_client, liste_id, delivery_type_id, payment_method_id |
| `sort_order`           | enum     | no       | "desc"    | "asc" or "desc"                                  |
| `limit`                | number   | no       | 100       | Max results (1–1000)                             |
| `offset`               | number   | no       | 0         | Pagination offset                                |

**Maps to:** `GET /api/v1/orders/`

**Query parameter mapping:**
- `customer_name` → `nume_client`
- `list_id` → `liste_id`
- `date_from` → `data_plasarii_start`
- `date_to` → `data_plasarii_end`
- `offset` → `skip`
- All others map 1:1

**Response:** Returns the list of orders as JSON. Each order includes its `items[]` array with `produse_id`, `pret_produs`, `cantitate_produs`, `unitati_id`.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

**Note on order totals:** The API does not return a pre-computed total. The LLM can compute it from the items: `total = Σ(pret_produs × cantitate_produs)` for each item. The tool description should mention this so the LLM knows how to calculate totals.

---

#### `shop_get_order`

**Purpose:** Get a single order by ID, including its items.

**Input Schema:**

| Parameter         | Type    | Required | Default | Description               |
|-------------------|---------|----------|---------|---------------------------|
| `order_id`        | number  | yes      | —       | The order ID              |
| `include_deleted`  | boolean | no       | false   | Include if soft-deleted   |

**Maps to:** `GET /api/v1/orders/{order_id}`

**Response:** Single order object with items.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

#### `shop_get_order_items`

**Purpose:** Get just the items/products for an order. Useful when the LLM already has the order metadata and only needs the line items.

**Input Schema:**

| Parameter   | Type   | Required | Description      |
|-------------|--------|----------|------------------|
| `order_id`  | number | yes      | The order ID     |

**Maps to:** `GET /api/v1/orders/{order_id}/products`

**Response:** Array of order items.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

### 5.2 Product Tools

#### `shop_list_products`

**Purpose:** List and filter products.

**Input Schema:**

| Parameter          | Type    | Required | Default | Description                       |
|--------------------|---------|----------|---------|-----------------------------------|
| `category_id`      | number  | no       | —       | Filter by category                |
| `include_deleted`   | boolean | no       | false   | Include soft-deleted products     |
| `limit`            | number  | no       | 100     | Max results (1–1000)              |
| `offset`           | number  | no       | 0       | Pagination offset                 |

**Maps to:** `GET /api/v1/products/`

**Query parameter mapping:**
- `offset` → `skip`
- All others map 1:1

**Response:** Array of products with `id`, `nume`, `cantitate`, `pret`, `description`, `category_id`, `unitati_id`, `is_deleted`, `images`.

**Note:** `pret` is the price in RON (whole number, integer). The tool description should clarify this for the LLM.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

#### `shop_get_product`

**Purpose:** Get a single product by ID.

**Input Schema:**

| Parameter         | Type    | Required | Default | Description               |
|-------------------|---------|----------|---------|---------------------------|
| `product_id`      | number  | yes      | —       | The product ID             |
| `include_deleted`  | boolean | no       | false   | Include if soft-deleted   |

**Maps to:** `GET /api/v1/products/{product_id}`

**Response:** Single product object.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

### 5.3 Category Tools

#### `shop_list_categories`

**Purpose:** List all product categories.

**Input Schema:**

| Parameter | Type   | Required | Default | Description          |
|-----------|--------|----------|---------|----------------------|
| `limit`   | number | no       | 100     | Max results (1–1000) |
| `offset`  | number | no       | 0       | Pagination offset    |

**Maps to:** `GET /api/v1/categories/`

**Query parameter mapping:**
- `offset` → `skip`

**Response:** Array of categories with `id`, `name`, `order_index`, `image_path`.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

#### `shop_get_category`

**Purpose:** Get a single category by ID.

**Input Schema:**

| Parameter     | Type   | Required | Description       |
|---------------|--------|----------|-------------------|
| `category_id` | number | yes      | The category ID   |

**Maps to:** `GET /api/v1/categories/{category_id}`

**Response:** Single category object.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

### 5.4 List Tools

#### `shop_list_lists`

**Purpose:** List all product lists (a "list" is a published product catalog for a specific date/period).

**Input Schema:**

| Parameter         | Type    | Required | Default | Description                    |
|-------------------|---------|----------|---------|--------------------------------|
| `include_deleted`  | boolean | no       | false   | Include soft-deleted lists     |
| `limit`           | number  | no       | 100     | Max results (1–1000)           |
| `offset`          | number  | no       | 0       | Pagination offset              |

**Maps to:** `GET /api/v1/liste/`

**Query parameter mapping:**
- `offset` → `skip`

**Response:** Array of lists with `id`, `data` (date), `is_current`, `is_published`, `mesaj_introducere`, `alte_detalii`, `orare_livrari_id`, `expiration_date`.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

#### `shop_get_list`

**Purpose:** Get a single list by ID.

**Input Schema:**

| Parameter  | Type   | Required | Description   |
|------------|--------|----------|---------------|
| `list_id`  | number | yes      | The list ID   |

**Maps to:** `GET /api/v1/liste/{list_id}`

**Response:** Single list object.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

#### `shop_get_list_products`

**Purpose:** Get all products associated with a specific list, including their stock/availability for that list.

**Input Schema:**

| Parameter  | Type   | Required | Description   |
|------------|--------|----------|---------------|
| `list_id`  | number | yes      | The list ID   |

**Maps to:** `GET /api/v1/liste/{list_id}/products`

**Response:** Array of list-product associations with product details and `stoc_produs` (stock/availability).

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

### 5.5 Reference Data Tools

#### `shop_list_delivery_types`

**Purpose:** List all available delivery types.

**Input Schema:** None (no parameters).

**Maps to:** `GET /api/v1/tipuri-livrare/`

**Response:** Array of delivery types with `id`, `denumire`, `description`, `order_index`.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

#### `shop_list_payment_methods`

**Purpose:** List all available payment methods.

**Input Schema:** None.

**Maps to:** `GET /api/v1/modalitati-plata/`

**Response:** Array of payment methods with `id`, `name`, `description`.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

#### `shop_list_payment_types`

**Purpose:** List all payment types (cash, card, etc.).

**Input Schema:** None.

**Maps to:** `GET /api/v1/payment-types/`

**Response:** Array of payment types with `id`, `name`, `description`.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

#### `shop_list_units`

**Purpose:** List all units of measurement (kg, L, buc, etc.).

**Input Schema:** None.

**Maps to:** `GET /api/v1/unitati/`

**Response:** Array of units with `id`, `denumire`.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

#### `shop_get_business_details`

**Purpose:** Get business details including delivery tax.

**Input Schema:** None.

**Maps to:** `GET /api/v1/detalii-business/`

**Response:** Business details object.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

#### `shop_get_system_config`

**Purpose:** Get system configuration (image placeholders, defaults, etc.).

**Input Schema:** None.

**Maps to:** `GET /api/v1/system/config`

**Response:** System config object.

**Annotations:** `readOnlyHint: true`, `destructiveHint: false`, `openWorldHint: false`

---

## 6. Implementation Details

### 6.1 API Client (`services/api-client.ts`)

This is the core HTTP client that all tools use. Responsibilities:

```typescript
class ApiClient {
  private baseUrl: string;
  private username: string;
  private password: string;
  private accessToken: string | null;
  private refreshToken: string | null;

  // Lazy login — called automatically on first request
  async login(): Promise<void>;

  // Refresh the access token using the refresh token
  async refresh(): Promise<void>;

  // Generic request method with auto-auth and auto-refresh
  async request<T>(method: string, path: string, params?: Record<string, string>): Promise<T>;

  // Parse set-cookie headers and store token values
  private parseCookies(headers: Headers): void;
}
```

**Auto-refresh logic in `request()`:**

```
1. If not logged in → call login()
2. Make the API request with Cookie header
3. If response is 401:
   a. Call refresh()
   b. Retry the original request (once)
   c. If still 401 → call login() again, retry
4. If response is not ok → throw descriptive error
5. Parse and return JSON body
```

### 6.2 Tool Response Format

All tools return **text content** formatted as JSON. The tool descriptions include enough context for the LLM to interpret the data (field meanings, price units, etc.).

```typescript
// Successful response
return {
  content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
};

// Error response
return {
  content: [{ type: "text", text: `Error: ${message}` }],
  isError: true
};
```

### 6.3 Pagination Pattern

Tools that list resources follow a consistent pagination pattern:

```typescript
// Input schema includes:
limit: z.number().min(1).max(1000).default(100).describe("Maximum number of results to return"),
offset: z.number().min(0).default(0).describe("Number of results to skip (for pagination)"),

// The response includes pagination metadata:
{
  "data": [...],        // The actual records
  "count": 42,          // Number of records in this response
  "total": 150,         // Total records matching the filter (if available from API)
  "has_more": true,     // Whether more records exist beyond this page
  "next_offset": 100    // Offset to use for the next page
}
```

**Note:** The existing API returns arrays directly (no envelope). The MCP tool wraps the response in this envelope to help the LLM paginate. `has_more` is inferred: if the API returned exactly `limit` records, there are probably more.

### 6.4 Character Limit

To prevent overwhelming the LLM context window, responses are truncated at **25,000 characters**. If truncation occurs, a message is appended:

```
... (response truncated at 25,000 characters. Use pagination with limit/offset to fetch smaller batches)
```

### 6.5 Error Handling

All API errors are caught and returned as actionable MCP error messages:

| HTTP Status | MCP Error Message                                                                  |
|-------------|------------------------------------------------------------------------------------|
| 400         | `"Bad request: {detail}. Check your parameters and try again."`                    |
| 401         | `"Authentication failed. The MCP server could not log in. Check credentials."`     |
| 403         | `"Forbidden. The admin account does not have permission for this action."`          |
| 404         | `"Not found: {entity} with ID {id} does not exist."`                               |
| 422         | `"Validation error: {detail}. Check parameter types and constraints."`             |
| 429         | `"Rate limited. Too many requests — wait before retrying."`                        |
| 500         | `"Server error. The API returned an internal error. Try again later."`             |

---

## 7. Tool Descriptions for LLM Discoverability

Tool descriptions are critical — they tell the LLM **when** and **how** to use each tool. Here are the planned descriptions:

### `shop_list_orders`
> List and filter orders from the online shop. Supports filtering by customer name, list ID, delivery type, payment method, and date range. Results include order items (products). To compute an order's total: sum(pret_produs × cantitate_produs) for each item. Prices (pret_produs) are in RON (integer, whole number). Supports pagination via limit/offset and sorting.

### `shop_get_order`
> Get a single order by its ID, including all order items (products with prices and quantities). To compute the order total: sum(pret_produs × cantitate_produs) for each item. Prices are in RON (integer).

### `shop_get_order_items`
> Get the line items (products) for a specific order. Each item has produse_id, pret_produs (price in RON, integer), cantitate_produs (quantity), and unitati_id (unit of measurement).

### `shop_list_products`
> List products in the shop catalog. Can filter by category_id. Each product has a price (pret) in RON (integer), a unit of measurement (unitati_id), and belongs to a category (category_id). Use shop_list_categories and shop_list_units to resolve IDs to names.

### `shop_get_product`
> Get a single product by ID. Returns full product details including name (nume), price (pret, in RON integer), description, category, unit, and images.

### `shop_list_categories`
> List all product categories. Each category has an id, name, and order_index. Use category IDs to filter products with shop_list_products.

### `shop_get_category`
> Get a single product category by ID.

### `shop_list_lists`
> List all product lists. A "list" is a published product catalog for a specific date/period (like a weekly menu). Each list has a date, publication status, and optional delivery schedule. Orders reference a list via liste_id.

### `shop_get_list`
> Get a single product list by ID. Returns list details including date, publication status, delivery schedule, and introductory message.

### `shop_get_list_products`
> Get all products associated with a specific list, including their stock/availability (stoc_produs) for that list.

### `shop_list_delivery_types`
> List all delivery types (e.g., home delivery, pickup). Each has an id, name (denumire), and description.

### `shop_list_payment_methods`
> List all payment methods configured in the shop. Each has an id, name, and description.

### `shop_list_payment_types`
> List all payment types (e.g., cash, card). These are the base types that payment methods belong to.

### `shop_list_units`
> List all units of measurement (e.g., kg, L, buc). Used to interpret product quantities and order item quantities.

### `shop_get_business_details`
> Get business details including delivery tax (used to compute full order totals when delivery address is present), business name, address, and tax information.

### `shop_get_system_config`
> Get system configuration including image placeholder paths, default category ID, and max image upload size.

---

## 8. Implementation Steps

### Step 1: Project Scaffolding

1. Create `mcp-server/` directory
2. Initialize `package.json` with dependencies:
   - `@modelcontextprotocol/server` (core MCP server, `McpServer` class)
   - `@modelcontextprotocol/node` (Node.js streamable HTTP transport)
   - `@modelcontextprotocol/express` (Express app helper for MCP)
   - `zod` (v4, peer dependency of the SDK)
3. Create `tsconfig.json` with strict mode
4. Create `Dockerfile` (multi-stage build)
5. Create `.dockerignore`

### Step 2: API Client

1. Implement `ApiClient` class in `services/api-client.ts`
2. Cookie parsing and storage
3. Login, refresh, and auto-retry logic
4. Generic `request()` method with query parameter support

### Step 3: Shared Schemas & Constants

1. Define pagination schema (reused across list tools)
2. Define `CHARACTER_LIMIT` constant
3. Define response helper functions

### Step 4: Implement Tools (in order of priority)

**Priority 1 — Core query tools:**
1. `shop_list_orders` (most complex, most useful)
2. `shop_get_order`
3. `shop_get_order_items`
4. `shop_list_products`
5. `shop_get_product`

**Priority 2 — Context tools (needed to interpret IDs in order/product data):**
6. `shop_list_categories`
7. `shop_get_category`
8. `shop_list_units`
9. `shop_list_delivery_types`
10. `shop_list_payment_methods`
11. `shop_list_payment_types`

**Priority 3 — Supplementary tools:**
12. `shop_list_lists`
13. `shop_get_list`
14. `shop_get_list_products`
15. `shop_get_business_details`
16. `shop_get_system_config`

### Step 5: Server Entry Point (Streamable HTTP)

1. Create `index.ts` with `McpServer` initialization
2. Register all tools
3. Set up streamable HTTP transport in **stateless JSON mode** (no SSE, no sessions):
   ```typescript
   import { createMcpExpressApp } from "@modelcontextprotocol/express";
   import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
   import { McpServer } from "@modelcontextprotocol/server";
   import type { Request, Response } from "express";
   import * as z from "zod/v4";

   // Factory function — creates a fresh server+tools for each request (stateless)
   function createServer(): McpServer {
     const server = new McpServer({
       name: "online-shop-mcp",
       version: "1.0.0",
     });
     // ... register all tools on server ...
     return server;
   }

   const app = createMcpExpressApp();

   app.post("/mcp", async (req: Request, res: Response) => {
     const server = createServer();
     try {
       const transport = new NodeStreamableHTTPServerTransport({
         sessionIdGenerator: undefined,  // stateless mode
       });
       await server.connect(transport);
       await transport.handleRequest(req, res, req.body);
       res.on("close", () => {
         transport.close();
         server.close();
       });
     } catch (error) {
       if (!res.headersSent) {
         res.status(500).json({
           jsonrpc: "2.0",
           error: { code: -32603, message: "Internal server error" },
           id: null,
         });
       }
     }
   });

   // GET and DELETE must return 405 Method Not Allowed
   app.get("/mcp", (_req: Request, res: Response) => {
     res.writeHead(405).end(JSON.stringify({
       jsonrpc: "2.0",
       error: { code: -32000, message: "Method not allowed." },
       id: null,
     }));
   });

   app.delete("/mcp", (_req: Request, res: Response) => {
     res.writeHead(405).end(JSON.stringify({
       jsonrpc: "2.0",
       error: { code: -32000, message: "Method not allowed." },
       id: null,
     }));
   });

   const port = parseInt(process.env.MCP_PORT || "3001");
   app.listen(port, () => {
     console.log(`MCP server listening on port ${port}`);
   });
   ```
4. **Stateless mode** (`sessionIdGenerator: undefined`): a **new `McpServer` and transport are created for every request**, ensuring complete isolation. No session tracking, no SSE streaming. The server and transport are cleaned up via `res.on("close", ...)`. This is simpler to scale and fits the Docker model well.

### Step 6: Docker Setup

1. Create `mcp-server/Dockerfile`:
   ```dockerfile
   # -- Build stage --
   FROM node:24-alpine AS build
   WORKDIR /app
   COPY package.json package-lock.json ./
   RUN npm ci
   COPY tsconfig.json ./
   COPY src/ ./src/
   RUN npm run build

   # -- Runtime stage --
   FROM node:24-alpine
   WORKDIR /app
   COPY package.json package-lock.json ./
   RUN npm ci --omit=dev
   COPY --from=build /app/dist ./dist
   EXPOSE 3001
   CMD ["node", "dist/index.js"]
   ```

2. Create `docker-compose.mcp.yml` at the project root:
   ```yaml
   services:
     mcp-server:
       build:
         context: ./mcp-server
         dockerfile: Dockerfile
       ports:
         - "3001:3001"
       environment:
         API_BASE_URL: http://backend:8000
         ADMIN_USERNAME: ${ADMIN_USERNAME}
         ADMIN_PASSWORD: ${ADMIN_PASSWORD}
         MCP_PORT: "3001"
       depends_on:
         - backend
       restart: unless-stopped
   ```

   This can be used standalone (`docker compose -f docker-compose.mcp.yml up`) or merged into an existing compose file that already defines the `backend` service.

### Step 7: Build & Test

1. Build the Docker image: `docker compose -f docker-compose.mcp.yml build`
2. Start the stack: `docker compose -f docker-compose.mcp.yml up`
3. Verify the MCP endpoint responds: `curl -X POST http://localhost:3001/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'`
4. Test with MCP Inspector: `npx @modelcontextprotocol/inspector --transport http http://localhost:3001/mcp`
5. Test each tool individually against the running backend
6. Test the auto-refresh flow (let access token expire, verify seamless refresh)

### Step 8: Client Configuration

#### Claude Desktop / Claude CLI

Add to `~/.claude.json` (or Claude Desktop settings):

```json
{
  "mcpServers": {
    "online-shop": {
      "type": "streamable-http",
      "url": "http://localhost:3001/mcp"
    }
  }
}
```

No credentials in the client config — they live in the Docker environment, not on the client side.

#### Alternative: VS Code / Continue / other MCP clients

Any MCP client that supports streamable HTTP transport can connect to `http://localhost:3001/mcp`.

---

## 9. Example Query Walkthroughs

### "What was the most expensive order ever placed?"

The LLM would:

1. Call `shop_list_orders` with `limit: 1000` (or paginate through all orders)
2. For each order, compute `total = Σ(item.pret_produs × item.cantitate_produs)`
3. Find the max total
4. Report the order ID, customer name, date, and total

### "How many orders did we get last week?"

1. Call `shop_list_orders` with `date_from: "2026-02-02T00:00:00Z"`, `date_to: "2026-02-08T23:59:59Z"`, `limit: 1`
2. The response count/total tells the LLM how many orders matched

### "Which customer has ordered the most?"

1. Call `shop_list_orders` with a high `limit` (paginate if needed)
2. Group by `nume_client`, count occurrences
3. Report the top customer

### "Show me all products in category 'Lactate'"

1. Call `shop_list_categories` to find the category ID for "Lactate"
2. Call `shop_list_products` with `category_id: <id>`
3. Return the product list

### "What's the average order value for home delivery orders?"

1. Call `shop_list_delivery_types` to find the home delivery type ID
2. Call `shop_list_orders` with `delivery_type_id: <id>`, paginate through all
3. Compute each order's total from items
4. Calculate the average

---

## 10. Limitations & Future Improvements

### Current Limitations (Approach A)

| Limitation                          | Impact                                              | Mitigation                              |
|-------------------------------------|-----------------------------------------------------|-----------------------------------------|
| No server-side aggregation          | "Most expensive order" requires fetching all orders  | Paginate and compute client-side        |
| No full-text search on products     | Can only filter by category, not by name             | LLM fetches all and filters in-context  |
| Order totals not pre-computed       | Each order's total must be computed from line items   | LLM computes from items array           |
| Large datasets may be slow          | Fetching 1000+ orders requires multiple API calls    | Use filters to narrow down first        |
| No revenue/analytics aggregation    | No "total revenue this month" in a single call       | LLM aggregates from order data          |

### Future Improvements (Approach B — when needed)

If Approach A proves too slow or limited for common queries, add targeted analytics endpoints to the backend:

1. `GET /api/v1/analytics/orders/summary` — order count, total revenue, avg order value by date range
2. `GET /api/v1/analytics/orders/top-customers` — top N customers by order count or total spend
3. `GET /api/v1/analytics/orders/top-orders` — top N orders by total value
4. `GET /api/v1/analytics/products/popular` — most ordered products

Each new analytics endpoint would get a corresponding MCP tool, making those queries single-call operations.

---

## 11. Security Considerations

- **Credentials:** Admin username/password stored as Docker environment variables (via `.env` file or secrets), never hardcoded in source
- **Network exposure:** The MCP server port (3001) is only published to `localhost` by default (`127.0.0.1:3001:3001`). It should **not** be exposed to the public internet. If deployed on a remote server, use a reverse proxy with authentication or restrict access via firewall rules
- **No MCP-level auth:** The MCP protocol itself does not authenticate clients in this setup. Anyone who can reach `localhost:3001` can call the tools. This is acceptable for local development; for production, add a reverse proxy with auth or restrict the port binding
- **Internal network:** The MCP server talks to the backend over Docker's internal network (`http://backend:8000`). This traffic never leaves the Docker host
- **Read-only:** All tools are explicitly read-only. No write/delete/update tools exist
- **Token storage:** Tokens are held in memory only, cleared when the container restarts
- **No credential logging:** Passwords and tokens must never appear in logs or error messages
- **Rate limiting:** The MCP server respects the backend's rate limits. Login attempts are limited to avoid lockout
- **Container security:** The Docker image uses `node:24-alpine` (minimal attack surface), runs as non-root (can be enforced with `USER node` in the Dockerfile), and has no unnecessary packages

---

## 12. Docker & Deployment Details

### 12.1 Dockerfile (`mcp-server/Dockerfile`)

Multi-stage build for minimal image size:

```dockerfile
# ── Build stage ──────────────────────────────────────────
FROM node:24-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

# ── Runtime stage ────────────────────────────────────────
FROM node:24-alpine
WORKDIR /app

# Run as non-root for security
RUN addgroup -S mcp && adduser -S mcp -G mcp
USER mcp

COPY --from=build /app/package.json /app/package-lock.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "fetch('http://localhost:3001/mcp', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({jsonrpc:'2.0',method:'tools/list',id:1})}).then(r=>{if(!r.ok)throw Error();process.exit(0)}).catch(()=>process.exit(1))"

CMD ["node", "dist/index.js"]
```

### 12.2 Docker Compose (`docker-compose.mcp.yml`)

```yaml
services:
  mcp-server:
    build:
      context: ./mcp-server
      dockerfile: Dockerfile
    ports:
      - "127.0.0.1:3001:3001"    # localhost only — not exposed to network
    environment:
      API_BASE_URL: http://backend:8000
      ADMIN_USERNAME: ${ADMIN_USERNAME}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD}
      MCP_PORT: "3001"
    depends_on:
      backend:
        condition: service_healthy  # wait for backend to be ready (if it has a healthcheck)
    restart: unless-stopped
    networks:
      - shop-network

  # Reference to existing backend service — if you already have a compose file
  # for the backend, merge this file into it or use `docker compose -f docker-compose.yml -f docker-compose.mcp.yml up`
  backend:
    # ... your existing backend service definition ...
    networks:
      - shop-network

networks:
  shop-network:
    driver: bridge
```

**Usage with an existing compose file:**

```bash
# If the backend already has its own docker-compose.yml:
docker compose -f docker-compose.yml -f docker-compose.mcp.yml up --build

# Or standalone (if backend is defined in the same file):
docker compose -f docker-compose.mcp.yml up --build
```

### 12.3 `.dockerignore` (`mcp-server/.dockerignore`)

```
node_modules/
dist/
*.md
.env
.env.*
.git
```

### 12.4 Environment Variables

Create a `.env` file at the project root (git-ignored) for Docker Compose:

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secret-password
```

Docker Compose automatically reads `.env` in the same directory and interpolates `${ADMIN_USERNAME}` and `${ADMIN_PASSWORD}`.

### 12.5 Development Workflow

```bash
# Build and start
docker compose -f docker-compose.mcp.yml up --build

# Rebuild after code changes
docker compose -f docker-compose.mcp.yml up --build mcp-server

# View logs
docker compose -f docker-compose.mcp.yml logs -f mcp-server

# Stop
docker compose -f docker-compose.mcp.yml down

# Quick test — list available tools
curl -s -X POST http://localhost:3001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' | jq .
```

### 12.6 Streamable HTTP Transport — Stateless Mode

The MCP server uses **stateless JSON** mode (not SSE/streaming):

- Each MCP request is an independent `POST /mcp` with a JSON-RPC body
- The server responds with a JSON-RPC result (not a stream)
- No session IDs, no server-side state between requests
- This means the server can be restarted/redeployed without breaking client sessions
- Multiple replicas could be run behind a load balancer if needed (though unlikely necessary for an admin tool)

**Why stateless?** Simpler to operate in Docker — no sticky sessions, no state to lose on restart, no SSE connection management. The only state is the API client's auth cookies, which are re-established automatically on first request after restart.
