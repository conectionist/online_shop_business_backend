# Admin Virtual Assistant — Implementation Plan

## 1. Overview

### What we're building

An AI assistant inside the admin panel. The admin describes a task in natural
language and the assistant does it, using tools that read the shop's data through
the existing backend services.

**First use case — WhatsApp orders.** A customer sends an order on WhatsApp in free
form ("buna, as vrea 2 paini cu secara si o focaccia cu usturoi, ridic vineri").
The admin pastes it into the assistant, which matches each line to a product in the
published list and returns a **draft order**. The admin checks the draft, fixes
anything, and confirms. Only then is the order saved.

**Other use cases — questions about the shop.** For example:

- "Ce a comandat Maria Popescu săptămâna trecută?"
- "Which products sold out on the last three lists?"
- "How many orders with home delivery do we have for Friday?"

### Non-goals (v1)

- The assistant never writes to the database on its own. Tools that change data
  return proposals, and a person confirms them in the UI.
- No raw SQL tool.
- Not customer-facing. Admin panel only.

---

## 2. Key Decisions

### 2.1 No MCP server for the in-panel assistant

MCP is how *external* AI clients (Claude Desktop, Claude Code, Cursor, ...) get
access to tools. For an assistant inside our own admin panel, the backend runs the
AI loop itself using the model provider's **tool calling** (function calling):

1. Send the model the conversation and a list of tool definitions.
2. The model answers with a tool call, e.g. `get_list_products(list_id=57)`.
3. The backend runs it against the existing services and sends the result back.
4. Repeat until the model gives a final answer.

An MCP server in between would add a separate process and an extra network hop
without adding anything.

**Relation to `MCP_SERVER_IMPLEMENTATION_PLAN.md`:** that plan is a separate
TypeScript server that logs in with a stored admin password, for use from Claude
Desktop. With this plan, tools live in one Python registry inside the backend
(section 4.3). If we later want Claude Desktop access, the same registry can be
served over MCP from the backend (the official Python MCP SDK can serve over
Streamable HTTP and be mounted into the FastAPI app). The MCP plan then becomes a
thin layer instead of a separate project with its own copy of every tool.

### 2.2 Tools call services directly

Tools are Python functions that call `app/services/*` with the request's DB session.
They don't go through HTTP, and they don't need stored credentials: the assistant
endpoints are admin-only, so every tool call already runs on behalf of a logged-in
admin.

### 2.3 Recipes for frequent tasks, an agent for everything else

- **Recipe:** a fixed pipeline in code with a single model call. Used for WhatsApp
  orders: the code loads the list, the model only does the matching, the code
  validates. Fast, cheap, predictable, and works with small local models.
- **Agent:** the open-ended tool-calling loop. Used for one-off questions.

### 2.4 The model provider is swappable

A small adapter interface (section 4.6) with two implementations:

- **Hosted:** Anthropic API (Claude models).
- **Local:** a llama.cpp server (or Ollama) on our own hardware.

The choice is made with an evaluation set of real messages (section 7.3), not by
guessing.

---

## 3. Architecture

```
Admin panel (React)
  │  POST /api/v1/assistant/...   (admin cookie)
  ▼
FastAPI backend
  ├─ assistant endpoints ─► recipe or agent loop
  │                            │ tool calls
  │                            ▼
  │                       tool registry ─► existing services ─► MySQL
  │
  └─ provider adapter ─► Anthropic API
                     └─► llama.cpp server (LAN)
```

WhatsApp order flow:

```
WhatsApp text
  ─► POST /assistant/whatsapp-order/parse
  ─► OrderDraft (nothing saved)
  ─► admin reviews and edits in the UI
  ─► POST /orders/admin
  ─► create_order()  (same checks as customer orders)
```

---

## 4. Backend

### 4.1 Project structure

Follows the existing layering (`endpoints` → `services` → `models`):

