# RapidX CLI

RapidX CLI is the local runtime for RapidX commands and the entry point for starting RapidX MCP.

Install from official npm:

```bash
npm install -g @liquiditytech/rapidx-cli@latest
```

Verify installation:

```bash
rapidx --version
rapidx schema --json
```

## JSON Output Envelope

Most CLI commands return a JSON envelope when `--json` is used:

```json
{
  "ok": true,
  "status": "PASS",
  "data": {},
  "evidence": [
    {
      "source": "real_tool_call",
      "toolOrCommandEvidence": "rapidx <domain> <action>",
      "timestamp": "2026-06-22T00:00:00.000Z"
    }
  ]
}
```

Failure responses use the same envelope shape:

```json
{
  "ok": false,
  "status": "INVALID_INPUT",
  "code": "RCLI30001",
  "message": "Input schema validation failed: unknown field: foo.",
  "evidence": []
}
```

Agents should read `ok`, `status`, `code`, `message`, and `data`. Do not infer success from process output text alone.

## How To Get Input Schema

Use:

```bash
rapidx schema --json
```

The response contains:

```text
data.schemaVersion
data.capabilities[]
data.inputSchemas
```

To construct input for a command:

1. Find the capability whose `cliCommand` matches the command.
2. Read its `inputSchema` name.
3. Look up that schema in `data.inputSchemas`.
4. Send JSON through `--input '<json>'`.

Example capability entry:

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

