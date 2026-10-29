# Order creation rate limit

The API limits how many orders a single IP can create in a time window to reduce spam and abuse. Only **POST /api/v1/orders/** is rate-limited; list, get, update, and delete are not.

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ORDER_RATE_LIMIT_MAX` | Maximum number of orders allowed per IP in the window | `10` |
| `ORDER_RATE_LIMIT_WINDOW` | Window period (no space). See valid values below | `24hour` |

The effective limit string is `ORDER_RATE_LIMIT_MAX/ORDER_RATE_LIMIT_WINDOW`, and must follow the **limits** library (slowapi) syntax.

### Valid window values

Use **no space** between a numeric multiplier and the unit. Valid examples:

| Window | Meaning |
|--------|---------|
| `second` | Per second |
| `minute` | Per minute |
| `hour` | Per hour |
| `day` | Per day |
| `24hour` | Per 24 hours |
| `1day` | Per 1 day |
| `1hour` | Per 1 hour |

Invalid: `24 hour` (space not allowed).

### Example env values

```env
# Default: 10 orders per 24 hours per IP
ORDER_RATE_LIMIT_MAX=10
ORDER_RATE_LIMIT_WINDOW=24hour

# Stricter: 5 orders per hour per IP
ORDER_RATE_LIMIT_MAX=5
ORDER_RATE_LIMIT_WINDOW=1hour

# Per minute
ORDER_RATE_LIMIT_MAX=2
ORDER_RATE_LIMIT_WINDOW=1minute

# Looser: 100 orders per day per IP
ORDER_RATE_LIMIT_MAX=100
ORDER_RATE_LIMIT_WINDOW=day
```

## Behaviour

- **Key:** The client IP as Uvicorn resolves it (`request.client.host`). Uvicorn takes it from
  `X-Forwarded-For` only when the request comes from a proxy listed in `FORWARDED_ALLOW_IPS`, so
  a client cannot choose its own key. If the proxy is missing from that list, every customer
  shares the proxy's IP and one limit; the API logs a warning when it sees this, at most hourly.
- **Never set `FORWARDED_ALLOW_IPS=*`.** Uvicorn then trusts everyone and takes the first
  `X-Forwarded-For` entry, which the client writes, so clients choose their own key again.
- **Trusting the Docker gateway** (e.g. `172.18.0.1`, when the proxy runs on the host) also
  trusts connections Docker relays to the published port 8000 from outside. Keep that port
  unreachable except through the proxy: publish it as `127.0.0.1:8000:8000`, or firewall it.
- **Over limit:** HTTP 429 with detail `"Too many orders from this IP. Please try again later."`
- **Storage:** In-memory by default (per process; with multiple workers the effective limit per IP is roughly limit × workers unless you switch to Redis).

## References

- Rate limit string notation: [limits library quickstart](https://limits.readthedocs.io/en/stable/quickstart.html#rate-limit-string-notation).