```
app/
├── api/endpoints/
│   └── assistant.py              # NEW — assistant endpoints
├── schemas/
│   └── assistant.py              # NEW — OrderDraft, chat request/response, ...
└── services/
    ├── order.py                  # + collect_order_issues(), admin create path
    └── assistant/                # NEW
        ├── __init__.py
        ├── config.py             # env settings for the assistant
        ├── providers/
        │   ├── base.py           # ChatProvider interface + result types
        │   ├── anthropic.py      # Anthropic API implementation
        │   └── local.py          # llama.cpp / Ollama implementation
        ├── tools/
        │   ├── registry.py       # Tool definition + registry
        │   ├── lists.py          # published list, list products, delivery types
        │   ├── orders.py         # order search, customer lookup, draft_order
        │   ├── reference.py      # payment methods, units, categories
        │   └── statistics.py     # wrappers around services/statistics.py
        ├── matching.py           # name normalization + candidate matching
        ├── prompts.py            # system prompts and prompt layout
        ├── whatsapp_order.py     # the WhatsApp order recipe
        └── agent.py              # the tool-calling loop for chat
```

### 4.2 Endpoints

All endpoints use `Depends(get_current_admin_from_cookie)`.

| Method & path | Purpose |
|---|---|
| `GET /api/v1/assistant/status` | Is the assistant enabled, which provider, is it local (slow). The UI uses it to show or hide the feature. |
| `POST /api/v1/assistant/whatsapp-order/parse` | Body: `{ text, list_id?, received_at? }`. Returns an `OrderDraft`. Saves nothing. |
| `POST /api/v1/orders/admin` | Body: `OrderCreate`. Creates an admin-entered order. See below. |
| `POST /api/v1/assistant/chat` | Body: `{ conversation_id?, message }`. Runs the agent loop. Returns the reply, the tool calls made, and any drafts. |

**Why `POST /orders/admin` is needed.** The public `POST /orders` is limited to
`ORDER_RATE_LIMIT_MAX` orders per IP per window (default 10 per 24 h) and has no
admin exemption. An admin entering WhatsApp orders through it would be blocked
after 10. The admin endpoint:

- requires the admin cookie, and has no per-IP order limit;
- calls `create_order(db, order_in, source="Assistant")`, so price, stock,
  delivery and duplicate checks stay the same as for customer orders;
- decides whether to pass `background` (see open questions: should an
  admin-entered order send the "new order" push to admins?).

It is useful on its own too, for any order the admin types in by hand.

**Endpoint style.** Uvicorn runs with `--workers 1`. Provider calls can take seconds
(hosted) or minutes (local CPU), so the assistant endpoints must not block the
event loop: write them as plain `def` endpoints (FastAPI runs them in the
threadpool), like the rest of the API, or as `async def` with an async HTTP client.

### 4.3 Tool registry

One definition per tool, used by every provider (and later by MCP):

```python
@dataclass(frozen=True)
class Tool:
    name: str                      # "get_list_products"
    description: str               # written for the model: what it returns, when to use it
    input_model: type[BaseModel]   # Pydantic model; JSON schema via model_json_schema()
    handler: Callable[[Session, Admin, BaseModel], dict]
    read_only: bool = True
```

Rules for handlers:

- **Return compact data.** Only the fields the model needs. No images, no
  timestamps it doesn't need, no internal flags. Prices as lei (`12.00`), not cents.
- **Cap rows** (e.g. 50) and say in the result when the output was cut, so the
  model can narrow the query.
- **Errors become results**, not exceptions: `{"error": "List 99 not found"}`. The
  model can recover from a clear error message.
- **Log every call** (tool name, arguments, duration, row count) at INFO; message
  text and results at DEBUG only, since they contain customer data.

#### Tools for v1

| Tool | Wraps | Notes |
|---|---|---|
| `get_published_list` | `list.get_current_published_list` | id, delivery date, expiration, intro message |
| `get_list_products` | `list_product.get_list_products` | id, name, quantity + unit (e.g. `500 g`), price, stock, category. One line per product. |
| `search_products` | `matching.candidates` | Top matches for a free-text name, diacritics-insensitive |
| `list_delivery_types` | `list_delivery_type.get_list_delivery_types` | For a list; says which ones need an address |
| `list_payment_methods` | `modalitati_plata.get_modalitati_plata` | |
| `find_customer` | `order.list_orders` | Past orders by name or phone. `OrderFilterParams` has no phone filter yet — add one. |
| `search_orders` | `order.list_orders` | By list, date range, delivery/payment type, customer |
| `get_order` | `order.get_order_by_id` | With items and product names |
| `get_stats_overview` | `statistics.get_overview` | Period KPIs |
| `get_product_stats` | `statistics.get_product_stats` | Top products, never ordered, sold out |
| `get_customer_stats` | `statistics.get_customer_stats` | Top customers |
| `get_current_list_stats` | `statistics.get_current_list_stats` | |
| `draft_order` | `collect_order_issues` (4.5) | Builds and checks an order draft. Saves nothing. Lets the chat agent produce drafts too. |

