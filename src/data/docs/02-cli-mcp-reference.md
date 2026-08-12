# RapidX CLI & MCP Reference

CLI and MCP are **two independent integration paths** — choose either or both:

- **CLI path**: call `rapidx <domain> <action> --input '...' --json` from any shell, script, or exec-capable language. No agent host required.
- **MCP path**: register `rapidx mcp serve` as an MCP server in Claude Code, Codex, Cursor, or any MCP-capable host. Your agent calls `rapidx/order/place`, `rapidx/market/get-ticker`, etc. as structured tools — no shell commands in your agent code.

Both paths use the same credentials, the same capabilities, and the same preview-then-submit safety model.

---

## Response Envelope

Every CLI command and MCP tool returns:

```json
{
  "ok": true,
  "status": "PASS",
  "data": {},
  "auditId": "optional-audit-id",
  "evidence": [
    {
      "source": "real_tool_call",
      "toolOrCommandEvidence": "rapidx market get-ticker",
      "timestamp": "2026-06-08T00:00:00.000Z"
    }
  ]
}
```

Failure uses the same shape:

```json
{
  "ok": false,
  "status": "INVALID_INPUT",
  "code": "RCLI30001",
  "message": "Input schema validation failed: unknown field: foo.",
  "evidence": []
}
```

Read `ok`, `status`, `code`, `message`, and `data`. Do not infer success from process output text alone.

| Status | Meaning |
|--------|---------|
| `PASS` | Completed successfully |
| `FAIL` | Failed — local, upstream, or unexpected |
| `BLOCKED` | Blocked by local validation (e.g. missing preview token) |
| `NOT_VERIFIED` | Could not confirm a real API call — treat as incomplete |
| `EXPECTED_ERROR` | Self-check probe failed in an expected way |
| `INVALID_INPUT` | Input validation failed before calling RapidX |
| `BUSINESS_ERROR` | RapidX rejected as a business-domain error |
| `NOT_FOUND` | Resource not found after lookup |
| `PERMISSION_SCOPE_ERROR` | Credentials lack required account/portfolio scope |

---

## Preview, Confirmation, and Automation

All write operations require **preview before submission**. Preview and submit must use the same runtime (both CLI or both MCP).

### Manual Confirmation (default)

The agent creates a preview, shows the result to the user, and submits only after the user confirms.

Preview response includes:

```json
{
  "previewId": "rpv_xxx",
  "businessParams": { "symbol": "...", "side": "BUY", ... },
  "riskNotes": [],
  "expiresAt": "2026-06-08T00:05:00.000Z",
  "confirmation": {
    "submitToken": "confirm_rpv_xxx",
    "requiredFields": ["previewId", "continueConsentId"]
  }
}
```

Preview records expire after ~5 minutes. If expired or if submit parameters differ from preview, RapidX returns `BLOCKED` — create a new preview.

### Automation Mode

Automation mode lets an agent submit without a per-order chat confirmation. It is valid **only when the human user explicitly enables it in chat**.

Enable on the **preview request** (not on submit):

```json
{
  "automationMode": true,
  "automationConsentText": "I enable RapidX automation mode for BINANCE_PERP_BTC_USDT with maxNotional 100 and accept automated preview-submit execution.",
  "automationScope": "single-preview"
}
```

Rules:
- Pass the user's exact authorization text through `automationConsentText` — do not rewrite or broaden it.
- `automationConsentText` must include the exact symbol and `maxNotional`.
- The text must clearly express automation intent (`automation`, `automated`).
- Submit still requires `previewId` and `continueConsentId`; automation changes confirmation mode, not the API shape.

When accepted, the preview response includes:

```json
{
  "automation": {
    "enabled": true,
    "confirmationMode": "automation-preview",
    "scope": "single-preview",
    "maxNotional": "100"
  }
}
```

---

## MCP Reference

