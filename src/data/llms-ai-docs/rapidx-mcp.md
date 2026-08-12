# RapidX MCP

RapidX MCP exposes RapidX capabilities as structured MCP tools under the `rapidx/*` namespace.

Start the MCP server with:

```bash
rapidx mcp serve
```

MCP is started by the CLI. It is not a separate npm package.

## MCP Host Configuration

Example MCP configuration:

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

If the agent host cannot resolve `rapidx`, use the absolute path returned by:

```bash
which rapidx
```

## Discovery And Schema

After startup, agents should call:

```text
rapidx/tools
```

Expected MCP tool count for the current release: `46`.

`rapidx/tools` returns:

```text
schemaVersion
inputSchemas
tools[]
```

Each tool includes:

```json
{
  "name": "rapidx/order/place-preview",
  "riskLevel": "trade-write",
  "inputSchema": "PreviewOrderInput",
  "outputSchema": "PreviewOrderResult",
  "previewRequired": false,
  "containsRealOrder": false,
  "requiresExplicitHumanConfirmation": false
}
```

To construct a tool input:

1. Find the tool by `name`.
2. Read its `inputSchema`.
3. Look up that schema in `inputSchemas`.
4. Send only fields allowed by the schema.

## Diagnostic Tools

| MCP tool | Purpose |
|---|---|
| `rapidx/tools` | Discover tool surface and schemas |
| `rapidx/self-check` | Run read-only integration self-check |
| `rapidx/update/check` | Check CLI, MCP schema, and skills version status |

## Common Tool Groups

Market:

```text
rapidx/market/get-ticker
rapidx/market/get-orderbook
rapidx/market/get-klines
rapidx/market/get-funding-rate
rapidx/market/get-mark-price
rapidx/market/get-symbol-info
rapidx/market/get-open-interest
```

Portfolio:

```text
rapidx/portfolio/overview
rapidx/portfolio/assets
rapidx/portfolio/statement
rapidx/portfolio/user-fee-rate
rapidx/portfolio/position-bracket
rapidx/portfolio/set-position-mode
```

Orders:

```text
rapidx/order/place-preview
rapidx/order/place
rapidx/order/replace-preview
rapidx/order/replace
rapidx/order/cancel-preview
rapidx/order/cancel
rapidx/order/cancel-all
rapidx/order/query
rapidx/order/open-orders
rapidx/order/history
```

Transactions, positions, and algo:

```text
rapidx/transaction/executions
rapidx/position/query
rapidx/position/history
rapidx/position/get-leverage
rapidx/position/set-leverage
rapidx/position/close
rapidx/position/close-all
rapidx/algo/place
rapidx/algo/replace
rapidx/algo/cancel
rapidx/algo/open-orders
rapidx/algo/history
rapidx/algo/query
```

## MCP Write Flow

Agents should use preview-first writes:

1. Call the matching preview tool, such as `rapidx/order/place-preview`.
2. Read `previewId` and `confirmation.submitToken`.
3. Submit through the matching write tool, such as `rapidx/order/place`.
4. Pass unchanged business parameters, `previewId`, and `continueConsentId`.
5. Read back order, position, transaction, or algo state after submit.

Example preview input:

```json
{
  "symbol": "BINANCE_PERP_BTC_USDT",
  "side": "BUY",
  "orderType": "LIMIT",
  "price": "65000",
  "quantity": "0.001",
  "timeInForce": "GTC",
  "maxNotional": "100",
  "clientOrderId": "agent-order-001"
}
```

Example submit input:

```json
{
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
}
```

Preview ids are runtime-local. MCP preview ids cannot be submitted through CLI.

## Automation With MCP

Automation sessions are created with:

```text
rapidx/automation/start
```

Agents should pass `automationSessionId` into supported preview tools. Automation scope is checked during preview and again during submit.

Automation tools:

```text
rapidx/automation/start
rapidx/automation/list
rapidx/automation/status
rapidx/automation/extend
rapidx/automation/stop
```

## Self-Check

Use `rapidx/self-check` for read-only MCP verification. It checks discovery, schema, credentials, market reads, portfolio reads, order reads, and position reads when credentials are available.

Do not use live trading verification as a routine health check.
