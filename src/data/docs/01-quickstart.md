# Getting Started with RapidX

> Install the CLI, connect your agent, run your first trade — in under 10 minutes.

RapidX CLI (`@liquiditytech/rapidx-cli` v1.0.38) provides two **independent** integration paths — choose either one or both:

| Path | How you use it | Best for |
|------|---------------|---------|
| **CLI** | `rapidx <domain> <action> --input '...' --json` in your shell or code | Scripts, CI, exec-only agents |
| **MCP** | `rapidx mcp serve` registered as an MCP server in Claude Code / Codex / Cursor | AI agent hosts that support MCP |

The two paths share the same credentials and the same underlying capabilities. You do **not** need to use MCP to use the CLI, and you do **not** need to run CLI commands if your agent uses MCP.

---

## Before You Begin

### Account & Credentials

Competition accounts are issued by the organizer at registration. Each account includes:
- `LTP_ACCESS_KEY` and `LTP_SECRET_KEY` — your API credentials
- `LTP_API_HOST` — the UAT API base URL (**required, no default**)
- Initial virtual balance: **1,000 USDT** (simulation only, no real assets at risk)
- Default position mode: `BOTH` (hedge mode)

> See [`resources.md §1`](./resources.md#1-competition-account) for full account details and Track A symbol restrictions.

### Software Requirements

| Requirement | Details |
|-------------|---------|
| Node.js | **20 or later** |
| npm | Any recent version |

`LTP_API_HOST` has no default. Missing it returns `RCORE01003`.

---

## Step 1 — Install the CLI

```bash
npm install -g @liquiditytech/rapidx-cli@latest
rapidx --version
```

If npm cannot find the package:

```bash
npm config set @liquiditytech:registry https://registry.npmjs.org/
npm install -g @liquiditytech/rapidx-cli@latest
```

---

## Step 2 — Configure Credentials

```bash
export LTP_ACCESS_KEY="<your-access-key>"
export LTP_SECRET_KEY="<your-secret-key>"
export LTP_API_HOST="<host-provided-by-organizer>"
```

> Never paste keys into public chats, repositories, screenshots, or logs.

Verify credential resolution (no full secrets printed):

```bash
rapidx auth check
```

---

## Step 3 — Choose Your Integration Path

CLI and MCP are independent — pick the one that fits your setup. You can switch or combine them at any time.

### Path A — MCP

For AI agent hosts that natively support MCP: **Claude Code, Codex, Cursor, Continue, OpenCode**. Your agent calls `rapidx/market/get-ticker`, `rapidx/order/place`, etc. as structured tools — no shell commands in your code.

**Option 1: Install skills (let the agent do the rest)**

Skills guide the agent through the full setup automatically.

```bash
# Claude Code
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git \
  --skill ltp-rapidx-config --skill ltp-rapidx-trading -a claude-code -y

# Codex
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git \
  --skill ltp-rapidx-config --skill ltp-rapidx-trading -a codex -y

# Cursor
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git \
  --skill ltp-rapidx-config --skill ltp-rapidx-trading -a cursor -y

# OpenClaw
openclaw skills install ltp-rapidx-config
openclaw skills install ltp-rapidx-trading

# Hermes
hermes skills install LiquidityTech/ltp-rapidx-skill/skills/ltp-rapidx-config
hermes skills install LiquidityTech/ltp-rapidx-skill/skills/ltp-rapidx-trading
```

After installing, tell your agent: *"Follow ltp-rapidx-config."* The skill configures MCP, sets credentials, and runs self-check.

**Option 2: Configure MCP manually**

Add to your agent's MCP config file (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "rapidx": {
      "command": "rapidx",
      "args": ["mcp", "serve"],
      "env": {
        "LTP_ACCESS_KEY": "<your-access-key>",
        "LTP_SECRET_KEY": "<your-secret-key>",
        "LTP_API_HOST": "<host-provided-by-organizer>"
      }
    }
  }
}
```

Restart the agent host. MCP tools become available under the `rapidx/` namespace.

### Path B — CLI

For exec-only agents, shell scripts, Python/Java/C++ bots, CI pipelines. No MCP setup required — call `rapidx` commands directly from your code.

```bash
rapidx market get-ticker --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
rapidx portfolio overview --json       # portfolio overview (account summary)
rapidx portfolio assets --json         # per-coin asset breakdown
rapidx order open-orders --json        # current open orders
rapidx position query --json           # open positions
```

All commands return a stable JSON envelope. Always call `rapidx schema --json` first to get exact input schemas for the current version — see [`02-cli-mcp-reference.md`](./02-cli-mcp-reference.md) §CLI Reference for the full command list, automation sessions, and readback patterns.

---

## Step 4 — Run Self-Check

```bash
rapidx self-check --read-only --json
```

Each check item reports `PASS` / `EXPECTED_ERROR` / `FAIL` / `NOT_VERIFIED`. Do not proceed to trading until all critical items pass.

Expected output:

```json
{
  "ok": true,
  "status": "PASS",
  "data": {
    "scope": "quick",
    "status": "PASS",
    "checks": [
      { "name": "discovery",     "status": "PASS" },
      { "name": "public-market", "status": "PASS" }
    ]
  }
}
```

---

## Step 5 — Query Market Data

```bash
# Live ticker
rapidx market get-ticker --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json

