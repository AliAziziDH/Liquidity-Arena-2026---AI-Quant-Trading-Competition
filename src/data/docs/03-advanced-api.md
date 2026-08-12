# Advanced: Direct REST & WebSocket API

> For custom code and low-level integrations that call RapidX directly, without the CLI or MCP layer.

**Most participants should use the CLI or MCP** — see [`01-quickstart.md`](./01-quickstart.md). This document is for cases where you need direct HTTP or WebSocket access: performance-critical bots, languages without Node.js, or custom tooling.

Official API docs: <https://apidocliquidity.readme.io/reference/get-account-list>

---

## Authentication

[Official docs →](https://apidocliquidity.readme.io/reference/authentication)

### Required Headers (REST)

| Header | Value |
|--------|-------|
| `X-MBX-APIKEY` | Your Access Key |
| `nonce` | Current Unix timestamp in seconds (string) |
| `signature` | HMAC-SHA256 signature (see below) |
| `Content-Type` | `application/json` |

### REST Signature Algorithm

```
1. Sort request parameters alphabetically by key:
   sorted_payload = "key1=val1&key2=val2&..."

2. Append "&" + timestamp:
   payload = sorted_payload + "&" + timestamp
   (no parameters: payload = "&" + timestamp)

3. HMAC-SHA256 with your Secret Key, hex-encoded:
   signature = HMAC-SHA256(secret_key, payload).hexdigest()
```

**Python example:**

```python
import hmac, hashlib, time

def sign(params: dict, secret_key: str):
    timestamp = str(int(time.time()))
    sorted_payload = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    payload = (sorted_payload + "&" if sorted_payload else "&") + timestamp
    sig = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return sig, timestamp
```

### WebSocket Authentication Signature

Different from REST — used for the private WebSocket login:

```
message = timestamp + "GET" + "/users/self/verify"
sign = HMAC-SHA256(secret_key, message).hexdigest()
```

---

## REST API Endpoints

Base URL: the `LTP_API_HOST` value provided by the organizer.

### Account & Assets

| Method | Path | Description | Docs |
|--------|------|-------------|------|
| GET | `/api/v1/trading/account` | Account overview per exchange | [→](https://apidocliquidity.readme.io/reference/get-portfolio-overview) |
| GET | `/api/v1/trading/portfolio/assets` | Portfolio asset breakdown | [→](https://apidocliquidity.readme.io/reference/get-portfolio-assets-details) |
| GET | `/api/v1/trading/user/tradingStats` | Trading statistics (`begin`, `end` params) | [→](https://apidocliquidity.readme.io/reference/query-user-tradingstats) |
| GET | `/api/v1/trading/userFeeRate` | Maker/Taker fee rates | [→](https://apidocliquidity.readme.io/reference/user-trading-fee-rate) |

### Orders

| Method | Path | Description | Docs |
|--------|------|-------------|------|
| POST | `/api/v1/trading/order` | Place order | [→](https://apidocliquidity.readme.io/reference/place-order) |
| PUT | `/api/v1/trading/order` | Amend order | [→](https://apidocliquidity.readme.io/reference/replace-order) |
| DELETE | `/api/v1/trading/order` | Cancel order | [→](https://apidocliquidity.readme.io/reference/cancel-order) |
| DELETE | `/api/v1/trading/cancelAll` | Cancel all orders (`sym` or `exchangeType`) | [→](https://apidocliquidity.readme.io/reference/cancel-one-portfolio-orders) |
| GET | `/api/v1/trading/order` | Get single order (`orderId` or `clientOrderId`) | [→](https://apidocliquidity.readme.io/reference/query-order) |
| GET | `/api/v1/trading/orders` | List open orders | [→](https://apidocliquidity.readme.io/reference/current-open-orders) |
| GET | `/api/v1/trading/history/orders` | Order history (`sym` optional) | [→](https://apidocliquidity.readme.io/reference/order-history) |
| GET | `/api/v1/trading/archive/history/orders` | Archived order history | [→](https://apidocliquidity.readme.io/reference/order-history-archive) |
| GET | `/api/v1/trading/executions` | Execution records | [→](https://apidocliquidity.readme.io/reference/query-transactions) |
| GET | `/api/v1/trading/executions/pageable` | Pageable executions | [→](https://apidocliquidity.readme.io/reference/query-transactions-pageable) |
| GET | `/api/v1/trading/statement` | Trading statement | [→](https://apidocliquidity.readme.io/reference/query-statement) |

**Place order fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `sym` | Yes | e.g. `BINANCE_PERP_BTC_USDT` |
| `side` | Yes | `BUY` / `SELL` |
| `positionSide` | Yes (hedge mode) | `LONG` / `SHORT` |
| `orderType` | Yes | `LIMIT` / `MARKET` |
| `orderQty` | Yes | Base/contract quantity |
| `limitPrice` | For LIMIT | Limit price |
| `timeInForce` | No | `GTC` (default) / `IOC` / `FOK` / `GTX` |
| `clientOrderId` | Recommended | Max 40 chars |

**Order states:** `NEW` → `OPEN` → `PARTIALLY_FILLED` → `FILLED` / `CANCELLED` / `REJECTED`

### Positions

| Method | Path | Description | Docs |
|--------|------|-------------|------|
| GET | `/api/v1/trading/position` | Open positions (`sym`, `exchange` optional) | [→](https://apidocliquidity.readme.io/reference/query-portfolio-position) |
| GET | `/api/v1/trading/history/position` | Position history | [→](https://apidocliquidity.readme.io/reference/query-portfolio-history-position) |
| DELETE | `/api/v1/trading/position` | Close position (`sym`, `positionSide`) | [→](https://apidocliquidity.readme.io/reference/close-position) |
| DELETE | `/api/v1/trading/positions` | Close all positions (`exchangeType`, `closeAllPos:"true"`) | [→](https://apidocliquidity.readme.io/reference/close-positions) |
| GET | `/api/v1/trading/perp/leverage` | Get leverage (`sym` or `exchange` optional) | [→](https://apidocliquidity.readme.io/reference/get-perp-leverage) |
| POST | `/api/v1/trading/position/leverage` | Set leverage (`sym`, `leverage`) | [→](https://apidocliquidity.readme.io/reference/set-leverage) |
| GET | `/api/v1/adl/rank` | ADL rank (`sym` optional) | [→](https://apidocliquidity.readme.io/reference/query-adl-rank) |

### Market Data (RapidX)

| Method | Path | Description | Docs |
|--------|------|-------------|------|
| GET | `/api/v1/trading/sym/info` | Symbol rules (`sym` optional) | [→](https://apidocliquidity.readme.io/reference/sym-info) |
| GET | `/api/v1/market/fundingRate` | Funding rate (`sym` required) | [→](https://apidocliquidity.readme.io/reference/get-current-fundingfee) |
| GET | `/api/v1/market/markPrice` | Mark price (`sym` optional) | [→](https://apidocliquidity.readme.io/reference/get-current-markprice) |
| GET | `/api/v1/trading/positionBracket` | Position tier/bracket | [→](https://apidocliquidity.readme.io/reference/positionbracket) |
| GET | `/api/v1/trading/loan/info` | Loan info | [→](https://apidocliquidity.readme.io/reference/get-loan-tier) |
| GET | `/api/v1/trading/coin/discount` | Coin discount rate | [→](https://apidocliquidity.readme.io/reference/get-discount-rate-detail) |
| GET | `/api/v1/trading/margin/leverage` | Margin leverage | [→](https://apidocliquidity.readme.io/reference/get-margin-leverage) |

### REST Response Format

```json
{
  "code": 200000,
  "message": "Success",
  "data": { ... }
}
```

`code: 200000` = success. Any other value is an error. [Error codes →](https://apidocliquidity.readme.io/reference/error-codes)

---

## WebSocket

### Private WebSocket (Trading + Account Events)

[User Data Streams overview →](https://apidocliquidity.readme.io/reference/ws-user-data-overview)

**URL:** `wss://wss-uat.liquiditytech.com/v1/private`

**Login:**

```json
{
  "action": "login",
  "args": {
    "apiKey": "YOUR_ACCESS_KEY",
    "timestamp": "1778140847",
    "sign": "..."
  }
}
```

**Response:**

```json
{ "event": "login", "code": 0, "msg": "" }
```

**Order actions:**

| Action | Docs |
|--------|------|
| `place_order` | [→](https://apidocliquidity.readme.io/reference/ws-place-order) |
| `replace_order` | [→](https://apidocliquidity.readme.io/reference/ws-replace-order) |
| `cancel_order` | [→](https://apidocliquidity.readme.io/reference/ws-cancel-order) |
| `cancel_orders` | [→](https://apidocliquidity.readme.io/reference/ws-cancel-orders) |

```json
{ "id": "p1", "action": "place_order",  "args": { ... } }
{ "id": "a1", "action": "replace_order","args": { "orderId": "...", "replacePrice": "64000" } }
{ "id": "c1", "action": "cancel_order", "args": { "orderId": "..." } }
```

**Orders push channel** — auto-subscribed after login. [User data streams →](https://apidocliquidity.readme.io/reference/ws-user-data-orders-trades-assets-positions)

```json
{
  "channel": "Orders",
  "data": {
    "orderId": "1234567890123456",
    "clientOrderId": "agent-001",
    "orderState": "FILLED",
    "executedQty": "0.001",
    "executedAvgPrice": "65000"
  }
}
```

Keepalive: send `"ping"` every 15 seconds; server replies `"pong"`.

### Market Data WebSocket

[Market Data overview →](https://apidocliquidity.readme.io/reference/market-data-overview)

**URL:** `wss://mds-uat.liquiditytech.com/marketdata/v2/public`

Append `?binary=false` for plain-text JSON instead of GZIP frames.

**Rate limits:**

| Mode | Max connections / IP | Max symbols / connection |
|------|---------------------|--------------------------|
| Unauthenticated | 5 | 5 |
| Authenticated | 40 | 50 |

Limits are counted by **trading pair** — subscribing BBO + TICKER + TRADE for the same symbol counts as 1 pair.

**Subscribe:**

```json
{
  "event": "subscribe",
  "arg": [
    { "channel": "BBO",   "sym": "BINANCE_PERP_BTC_USDT" },
    { "channel": "TRADE", "sym": "BINANCE_PERP_BTC_USDT" }
  ]
}
```

**Available channels:**

| Channel | Frequency | Scope | Docs |
|---------|-----------|-------|------|
| `BBO` | On change | All | [→](https://apidocliquidity.readme.io/reference/market-data-bbo) |
| `TICKER` | 2000 ms | All | [→](https://apidocliquidity.readme.io/reference/market-data-ticker) |
| `TRADE` | Real-time | All | [→](https://apidocliquidity.readme.io/reference/market-data-trade) |
| `ORDER_BOOK` | 250 ms | All | [→](https://apidocliquidity.readme.io/reference/market-data-order-book) |
| `KLINE` | Real-time | All | [→](https://apidocliquidity.readme.io/reference/market-data-kline-candlestick) |
| `MARK_PRICE` | Real-time | Perpetual only | [→](https://apidocliquidity.readme.io/reference/market-data-price) |
| `INDEX_PRICE` | Real-time | Perpetual only | [→](https://apidocliquidity.readme.io/reference/market-data-price) |
| `MARK_PRICE_KLINE` | Real-time | Perpetual only | [→](https://apidocliquidity.readme.io/reference/market-data-kline-candlestick) |
| `INDEX_KLINE` | Real-time | Perpetual only | [→](https://apidocliquidity.readme.io/reference/market-data-kline-candlestick) |
| `OPEN_INTEREST` | On change | Perpetual only | [→](https://apidocliquidity.readme.io/reference/market-data-open-interest) |

Keepalive: send `{ "ping": <timestamp_ms> }` every 20 seconds; server replies `{ "pong": <timestamp_ms> }`.

---

## Symbol Format

```
{EXCHANGE}_{TYPE}_{BASE}_{QUOTE}
```

| Exchange | Type | Examples |
|----------|------|---------|
| `BINANCE` | `PERP` | `BINANCE_PERP_BTC_USDT`, `BINANCE_PERP_ETH_USDT` |

Channels marked "Perpetual only" reject `SPOT` symbols with error `11100`.

---

## Common Error Codes

[Full error code reference →](https://apidocliquidity.readme.io/reference/error-codes)

### REST

| Code | Meaning |
|------|---------|
| `200000` | Success |
| `2002` | Invalid API authorization |
| `401018` | Order not found |
| `401097` | Position quantity is 0 |
| `401117` | Order already completed |

### Market Data WebSocket

| Code | Meaning |
|------|---------|
| `0` | Success |
| `11100` | Invalid symbol |
| `11210` | Unauthenticated symbol limit (5) exceeded |
| `11220` | Authenticated symbol limit (50) exceeded |
| `11250` | Symbol not currently supported |
| `11260` | Request rate limit exceeded |

---