### 4.4 Product matching (`matching.py`)

WhatsApp messages rarely have diacritics, and customers shorten names
("paine secara", "o japoneza", "focaccia usturoi").

- `normalize(s)`: lowercase, strip diacritics (Unicode NFKD, drop combining marks:
  `â ă î ș ț` → `a a i s t`), drop punctuation, collapse spaces.
- `candidates(text, products, k=3)`: score each product name against the text and
  return the top `k` with scores. Use `rapidfuzz` (`token_set_ratio`, fast, MIT
  license) or the standard library's `difflib` if we'd rather not add a dependency.

The recipe uses this to give the model a short candidate list per message line.
That helps a lot with small local models: picking from 3 candidates is much easier
than searching a list of 60.

### 4.5 Order checks without saving (`collect_order_issues`)

`create_order` stops at the first failed check by raising `HTTPException`. A draft
needs **all** problems at once, so the admin sees everything to fix.

Add to `app/services/order.py`:

```python
def collect_order_issues(db: Session, order_in: OrderCreate) -> list[OrderIssue]:
    """Run the same checks as create_order and return every problem found."""
```

It calls the existing helpers one by one (`_validate_foreign_keys`,
`_is_duplicate_order`, `_validate_list_open`, `_validate_delivery_method_availability`,
`_validate_delivery_address`, and `_check_stock` per item), catches each
`HTTPException`, and turns its `detail` (`error_code`, `message`, `product_id`, ...)
into an `OrderIssue`. `create_order` itself doesn't change, so the draft and the
real order always follow the same rules.

### 4.6 Provider adapter

```python
class ChatProvider(Protocol):
    def complete(
        self,
        system: str,
        messages: list[dict],
        tools: list[Tool] | None = None,
        output_schema: dict | None = None,   # JSON schema for structured output
    ) -> ProviderResult: ...

@dataclass
class ProviderResult:
    text: str | None
    tool_calls: list[ToolCall]      # id, name, arguments (dict)
    stop_reason: str
    usage: Usage                    # input/output tokens, for logging and cost
    raw_assistant_message: Any      # provider-specific; stored as-is in history
```

**Anthropic** (`anthropic` Python SDK):

- Tools: `messages.create(..., tools=[...])` with each tool's name, description and
  `input_schema` from the Pydantic model.
- Structured output for the recipe: `output_config={"format": {"type": "json_schema", "schema": ...}}`.
- Prompt caching: put `cache_control` on the stable prefix (instructions + product
  list), so repeat orders against the same list pay much less for input.
- Effort: set `output_config.effort` to `low` for the recipe; it's a simple task.
- Pass assistant messages back unchanged in the history (they can contain thinking
  blocks the API expects to get back as-is).
- Check `stop_reason` before reading content (`refusal`, `max_tokens`).
- Model-specific details change between releases. Check the API docs for the chosen
  model when implementing.

**Local** (llama.cpp `llama-server`, or Ollama):

- Both expose a chat-completions HTTP API with tool calling and JSON-schema
  constrained output. Constrained output matters a lot for small models: they
  can't return broken JSON.
- Use `httpx` (add it to `requirements.txt` explicitly).
- Keep the prompt prefix byte-identical between requests. llama-server reuses its
  cache for a matching prefix, so later orders only process the new message.
- Turn off "thinking" modes on models that have one (e.g. Qwen3); on a CPU it adds
  minutes.

### 4.7 The WhatsApp order recipe (`whatsapp_order.py`)

1. **Load context.** The list (`list_id` or the published one), its products
   (compact), its delivery types, the payment methods.
2. **Pre-match.** Split the message into lines and compute candidates for each
   (section 4.4).