Example schema lookup:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["symbol", "side", "orderType", "quantity", "maxNotional", "clientOrderId"],
  "properties": {
    "symbol": { "type": "string" },
    "side": { "type": "string", "enum": ["BUY", "SELL"] },
    "orderType": { "type": "string", "enum": ["LIMIT", "MARKET"] },
    "price": { "type": "string" },
    "quantity": { "type": "string" },
    "maxNotional": { "type": "string" },
    "clientOrderId": { "type": "string" },
    "automationSessionId": { "type": "string" }
  }
}
```

The exact schema from `rapidx schema --json` is authoritative.

## Configure Credentials

RapidX CLI needs these values:

```text
LTP_ACCESS_KEY
LTP_SECRET_KEY
LTP_API_HOST
```

For CLI-only use, provide them as environment variables in the runtime that executes `rapidx`.

For MCP use, put them in the MCP server environment:

```json
{
  "mcpServers": {
    "rapidx": {
      "command": "rapidx",
      "args": ["mcp", "serve"],
      "env": {
        "LTP_ACCESS_KEY": "<secret>",
        "LTP_SECRET_KEY": "<secret>",
        "LTP_API_HOST": "<provided-api-host>"
      }
    }
  }
}
```

When the agent host supports user-provided secrets, use that mechanism for `LTP_ACCESS_KEY` and `LTP_SECRET_KEY`.

Check credential resolution:

```bash
rapidx auth check --json
```

## Command Model

For agent execution, use `--json` on one-shot CLI commands. Practical exceptions:

- `rapidx --version`
- `rapidx mcp serve`

Core diagnostic commands:

| Command | Purpose |
|---|---|
| `rapidx --version` | Print CLI version |
| `rapidx schema --json` | Discover capabilities and input schemas |
| `rapidx auth check --json` | Check credential resolution |
| `rapidx doctor --json` | Run local diagnostics |
| `rapidx update check --json` | Check CLI, MCP schema, and skills versions |
| `rapidx self-check --json` | Run read-only integration self-check |
| `rapidx trade verify-live --input '<json>' --json` | Run explicit small live-trade verification with user-approved input |

## Live Trading Verification

`rapidx trade verify-live` submits a real verification order. It is used when the user wants to prove that read, preview, submit, cancel, and cleanup all work against the real RapidX trading API.

It requires explicit input:

```bash
rapidx trade verify-live --input '{
  "symbol": "BINANCE_PERP_BTC_USDT",
  "side": "BUY",
  "maxNotional": "100",
  "clientOrderId": "verify-live-001",
  "explicitUserConsent": true,
  "acceptedRiskText": "I authorize a real verification order for BINANCE_PERP_BTC_USDT BUY maxNotional 100 with cancel cleanup."
}' --json
```

Use `rapidx self-check --json` for routine read-only verification. Use `verify-live` only after the user explicitly accepts real-order risk.

## Common Read Commands

```bash
rapidx market get-ticker --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
rapidx portfolio overview --json
rapidx portfolio assets --json
rapidx order open-orders --json
rapidx position query --json
rapidx algo open-orders --json
```

## Order Placement Example

Preview:

```bash
rapidx order place-preview --input '{
  "symbol": "BINANCE_PERP_BTC_USDT",
  "side": "BUY",
  "orderType": "LIMIT",
  "price": "65000",
  "quantity": "0.001",
  "timeInForce": "GTC",
  "maxNotional": "100",
  "clientOrderId": "agent-order-001"
}' --json
```

Submit using the `previewId` and `confirmation.submitToken` returned by preview:

```bash
rapidx order place --input '{
  "symbol": "BINANCE_PERP_BTC_USDT",
  "side": "BUY",
  "orderType": "LIMIT",
  "price": "65000",
  "quantity": "0.001",
  "timeInForce": "GTC",
  "maxNotional": "100",
  "clientOrderId": "agent-order-001",
  "previewId": "rpv_xxx",
  "continueConsentId": "confirm_rpv_xxx"
}' --json
```

Read back:

```bash
rapidx order query --input '{"clientOrderId":"agent-order-001"}' --json
rapidx transaction executions --input '{"symbol":"BINANCE_PERP_BTC_USDT"}' --json
```

## Starting MCP

MCP is started by the CLI:

```bash
rapidx mcp serve
```

The MCP server is not a separate npm package. In normal use, configure this command in the MCP host rather than running it as a one-shot command.

## Automation Sessions

Automation sessions let a user authorize an agent to trade automatically within a bounded scope.

Use automation when the user wants the agent to place, replace, or cancel orders for a period of time without asking for a new chat confirmation for every matching order.

Automation does not skip preview. Each write still goes through preview and submit. The difference is that a preview can be bound to an active automation session, so the matching submit can use the preview's `confirmation.submitToken` without another per-order chat approval.

### Start A Session

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

The response returns:

```json
{
  "automationSessionId": "ras_xxx",
  "status": "ACTIVE",
  "symbols": ["BINANCE_PERP_BTC_USDT"],
  "maxNotionalPerOrder": "100",
  "maxTotalNotional": "1000",
  "usedNotional": "0"
}
```

Agents should keep the `automationSessionId` for the session and pass it into matching previews.

### Use A Session In Preview

```bash
rapidx order place-preview --input '{
  "automationSessionId": "ras_xxx",
  "symbol": "BINANCE_PERP_BTC_USDT",
  "side": "BUY",
  "orderType": "MARKET",
  "quantity": "0.001",
  "maxNotional": "100",
  "clientOrderId": "auto-order-001"
}' --json
```

If the preview matches the session scope, the preview result includes automation-session confirmation information.

Submit with the same business parameters plus `previewId` and `continueConsentId`:

```bash
rapidx order place --input '{
  "automationSessionId": "ras_xxx",
  "symbol": "BINANCE_PERP_BTC_USDT",
  "side": "BUY",
  "orderType": "MARKET",
  "quantity": "0.001",
  "maxNotional": "100",
  "clientOrderId": "auto-order-001",
  "previewId": "rpv_xxx",
  "continueConsentId": "confirm_rpv_xxx"
}' --json
```

### Manage Sessions

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

### Agent Rules For Automation

1. Start automation only after explicit user authorization.
2. Keep the `automationSessionId` for the active workflow.
3. Pass `automationSessionId` into each matching preview.
4. Do not expand symbols, actions, order types, or notional limits without starting a new session.
5. Use `automation status` if unsure whether a session is active.
6. Read back order state after every submit.
7. Stop the session when the user asks to end automation.

## Avoid Shell Wrapper Patterns

Agents should call `rapidx` directly. Avoid:

```bash
cd /some/workspace && node some-mcp-call.js
```

Use a direct command or configure the agent host working directory instead. This avoids shell preflight failures in stricter agent hosts.
