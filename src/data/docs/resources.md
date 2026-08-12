# Resource Manifest — AI Quantitative Trading Competition

> Everything a participant receives or needs to access for the competition.

---

## 1. Competition Account

Each participant receives a dedicated simulation account on the UAT mock matching environment.

| Item | Value |
|------|-------|
| Portfolio ID | *(issued individually by organizer)* |
| Access Key (`LTP_ACCESS_KEY`) | *(issued individually, distributed via secure channel)* |
| Secret Key (`LTP_SECRET_KEY`) | *(issued individually, distributed via secure channel)* |
| API Host (`LTP_API_HOST`) | *(provided by organizer — **required, no default**)* |
| Initial virtual balance | 1,000 USDT (subject to organizer announcement) |
| Position mode | `BOTH` (hedge mode) by default |
| Real-asset risk | **None.** All orders route to the mock matching engine. |

> Credentials are delivered via the registration channel. Treat them as production secrets — never commit, log, or share them.

---

## 2. Service Endpoints

See [`03-advanced-api.md`](./03-advanced-api.md) for authentication, signature algorithm, and full endpoint reference.

| Service | URL |
|---------|-----|
| REST API | *(use `LTP_API_HOST` value provided by organizer)* |
| Private WebSocket (trading & account events) | `wss://wss-uat.liquiditytech.com/v1/private` |
| Market Data WebSocket (OPEN API) | `wss://mds-uat.liquiditytech.com/marketdata/v2/public` |

### Market Data WebSocket Rate Limits

| Mode | Max connections / IP | Max symbols / connection |
|------|---------------------|--------------------------|
| Unauthenticated | 5 | 5 |
| Authenticated | 40 | 50 |

> Authenticate with your competition API Key to reach the higher limits.

---

## 3. npm Packages

See [`01-quickstart.md`](./01-quickstart.md) §Step 1 for install and registry troubleshooting.

| Package | Description | Install |
|---------|-------------|---------|
| `@liquiditytech/rapidx-cli` | RapidX CLI (`rapidx` command) + `rapidx mcp serve` | `npm install -g @liquiditytech/rapidx-cli` |

Run `rapidx --version` after install to confirm the version.

If npm maps `@liquiditytech` to a custom registry, point it to the official registry first:

```bash
npm config set @liquiditytech:registry https://registry.npmjs.org/
npm install -g @liquiditytech/rapidx-cli@latest
```

---

## 4. Skills

See [`01-quickstart.md`](./01-quickstart.md) §Step 3 Path A for per-agent-host install commands (Claude Code, Codex, Cursor, OpenClaw, Hermes).

| Skill | Location | Purpose |
|-------|----------|---------|
| `ltp-rapidx-config` | `https://github.com/LiquidityTech/ltp-rapidx-skill` | Install CLI, collect credentials, configure MCP, run self-check |
| `ltp-rapidx-trading` | Same repository | Discover tools, manage reads/writes, run live trade verification |

---

## 5. CLI & MCP Tool Catalogue

See [`02-cli-mcp-reference.md`](./02-cli-mcp-reference.md) for full input/output specs, the preview-then-submit pattern, and automation mode.

All CLI commands use the format `rapidx <domain> <action> --input '<json>' --json`.
All MCP tools use the `rapidx/` prefix.

### Discovery & Diagnostics

| CLI | MCP tool | Description |
|-----|----------|-------------|
| `rapidx schema --json` | `rapidx/tools` | List all capabilities and schemas |
| `rapidx self-check --read-only --json` | `rapidx/self-check` | Verify read-only connectivity |
| `rapidx doctor --json` | CLI only | Local diagnostics (version, credential source, invocation mode) |
| `rapidx auth check` | CLI only | Credential check without printing secrets |
| `rapidx invocation check` | CLI only | Verify the invocation style is supported |
| `rapidx update check --json` | `rapidx/update/check` | Check for CLI/skills updates |

### Market Data

| CLI | MCP tool |
|-----|----------|
| `rapidx market get-ticker` | `rapidx/market/get-ticker` |
| `rapidx market get-orderbook` | `rapidx/market/get-orderbook` |
| `rapidx market get-klines` | `rapidx/market/get-klines` |
| `rapidx market get-funding-rate` | `rapidx/market/get-funding-rate` |
| `rapidx market get-mark-price` | `rapidx/market/get-mark-price` |
| `rapidx market get-symbol-info` | `rapidx/market/get-symbol-info` |
| `rapidx market get-open-interest` | `rapidx/market/get-open-interest` |

### Portfolio

| CLI | MCP tool |
|-----|----------|
| `rapidx portfolio overview` | `rapidx/portfolio/overview` |
| `rapidx portfolio assets` | `rapidx/portfolio/assets` |
| `rapidx portfolio statement` | `rapidx/portfolio/statement` |
| `rapidx portfolio user-fee-rate` | `rapidx/portfolio/user-fee-rate` |
| `rapidx portfolio position-bracket` | `rapidx/portfolio/position-bracket` |
| `rapidx portfolio set-position-mode` | `rapidx/portfolio/set-position-mode` |

### Orders (preview required for all writes)

| CLI | MCP tool |
|-----|----------|
| `rapidx order place-preview` | `rapidx/order/place-preview` |
| `rapidx order place` | `rapidx/order/place` |
| `rapidx order replace-preview` | `rapidx/order/replace-preview` |
| `rapidx order replace` | `rapidx/order/replace` |
| `rapidx order cancel-preview` | `rapidx/order/cancel-preview` |
| `rapidx order cancel` | `rapidx/order/cancel` |
| `rapidx order cancel-all` | `rapidx/order/cancel-all` |
| `rapidx order query` | `rapidx/order/query` |
| `rapidx order open-orders` | `rapidx/order/open-orders` |
| `rapidx order history` | `rapidx/order/history` |

