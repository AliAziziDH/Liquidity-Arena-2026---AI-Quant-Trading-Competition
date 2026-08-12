# RapidX AI Tool Capability Reference

This page maps RapidX CLI commands and MCP tools to their main capability areas.

Use `rapidx schema --json` or `rapidx/tools` as the source of truth for the current runtime.

Use these runtime commands to check current versions, tool count, and schemas:

```bash
rapidx update check --json
rapidx schema --json
```

## Schema Discovery

CLI:

```bash
rapidx schema --json
```

MCP:

```text
rapidx/tools
```

Use the returned `capabilities` and `inputSchemas` before constructing any command or tool input.

## Diagnostics

| CLI | MCP tool | Purpose |
|---|---|---|
| `rapidx schema --json` | `rapidx/tools` | Discover capabilities and schemas |
| `rapidx self-check --json` | `rapidx/self-check` | Read-only self-check |
| `rapidx update check --json` | `rapidx/update/check` | Version and compatibility check |
| `rapidx auth check --json` | - | Credential resolution check |
| `rapidx doctor --json` | - | Local diagnostics |

## Automation

| CLI | MCP tool | Purpose |
|---|---|---|
| `rapidx automation start` | `rapidx/automation/start` | Create automation session |
| `rapidx automation list` | `rapidx/automation/list` | List sessions |
| `rapidx automation status` | `rapidx/automation/status` | Read session status |
| `rapidx automation extend` | `rapidx/automation/extend` | Extend a session |
| `rapidx automation stop` | `rapidx/automation/stop` | Stop a session |

Automation sessions are local authorization state, not RapidX HTTP endpoints.

## Market

| CLI | MCP tool | Main source |
|---|---|---|
| `rapidx market get-ticker` | `rapidx/market/get-ticker` | Venue market data adapter |
| `rapidx market get-orderbook` | `rapidx/market/get-orderbook` | Venue market data adapter |
| `rapidx market get-klines` | `rapidx/market/get-klines` | Venue market data adapter |
| `rapidx market get-open-interest` | `rapidx/market/get-open-interest` | Venue market data adapter |
| `rapidx market get-funding-rate` | `rapidx/market/get-funding-rate` | `GET /api/v1/market/fundingRate` |
| `rapidx market get-mark-price` | `rapidx/market/get-mark-price` | `GET /api/v1/market/markPrice` |
| `rapidx market get-symbol-info` | `rapidx/market/get-symbol-info` | `GET /api/v1/trading/sym/info` |

## Portfolio

| CLI | MCP tool | RapidX API |
|---|---|---|
| `rapidx portfolio overview` | `rapidx/portfolio/overview` | `GET /api/v1/trading/account` |
| `rapidx portfolio assets` | `rapidx/portfolio/assets` | `GET /api/v1/trading/portfolio/assets` |
| `rapidx portfolio statement` | `rapidx/portfolio/statement` | `GET /api/v1/trading/statement` |
| `rapidx portfolio user-fee-rate` | `rapidx/portfolio/user-fee-rate` | `GET /api/v1/trading/userFeeRate` |
| `rapidx portfolio position-bracket` | `rapidx/portfolio/position-bracket` | `GET /api/v1/trading/positionBracket` |
| `rapidx portfolio set-position-mode` | `rapidx/portfolio/set-position-mode` | `POST /api/v1/trading/account` |

## Orders

| CLI | MCP tool | RapidX API |
|---|---|---|
| `rapidx order place-preview` | `rapidx/order/place-preview` | Preview preflight, including symbol rules |
| `rapidx order place` | `rapidx/order/place` | `POST /api/v1/trading/order` |
| `rapidx order replace-preview` | `rapidx/order/replace-preview` | Preview preflight, including order readback |
| `rapidx order replace` | `rapidx/order/replace` | `PUT /api/v1/trading/order` |
| `rapidx order cancel-preview` | `rapidx/order/cancel-preview` | Preview preflight, including order readback |
| `rapidx order cancel` | `rapidx/order/cancel` | `DELETE /api/v1/trading/order` |
| `rapidx order cancel-all` | `rapidx/order/cancel-all` | `DELETE /api/v1/trading/cancelAll` |
| `rapidx order query` | `rapidx/order/query` | `GET /api/v1/trading/order` |
| `rapidx order open-orders` | `rapidx/order/open-orders` | `GET /api/v1/trading/orders` |
| `rapidx order history` | `rapidx/order/history` | `GET /api/v1/trading/history/orders` |

## Transactions

| CLI | MCP tool | RapidX API |
|---|---|---|
| `rapidx transaction executions` | `rapidx/transaction/executions` | `GET /api/v1/trading/executions` |

## Positions

| CLI | MCP tool | RapidX API |
|---|---|---|
| `rapidx position query` | `rapidx/position/query` | `GET /api/v1/trading/position` |
| `rapidx position history` | `rapidx/position/history` | `GET /api/v1/trading/history/position` |
| `rapidx position get-leverage` | `rapidx/position/get-leverage` | `GET /api/v1/trading/perp/leverage` |
| `rapidx position set-leverage` | `rapidx/position/set-leverage` | `POST /api/v1/trading/position/leverage` |
| `rapidx position close` | `rapidx/position/close` | `DELETE /api/v1/trading/position` |
| `rapidx position close-all` | `rapidx/position/close-all` | `DELETE /api/v1/trading/positions` |

## Algo Orders

| CLI | MCP tool | RapidX API |
|---|---|---|
| `rapidx algo place` | `rapidx/algo/place` | `POST /api/v1/algo/order` |
| `rapidx algo replace` | `rapidx/algo/replace` | `PUT /api/v1/algo/order` |
| `rapidx algo cancel` | `rapidx/algo/cancel` | `DELETE /api/v1/algo/order` |
| `rapidx algo open-orders` | `rapidx/algo/open-orders` | `GET /api/v1/algo/openOrders` |
| `rapidx algo history` | `rapidx/algo/history` | `GET /api/v1/algo/history/orders` |
| `rapidx algo query` | `rapidx/algo/query` | `GET /api/v1/algo/order` |

## Advanced Preview And Verification

| CLI | MCP tool | Purpose |
|---|---|---|
| `rapidx trade preview` | `rapidx/trade/preview` | Advanced generic preview for write capabilities without a dedicated preview tool |
| `rapidx trade verify-live` | `rapidx/trade/verify-live` | Explicit small live-trade verification |

Use concrete order preview tools for normal order workflows:

```text
rapidx/order/place-preview
rapidx/order/replace-preview
rapidx/order/cancel-preview
```

Agents should not use generic `trade preview` for normal order placement, replacement, or cancellation.