3. **One model call** with structured output. Prompt layout, stable parts first so
   they can be cached:

   ```
   [instructions]            static
   [product list for list X] changes only when the list changes; sorted, no timestamps
   [delivery + payment ids]  static per list
   ─── cache boundary ───
   [candidate hints]         per message
   [the WhatsApp message]    in a delimited block, labeled as customer text, not instructions
   ```

   Instructions cover: use only `product_id`s from the list; `quantity` is the
   number of product units (1 kg of a 500 g bread = 2); mark doubtful lines `low`
   instead of guessing; leave fields `null` when the message doesn't say.

   Output schema:

   ```json
   {
     "customer_name": "string | null",
     "phone": "string | null",
     "delivery_address": "string | null",
     "delivery_type_id": "integer | null",
     "payment_method_id": "integer | null",
     "notes": "string | null",
     "lines": [
       {
         "raw": "2 paini cu secara",
         "product_id": 12,
         "quantity": 2,
         "confidence": "high | medium | low",
         "comment": "string | null"
       }
     ]
   }
   ```

4. **Check in code.** Every `product_id` is in the list, quantities are positive
   integers, then `collect_order_issues` for stock, delivery, address and
   duplicates. Compute line totals and the total from current prices.
5. **Return an `OrderDraft`:** the fields above plus product names and prices, line
   totals, total, `issues`, lines with no match, and `ready: bool` (no blocking
   issues). Nothing is saved.

### 4.8 The chat agent (`agent.py`)

- Loop: call the provider; if it asks for tools, run them (all calls from one
  response, results returned together), append the results, repeat.
- Limits: `ASSISTANT_MAX_TOOL_ITERATIONS` (e.g. 8), a total token budget, and a
  wall-clock timeout. When a limit is hit, return what we have and say so.