### Transactions

| CLI | MCP tool |
|-----|----------|
| `rapidx transaction executions` | `rapidx/transaction/executions` |

### Positions (preview required for writes)

| CLI | MCP tool |
|-----|----------|
| `rapidx position query` | `rapidx/position/query` |
| `rapidx position history` | `rapidx/position/history` |
| `rapidx position get-leverage` | `rapidx/position/get-leverage` |
| `rapidx position set-leverage` | `rapidx/position/set-leverage` |
| `rapidx position close` | `rapidx/position/close` |
| `rapidx position close-all` | `rapidx/position/close-all` |

### Algo Orders (preview required for writes)

| CLI | MCP tool |
|-----|----------|
| `rapidx algo place` | `rapidx/algo/place` |
| `rapidx algo replace` | `rapidx/algo/replace` |
| `rapidx algo cancel` | `rapidx/algo/cancel` |
| `rapidx algo open-orders` | `rapidx/algo/open-orders` |
| `rapidx algo history` | `rapidx/algo/history` |
| `rapidx algo query` | `rapidx/algo/query` |

### Automation Sessions

| CLI | MCP tool |
|-----|----------|
| `rapidx automation start` | `rapidx/automation/start` |
| `rapidx automation list` | `rapidx/automation/list` |
| `rapidx automation status` | `rapidx/automation/status` |
| `rapidx automation extend` | `rapidx/automation/extend` |
| `rapidx automation stop` | `rapidx/automation/stop` |

### Trade Utilities

| CLI | MCP tool |
|-----|----------|
| `rapidx trade preview` | `rapidx/trade/preview` |
| `rapidx trade verify-live` | `rapidx/trade/verify-live` |

Full input/output specifications: [`02-cli-mcp-reference.md`](./02-cli-mcp-reference.md).

---

## 6. Symbol Universe

Format: `{EXCHANGE}_{TYPE}_{BASE}_{QUOTE}`

Supported exchanges: `BINANCE` · `OKX` · `EDX`

### Track A — Binance Perp Only

> **Note**: Track A restricts trading to a defined set of Binance perpetual futures symbols.
>
> - **Symbol restriction**: only the symbols listed in the official competition announcement are permitted. Use `rapidx market get-symbol-info --json` to query tradable symbols, but always verify against the organizer's symbol list — *see official announcement for the complete list*.
> - **Rate limits**: TBD — details to be announced.

### Common Symbols

| Symbol | Description |
|--------|-------------|
| `BINANCE_PERP_BTC_USDT` | Binance BTC perpetual futures |
| `BINANCE_PERP_ETH_USDT` | Binance ETH perpetual futures |
| `BINANCE_PERP_BNB_USDT` | Binance BNB perpetual futures |
| `BINANCE_PERP_XRP_USDT` | Binance XRP perpetual futures |
| `BINANCE_PERP_ADA_USDT` | Binance ADA perpetual futures |
| `BINANCE_PERP_DOGE_USDT` | Binance DOGE perpetual futures |

Full list:

```bash
rapidx market get-symbol-info --json
```

> **Check symbol rules before trading**: minimum notional, lot size, tick size, and contract size vary by symbol. Run `rapidx market get-symbol-info --input '{"symbol":"..."}' --json` before sizing any order.

---

## 7. Documentation

| Document | Location |
|----------|----------|
| Getting started | [`01-quickstart.md`](./01-quickstart.md) |
| CLI & MCP reference | [`02-cli-mcp-reference.md`](./02-cli-mcp-reference.md) |
| Advanced REST & WebSocket | [`03-advanced-api.md`](./03-advanced-api.md) |
| Resource manifest | This document |
| GitHub repository | <https://github.com/LiquidityTech/ltp-arena-docs> |

---

## 8. Verification

Use the built-in CLI self-check — no extra dependencies required:

```bash
rapidx auth check
rapidx self-check --read-only --json
```

Each check reports **PASS** / **EXPECTED_ERROR** / **FAIL** / **NOT_VERIFIED**.

For an end-to-end live trade test (submits a real post-only order then cancels):

```bash
rapidx trade verify-live --input '{
  "symbol": "BINANCE_PERP_BTC_USDT",
  "side": "BUY",
  "maxNotional": "10",
  "clientOrderId": "verify-live-001",
  "explicitUserConsent": true,
  "acceptedRiskText": "I authorize a real verification order for BINANCE_PERP_BTC_USDT BUY maxNotional 10 with cancel cleanup."
}' --json
```

---

## 9. Competition Schedule

| Phase | Activity |
|-------|----------|
| Registration | Receive credentials, install CLI, run self-check |
| Development | Build and test agent against live UAT data |
| Submission cut-off | Freeze agent code + model weights |
| Evaluation window | Frozen agents run on live forward market data |
| Scoring & awards | Multi-metric scoring (return, Sharpe, max drawdown, win rate) |

Exact dates communicated via the organizer's official channel.

---

## 10. Support

> TBD — details to be announced.

---

## 11. Safety & Compliance Reminders

1. **No real assets at risk** — competition runs on the UAT mock matching engine.
2. **Preview before every write** — all writes require preview; the preview never submits a real order.
3. **`LTP_API_HOST` is required** — missing host returns `RCORE01003`.
4. **State confirmation after every write** — call `rapidx order query` or `rapidx position query`. No blind retries.
5. **Secrets never leak** — keys are masked in all CLI/MCP output, logs, and reports.
6. **Single-track competition** — all participants compete under identical conditions.

---