> **Reference implementation**: [ltp-ai-hub / rapidx-mcp-cli](https://github.com/LiquidityTech/ltp-ai-hub/tree/main/rapidx-mcp-cli)
> — A production-quality example showing how to integrate RapidX MCP into an AI agent workflow. Uses the same `@liquiditytech/rapidx-cli` npm package; MCP is not a separate package.

Start the server:

```bash
rapidx mcp serve
```

MCP config:

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

If the agent host cannot resolve `rapidx`, set `command` to the absolute path from `which rapidx`.

### Schema Discovery

After startup, agents should call `rapidx/tools` first:

```text
rapidx/tools
```

Response structure:

```json
{
  "schemaVersion": "2026-05-23",
  "inputSchemas": { "PreviewOrderInput": { ... }, ... },
  "tools": [
    {
      "name": "rapidx/order/place-preview",
      "riskLevel": "trade-write",
      "inputSchema": "PreviewOrderInput",
      "outputSchema": "PreviewOrderResult",
      "previewRequired": false,
      "containsRealOrder": false,
      "requiresExplicitHumanConfirmation": false
    }
  ]
}
```

To construct a tool input:
1. Find the tool by `name`.
2. Read its `inputSchema`.
3. Look up that schema in `inputSchemas`.
4. Send only fields allowed by the schema.

### MCP Tool Groups

#### Discovery & Diagnostics

| MCP tool | Description |
|----------|-------------|
| `rapidx/tools` | Discover tool surface, schemas, and risk levels |
| `rapidx/self-check` | Read-only integration self-check |
| `rapidx/update/check` | Check CLI, MCP schema, and skills version status |

#### Market

| MCP tool |
|----------|
| `rapidx/market/get-ticker` |
| `rapidx/market/get-orderbook` |
| `rapidx/market/get-klines` |
| `rapidx/market/get-funding-rate` |
| `rapidx/market/get-mark-price` |
| `rapidx/market/get-symbol-info` |
| `rapidx/market/get-open-interest` |

#### Portfolio

| MCP tool | RapidX API |
|----------|-----------|
| `rapidx/portfolio/overview` | `GET /api/v1/trading/account` |
| `rapidx/portfolio/assets` | `GET /api/v1/trading/portfolio/assets` |
| `rapidx/portfolio/statement` | `GET /api/v1/trading/statement` |
| `rapidx/portfolio/user-fee-rate` | `GET /api/v1/trading/userFeeRate` |
| `rapidx/portfolio/position-bracket` | `GET /api/v1/trading/positionBracket` |
| `rapidx/portfolio/set-position-mode` | `POST /api/v1/trading/account` |

#### Orders (preview required for writes)

| MCP tool | Purpose |
|----------|---------|
| `rapidx/order/place-preview` | Preview — validates symbol rules, notional, lot size |
| `rapidx/order/place` | Submit place |
| `rapidx/order/replace-preview` | Preview — reads back order before returning token |
| `rapidx/order/replace` | Submit replace |
| `rapidx/order/cancel-preview` | Preview — reads back order before returning token |
| `rapidx/order/cancel` | Submit cancel |
| `rapidx/order/cancel-all` | Cancel all open orders |
| `rapidx/order/query` | Get single order |
| `rapidx/order/open-orders` | List open orders |
| `rapidx/order/history` | Order history |

#### Transactions

| MCP tool | RapidX API |
|----------|-----------|
| `rapidx/transaction/executions` | `GET /api/v1/trading/executions` |

#### Positions (preview required for writes)

| MCP tool | RapidX API |
|----------|-----------|
| `rapidx/position/query` | `GET /api/v1/trading/position` |
| `rapidx/position/history` | `GET /api/v1/trading/history/position` |
| `rapidx/position/get-leverage` | `GET /api/v1/trading/perp/leverage` |
| `rapidx/position/set-leverage` | `POST /api/v1/trading/position/leverage` |
| `rapidx/position/close` | `DELETE /api/v1/trading/position` |
| `rapidx/position/close-all` | `DELETE /api/v1/trading/positions` |

#### Automation Sessions

Automation sessions let a user authorize an agent to trade within a bounded scope without per-order chat confirmation. Preview is still required on every write — the session replaces the per-order chat approval, not the preview step.

| MCP tool | Purpose |
|----------|---------|
| `rapidx/automation/start` | Start a session with scope (symbols, notional, duration, allowed actions) |
| `rapidx/automation/list` | List active sessions |
| `rapidx/automation/status` | Read session status and usage |
| `rapidx/automation/extend` | Extend session expiry (requires user consent) |
| `rapidx/automation/stop` | Stop a session |

Pass `automationSessionId` into preview tools to bind a write to the active session.

#### Trade Utilities

| MCP tool | Purpose |
|----------|---------|
| `rapidx/trade/preview` | Generic preview for capabilities without a dedicated preview tool |
| `rapidx/trade/verify-live` | Explicit small real-trade verification (requires user consent) |

Use concrete preview tools (`rapidx/order/place-preview`, etc.) for normal order workflows — not `rapidx/trade/preview`.

---

## CLI Reference

### Schema Discovery

```bash
rapidx schema --json
```

Response contains `data.schemaVersion`, `data.capabilities[]`, and `data.inputSchemas`. Each capability entry:

```json
{
  "capabilityId": "order.place-preview",
  "cliCommand": "rapidx order place-preview",
  "mcpTool": "rapidx/order/place-preview",
  "inputSchema": "PreviewOrderInput",
  "outputSchema": "PreviewOrderResult",
  "previewRequired": false
}
```

Use the schema to construct `--input` JSON. The live schema from `rapidx schema --json` is authoritative — never hard-code input shapes.

### Diagnostics

```bash
rapidx --version
rapidx schema --json              # discover capabilities and input schemas
rapidx auth check --json          # credential resolution check
rapidx doctor --json              # local diagnostics
rapidx update check --json        # CLI, MCP schema, and skills version check
rapidx self-check --json          # read-only integration self-check
```

### Market

```bash
rapidx market get-ticker         --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
rapidx market get-orderbook      --input '{"symbol":"BINANCE_PERP_BTC_USDT","level":20}' --json
rapidx market get-klines         --input '{"symbol":"BINANCE_PERP_BTC_USDT","interval":"1h","limit":100}' --json
rapidx market get-funding-rate   --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
rapidx market get-mark-price     --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
rapidx market get-symbol-info    --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
rapidx market get-open-interest  --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
```

### Portfolio

```bash
rapidx portfolio overview --json
rapidx portfolio assets --json
rapidx portfolio statement --json
rapidx portfolio user-fee-rate --json
rapidx portfolio position-bracket --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
```

`set-position-mode` is a write operation — preview first:

```bash
rapidx trade preview --input '{"targetCapabilityId":"portfolio.set-position-mode","exchange":"BINANCE","mode":"NET"}' --json
```

### Orders

```bash
# Preview (required before place/replace/cancel)
rapidx order place-preview   --input '{"symbol":"BINANCE_PERP_BTC_USDT","side":"BUY","positionSide":"LONG","orderType":"LIMIT","price":"65000","quantity":"0.001","maxNotional":"100","clientOrderId":"agent-001","postOnly":true}' --json
rapidx order replace-preview --input '{"orderId":"1234567890123456","price":"64000"}' --json
rapidx order cancel-preview  --input '{"orderId":"1234567890123456"}' --json

# Submit (include previewId + continueConsentId from preview response)
# continueConsentId = preview response's confirmation.submitToken
rapidx order place  --input '{...same params...,"previewId":"rpv_xxx","continueConsentId":"confirm_rpv_xxx"}' --json
rapidx order replace --input '{"orderId":"...","price":"64000","previewId":"rpv_xxx","continueConsentId":"confirm_rpv_xxx"}' --json
rapidx order cancel  --input '{"orderId":"...","previewId":"rpv_xxx","continueConsentId":"confirm_rpv_xxx"}' --json

# Reads
rapidx order query       --input '{"clientOrderId":"agent-001"}' --json
rapidx order open-orders --json
rapidx order history     --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
rapidx order cancel-all  --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
```

`positionSide` (`LONG` or `SHORT`) is **required** — competition accounts default to `BOTH` (hedge) mode.

`orderId` must be a 16-digit RapidX order ID. Wrong format → `RCORE00002`. Valid but missing → `NOT_FOUND`.

Cancel is asynchronous at the exchange layer. Check `cancelAccepted` and `terminalStateConfirmed`; poll `rapidx order query` until `CANCELED` if not confirmed.

### Positions

```bash
rapidx position query        --json
rapidx position history      --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
rapidx position get-leverage --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json

# Writes — preview first via rapidx trade preview
rapidx trade preview --input '{"targetCapabilityId":"position.set-leverage","symbol":"BINANCE_PERP_BTC_USDT","leverage":5}' --json
rapidx trade preview --input '{"targetCapabilityId":"position.close","symbol":"BINANCE_PERP_BTC_USDT","reduceOnly":true,"maxNotional":"100"}' --json

rapidx position set-leverage --input '{"previewId":"rpv_xxx","continueConsentId":"confirm_rpv_xxx","symbol":"BINANCE_PERP_BTC_USDT","leverage":5}' --json
rapidx position close        --input '{"previewId":"rpv_xxx","continueConsentId":"confirm_rpv_xxx","symbol":"BINANCE_PERP_BTC_USDT","reduceOnly":true,"maxNotional":"100"}' --json
rapidx position close-all    --input '{"exchange":"BINANCE"}' --json
```

`position.close` does not accept `side` or `quantity`. In HEDGE mode pass `positionSide: "LONG"` or `"SHORT"`; in NET mode omit `positionSide`. If no position exists, preview returns `BLOCKED` with `NO_POSITION_TO_CLOSE`.

### Transactions

```bash
rapidx transaction executions --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
```

### Automation Sessions (CLI)

Automation sessions let the user authorize bounded automated trading without per-order chat confirmation. Preview is still required for every write; the session replaces the per-order chat approval.

**Start a session:**

```bash
rapidx automation start --input '{
  "symbols": ["BINANCE_PERP_BTC_USDT"],
  "maxNotionalPerOrder": "100",
  "maxTotalNotional": "1000",
  "expiresInSeconds": 3600,
  "allowedActions": ["order.place", "order.replace", "order.cancel"],
  "allowedOrderTypes": ["LIMIT", "MARKET"],
  "explicitUserConsent": true,
  "acceptedRiskText": "I authorize RapidX automation for BINANCE_PERP_BTC_USDT with max 100 USDT per order and 1000 USDT total for 1 hour."
}' --json
```

Response returns `automationSessionId`. Pass it into previews:

```bash
rapidx order place-preview --input '{
  "automationSessionId": "ras_xxx",
  "symbol": "BINANCE_PERP_BTC_USDT",
  "side": "BUY",
  "orderType": "LIMIT",
  "price": "65000",
  "quantity": "0.001",
  "maxNotional": "100",
  "clientOrderId": "auto-001"
}' --json
```

Submit with the same params plus `previewId` and `continueConsentId`:

```bash
rapidx order place --input '{
  "automationSessionId": "ras_xxx",
  ...same business params...,
  "previewId": "rpv_xxx",
  "continueConsentId": "confirm_rpv_xxx"
}' --json
```

**Manage sessions:**

```bash
rapidx automation list --json
rapidx automation status --input '{"automationSessionId":"ras_xxx"}' --json
rapidx automation extend --input '{
  "automationSessionId": "ras_xxx",
  "expiresInSeconds": 7200,
  "explicitUserConsent": true,
  "acceptedRiskText": "I authorize extending this RapidX automation session."
}' --json
rapidx automation stop --input '{"automationSessionId":"ras_xxx"}' --json
```

Agent rules: start only after explicit user authorization; pass `automationSessionId` into every preview; do not expand scope without a new session; stop when the user ends automation.

### Live Trade Verification

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

Use `rapidx self-check --json` for routine read-only checks. Use `verify-live` only after explicit user consent for a real-order test.

`rapidx self-check trade-verify` is a CLI compatibility alias for `verify-live`.

---

## Readback Patterns

Do not treat a submit response as final state. Always read back after writes:

| Operation | Read back with |
|-----------|---------------|
| `order place` | `rapidx order query`, then `rapidx transaction executions` if filled |
| `order replace` | `rapidx order query` |
| `order cancel` | `rapidx order query` or `rapidx order open-orders` |
| `order cancel-all` | `rapidx order open-orders` |
| `position close` | `rapidx position query` |

---

## Troubleshooting

### Self-check returns NOT_VERIFIED

Check `message`, `code`, and `evidence`. Common causes: missing credentials, wrong `LTP_API_HOST`, missing account permission, blocked network.

| Code | Meaning | Action |
|------|---------|--------|
| `RCORE01001` | Missing credential | Set `LTP_ACCESS_KEY` and `LTP_SECRET_KEY` |
| `RCORE01003` | Missing API host | Set `LTP_API_HOST` |
| `RCORE00002` | Invalid order ID format | Use a 16-digit RapidX `orderId` |
| `RCORE01004` | Credential scope mismatch | Use credentials with the required scope |
| `RCORE22004` | Resource not found | Check `orderId`, `clientOrderId`, or symbol |
| `RCLI20002` | Preview/consent missing | Run the matching preview first |
| `RCLI22001` | RapidX upstream business error | Read the upstream message and adjust |
| `RCORE23002` | Network/timeout failure | Check connectivity and retry |
| `RCORE23003` | Rate limit reached | Retry later; avoid polling loops |

### Write returns BLOCKED

- Was the matching preview called first?
- Is `previewId` present?
- Does `continueConsentId` equal the preview's `confirmation.submitToken`?
- Do submit params match preview params exactly?
- Is the preview expired (>5 min)?

### MCP tools not visible

Verify MCP config uses `"command": "rapidx", "args": ["mcp", "serve"]`, then reload the agent host. If the host does not inherit shell `PATH`, set `command` to the absolute path from `which rapidx`.

### `rapidx mcp serve` looks stuck

`rapidx mcp serve` is a long-running stdio MCP server — configure it in the MCP host, do not run it as a one-shot command. Use `rapidx self-check --json` for one-shot local verification.

### Symbol not recognized

RapidX requires canonical symbols — normalize before calling any tool:

```
BTCUSDT  →  BINANCE_PERP_BTC_USDT
ETHUSDT  →  BINANCE_PERP_ETH_USDT
```

---

## Upgrade

```bash
rapidx update check --json
npm install -g @liquiditytech/rapidx-cli@latest
rapidx schema --json
rapidx self-check --json
```

Upgrade skills with the same install method used for your agent host.