- Only read-only tools plus `draft_order`.
- **Conversation state** in Redis, keyed by `conversation_id`, with a TTL (e.g.
  2 h). It stores the full history, including tool results and provider-specific
  blocks, so the frontend only handles plain text. Redis is optional in this
  project (`app/core/redis.py` falls back when it's down): if it's unavailable, the
  chat works one question at a time and the UI says so.

### 4.9 Configuration

Added to `app/core/config.py` with the existing `get_optional_env_var` pattern, and
to `.env.example`:

| Variable | Default | Meaning |
|---|---|---|
| `ASSISTANT_ENABLED` | `false` | Feature switch |
| `ASSISTANT_PROVIDER` | `anthropic` | `anthropic` or `local` |
| `ASSISTANT_MODEL` | `claude-opus-5-5` | Model name for the provider. Pick the final one with the eval (section 7.3). |
| `ANTHROPIC_API_KEY` | — | Required for `anthropic` |
| `ASSISTANT_LOCAL_BASE_URL` | `http://llm:8080` | llama.cpp / Ollama server |
| `ASSISTANT_LOCAL_API_KEY` | — | Matches llama-server's `--api-key` |
| `ASSISTANT_REQUEST_TIMEOUT_SECONDS` | `300` | Local CPU models are slow |
| `ASSISTANT_MAX_TOOL_ITERATIONS` | `8` | Agent loop limit |
| `ASSISTANT_CONVERSATION_TTL_SECONDS` | `7200` | Chat history lifetime in Redis |

---

## 5. Frontend

### 5.1 Files

```
src/
├── types/assistant.ts                          # OrderDraft, OrderIssue, chat types
├── services/assistant.ts                       # API calls
├── hooks/useAssistant.ts                       # react-query mutations/queries
├── pages/admin/Assistant.tsx                   # route /admin/assistant
└── components/features/admin/assistant/
    ├── WhatsappOrderPanel.tsx                  # paste text → draft
    ├── OrderDraftReview.tsx                    # review/edit/confirm a draft
    └── ChatPanel.tsx                           # free-form questions (phase 3)
```

### 5.2 UI

- **Route** `/admin/assistant` in `App.tsx`, and an "Asistent" card on the admin
  `Dashboard.tsx` (where the other admin sections are linked). Hidden when
  `GET /assistant/status` says it's disabled.
- **Two tabs:** "Comandă din WhatsApp" and "Întreabă asistentul".
- **`OrderDraftReview`:**
  - customer name, phone, address, delivery type and payment method, pre-filled
    and editable;
  - one row per line: the original text, a product picker (the list's products),
    quantity, price, confidence badge (low = highlighted);
  - lines with no match shown with their original text and an empty picker;
  - issues from the backend (stock, address, duplicate, ...) next to the field or
    line they belong to;
  - total, then **Confirm** → `POST /orders/admin` → success message with a link to
    the order.
  - Reuse `AddProductModal` from `EditOrderForm.tsx` (move it to its own file).
- **Entry point from orders:** an "Importă din WhatsApp" button in
  `ListOrdersTab.tsx` that opens the WhatsApp panel with that list selected.

### 5.3 Waiting times

- The shared axios instance in `src/services/api.ts` has a **10 s timeout**.
  Assistant calls need a longer one per request (e.g. 120 s hosted, 300 s local).
- Show an elapsed-time counter while waiting. When `status.is_local` is true, also
  say it can take a minute or two.
- With a local model, move to streaming progress (Server-Sent Events: "reading the
  list...", "matching products...") — see phase 4. It also avoids proxy timeouts:
  a reverse proxy in front of the API (nginx defaults to a 60 s read timeout) would
  cut a silent request that runs for minutes.

---

## 6. Security & Privacy

- **Admin only.** Every assistant endpoint requires the admin cookie.
- **No direct writes.** The model can only read and draft. `POST /orders/admin`
  re-checks everything at confirm time, so a wrong or tampered draft can't skip
  the rules.
- **Prompt injection.** The WhatsApp text is untrusted. It goes in a delimited
  block marked as customer text. Since no tool writes anything, the worst case is a
  wrong draft that the admin sees before confirming.
- **Limit what tools return.** Row caps, compact fields. Statistics tools return
  aggregates, not phone numbers.
- **No secrets in prompts.** Tools get the DB session server-side; tokens and keys
  never reach the model.
- **Cost control.** Iteration limit, token budget, and a per-admin daily request
  cap.
- **Customer data with a hosted model.** Names, phones and addresses in WhatsApp
  messages are sent to the model provider. Under GDPR this needs a data processing
  agreement with the provider and a mention in the privacy policy. A local model
  keeps the data on our own hardware.
- **Local model server.** Never exposed to the internet. Bind it to the Docker
  network or LAN, and set `--api-key`.

---

## 7. Testing & Evaluation

### 7.1 Unit tests

- `normalize()` and `candidates()` (diacritics, abbreviations, word order).
- Tool registry: every tool's input schema is generated and valid.
- `collect_order_issues()`: stock, closed list, delivery type not on the list,
  missing address, duplicate.
- Recipe with a **fake provider** that returns canned JSON: bad `product_id`s are
  rejected, totals are right, issues are collected.

### 7.2 Integration tests

- Assistant endpoints with the fake provider: admin-only (401 without cookie),
  `parse` saves nothing, `POST /orders/admin` creates an order with the current
  prices and isn't blocked by the per-IP order limit.

### 7.3 Evaluation set (to choose the model and hardware)

- `tests/assistant_eval/cases/*.json`: about 20 real WhatsApp messages, each with a
  snapshot of the list products and the correct order. **Anonymize names, phones and
  addresses** before committing.
- `scripts/eval_assistant.py --provider ... --model ...`: runs every case and reports
  - per line: correct product and quantity (precision and recall);
  - customer fields correct;
  - time per case;
  - tokens and cost per case (hosted).
- Run it against a hosted model first to set the bar, then against local models on
  the candidate hardware. Pick the cheapest setup that scores well enough with a
  wait the admin accepts.

---

## 8. Implementation Phases

### Phase 0 — Preparation
- [ ] Collect ~20 real WhatsApp orders and their correct orders (anonymized).
- [ ] Decide the open questions in section 10.

### Phase 1 — Backend: WhatsApp orders
- [ ] `collect_order_issues()` in `services/order.py`
- [ ] `POST /api/v1/orders/admin`
- [ ] Phone filter in `OrderFilterParams`
- [ ] `services/assistant/`: config, provider interface, Anthropic provider
- [ ] `matching.py`
- [ ] Tool registry + read-only tools from 4.3
- [ ] WhatsApp recipe + `POST /assistant/whatsapp-order/parse` + `GET /assistant/status`
- [ ] Unit and integration tests
- [ ] Eval script and cases

### Phase 2 — Frontend: WhatsApp orders
- [ ] Types, service, hooks
- [ ] `/admin/assistant` page and Dashboard card
- [ ] `WhatsappOrderPanel` and `OrderDraftReview`
- [ ] "Importă din WhatsApp" button in `ListOrdersTab`
- [ ] Tests (vitest + msw)

### Phase 3 — Chat
- [ ] Agent loop with limits
- [ ] Conversation history in Redis
- [ ] `POST /assistant/chat`
- [ ] `ChatPanel`

### Phase 4 — Local model and extras
- [ ] Local provider (llama.cpp / Ollama)
- [ ] Run the eval on the candidate hardware (section 9.2)
- [ ] `llm` service in Docker Compose, or the server on a LAN machine
- [ ] Streaming progress (SSE) for both endpoints
- [ ] Optional: serve the tool registry over MCP (replaces the separate TypeScript
      server in `MCP_SERVER_IMPLEMENTATION_PLAN.md`)

---

## 9. Cost & Performance Estimates

Rough numbers to plan with. Measure with the eval before deciding.

### 9.1 Hosted (Anthropic list prices, October 2026)

Assumes a WhatsApp order is ~4k input and ~0.5k output tokens, and a chat
question with a few tool calls is ~25k input and ~1.5k output tokens. Thinking
tokens count as output. Prompt caching lowers the input part for repeat orders
against the same list.

| Model | Input / output, $ per 1M tokens | WhatsApp order | Chat question |
|---|---|---|---|
| Claude Opus 5.5 | 4.00 / 20.00 | ~2.6 ¢ | ~13 ¢ |
| Claude Sonnet 5.5 | 2.00 / 10.00 | ~1.3 ¢ | ~6.5 ¢ |
| Claude Haiku 5.5 | 0.10 / 0.50 | ~0.07 ¢ | ~0.3 ¢ |

Prices change; check the provider's pricing page before relying on these.

### 9.2 Local (CPU only)

On a CPU, reading the prompt is limited by the cores and writing the answer is
limited by RAM bandwidth (each output token reads the whole model). For the
assistant, reading the prompt is the slow part. Estimates for an 8B model at 4-bit
(~5 GB); a 4B model is roughly twice as fast:

| | i5-7400, DDR4-2400 dual-channel | i5-1135G7, dual-channel |
|---|---|---|
| Read a 4k-token prompt | 2–4 min | 1–1.5 min (less with the iGPU) |
| Write | 4–5 tokens/s | 7–10 tokens/s |
| WhatsApp order, same list already cached | 1–1.5 min | ~45 s |

Notes:

- The i5-1135G7 needs **two RAM sticks** (dual-channel). With one 16 GB stick it has
  half the bandwidth, which makes it slower than the i5-7400, and the Iris Xe GPU
  doesn't run in full mode.
- Its Iris Xe GPU can speed up prompt reading through llama.cpp's Vulkan or SYCL
  backends. It's a laptop chip and may slow down under long loads in a small case.
- Models to try (Q4_K_M): **Qwen3 4B and 8B** with thinking off. **gpt-oss-20b**
  (~13 GB) fits in 16 GB only on a machine that runs nothing else. Models of 30B and
  up don't fit in 16 GB. Newer small models come out often; check what's current.
- Small models should do the WhatsApp matching well, especially with candidate hints.
  Multi-step chat questions are where they become unreliable.
- An always-on mini PC costs a few euros a month in electricity just idling.

---

## 10. Open Questions

1. **Closed lists.** `create_order` rejects orders for a list that isn't open
   (`LIST_NOT_OPEN`). Should an admin be able to enter a WhatsApp order after the
   list has closed, if the customer sent it in time?
2. **Stock.** Should admin-entered orders respect stock limits, or may the admin go
   over them?
3. **Defaults.** Which delivery type and payment method to pre-select when the
   message doesn't say? (The customer's previous order is a good guess.)
4. **Order time.** `data_plasarii`: the time the message was received or the time
   the admin enters it? It feeds the weekday × hour heatmap in the statistics.
5. **Marking assistant orders.** `source="Assistant"` currently only goes to the
   logs. Do we want a column to tell admin-entered orders apart in statistics?
6. **Push notification.** `create_order` sends a "new order" push to admins when
   given `background`. Should admin-entered orders skip it?
7. **Provider.** Hosted or local, and which model — decided after the eval
   (section 7.3).