# Klines (1h, last 100 bars)
rapidx market get-klines --input '{"symbol":"BINANCE_PERP_BTC_USDT","interval":"1h","limit":100}' --json

# Order book (20 levels)
rapidx market get-orderbook --input '{"symbol":"BINANCE_PERP_BTC_USDT","level":20}' --json

# Symbol rules — always check before trading
rapidx market get-symbol-info --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
```

`get-symbol-info` returns `minNotional`, `lotSize`, `tickSize`, and `contractSize` — read it before sizing any order.

---

## Step 6 — Place Your First Order

All write operations follow **preview → submit**. The preview validates trading rules and returns a token; the submit uses that token.

```bash
# 1. Preview
rapidx order place-preview --input '{
  "symbol": "BINANCE_PERP_BTC_USDT",
  "side": "BUY",
  "positionSide": "LONG",
  "orderType": "LIMIT",
  "price": "60000",
  "quantity": "0.001",
  "maxNotional": "100",
  "clientOrderId": "my-first-order",
  "postOnly": true
}' --json
```

> `positionSide` is **required** — competition accounts default to `BOTH` (hedge) mode, which requires `LONG` or `SHORT` on every order.
> `postOnly: true` means the order will be rejected if it would immediately fill (protects against accidental market execution).

Preview response — copy `submitToken` for the next step:

```json
{
  "ok": true,
  "status": "PASS",
  "data": {
    "previewId": "rpv_xxx",
    "confirmation": { "submitToken": "confirm_rpv_xxx" }
  }
}
```

```bash
# 2. Submit — same params + previewId + continueConsentId
#    continueConsentId = the submitToken value from the preview response above
rapidx order place --input '{
  "symbol": "BINANCE_PERP_BTC_USDT",
  "side": "BUY",
  "positionSide": "LONG",
  "orderType": "LIMIT",
  "price": "60000",
  "quantity": "0.001",
  "maxNotional": "100",
  "clientOrderId": "my-first-order",
  "postOnly": true,
  "previewId": "rpv_xxx",
  "continueConsentId": "confirm_rpv_xxx"
}' --json

# 3. Confirm state
rapidx order query --input '{"clientOrderId":"my-first-order"}' --json
```

> Preview and submit must use the **same runtime** (both CLI or both MCP — do not mix).
> Preview records expire after ~5 minutes.
> `clientOrderId` must be **unique per order** — reusing the same value on a second run will fail. Use a timestamp suffix (e.g. `"my-order-1749123456"`) for each new order.

---

## What's Next

| Document | Contents |
|----------|----------|
| [`02-cli-mcp-reference.md`](./02-cli-mcp-reference.md) | Complete MCP tool reference + CLI command reference, automation sessions, readback patterns, troubleshooting |
| [`03-advanced-api.md`](./03-advanced-api.md) | Direct REST/WebSocket access for custom integrations |
| [`resources.md`](./resources.md) | Endpoints, npm package, symbol list, schedule, support |

---
