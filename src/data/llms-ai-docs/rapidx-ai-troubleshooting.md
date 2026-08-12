# RapidX AI Troubleshooting

This page explains common points of confusion for RapidX CLI, MCP, and Skills.

## What Are RapidX Skills?

RapidX skills are instruction files loaded by an agent host. They teach the agent how to install RapidX CLI, configure credentials, configure MCP, run self-check, and operate RapidX.

Users do not call a skill through RapidX API. Users install the skills into their agent host, then ask the agent to follow `ltp-rapidx-config` first.

## The Agent Uses CLI Even Though MCP Is Available

Cause: the agent has not verified MCP tool discovery, or the host did not load RapidX MCP.

Fix:

1. Confirm MCP config uses `rapidx mcp serve`.
2. Restart or reload the MCP host.
3. Discover tools with `rapidx/tools`.
4. Use MCP tools for normal operation.
5. Use CLI as fallback for CLI-only hosts.

## `rapidx mcp serve` Looks Stuck

Cause: `rapidx mcp serve` starts a long-running stdio MCP server. It is not a one-shot command.

Fix: configure it in the MCP host. Use `rapidx self-check --json` for one-shot local verification.

## MCP Server Fails With ENOENT

Error example:

```text
spawn rapidx mcp serve ENOENT
```

Cause: the MCP host cannot find the `rapidx` binary.

Fix:

1. Install CLI globally.
2. Run `which rapidx`.
3. Use the absolute path in MCP config if the host does not inherit shell `PATH`.
4. Restart the MCP host.

## Missing `LTP_API_HOST`

Required values:

```text
LTP_ACCESS_KEY
LTP_SECRET_KEY
LTP_API_HOST
```

Fix: provide the API host from the environment or workspace owner, together with access key and secret key.

## Credentials In Chat Clients

Use the safest available channel:

1. User-provided secret mechanism.
2. MCP config environment variables.
3. Shell environment variables.
4. Private trusted chat only when no safer channel exists.

For Telegram or similar chat-only clients, explain that messages may be stored by the chat service. Do not use group chats or public channels for credentials. Recommend rotating temporary keys after use.

## Native Exchange Symbol Does Not Work

RapidX tools require RapidX canonical symbols:

```text
BINANCE_PERP_<BASE>_<QUOTE>
OKX_PERP_<BASE>_<QUOTE>
```

Examples:

```text
BTCUSDT -> BINANCE_PERP_BTC_USDT
ETHUSDT -> BINANCE_PERP_ETH_USDT
```

## Preview Submit Fails

Common causes:

- Preview and submit happened in different runtimes.
- Business parameters changed between preview and submit.
- `previewId` is missing or stale.
- `continueConsentId` is missing or does not match the preview.

Fix:

- CLI preview must be submitted with CLI.
- MCP preview must be submitted with MCP.
- Submit with unchanged business parameters.
- Include `previewId` and `continueConsentId`.

## Automation Does Not Submit Automatically

Automation sessions do not place orders by themselves.

The agent still needs to:

```text
preview with automationSessionId
-> submit with previewId and continueConsentId
-> readback
```

If automation preview is blocked, check:

- session is active
- symbol is allowed
- action is allowed
- order type is allowed
- max notional per order is not exceeded
- total notional is not exceeded

## Submit Response Is Not Final State

After writes, always read back:

| Operation | Readback |
|---|---|
| place | `order query`, then `transaction executions` if filled |
| replace | `order query` |
| cancel | `order query` or `order open-orders` |
| close position | `position query` |
| algo write | `algo query` or `algo open-orders` |

Cancel can be asynchronous. A successful cancel response can mean the request was accepted, not that the order is already terminal.

## Position Close Fails In NET Mode

For `position.close`:

- Do not pass `side`.
- Do not pass `quantity`.
- In NET mode, omit `positionSide`.
- In HEDGE mode, pass `LONG` or `SHORT`.

If a read API returns `positionSide="NONE"` for NET mode, do not pass `"NONE"` to `position.close`.

## Self-Check vs Live Verification

Self-check:

```bash
rapidx self-check --json
```

Purpose: read-only integration verification.

Live verification:

```bash
rapidx trade verify-live --input '<TradingVerificationInput JSON>' --json
```

Purpose: explicit small real-trade verification. It submits a real order and requires user consent.

Do not use live verification as a routine health check.

## Chained Shell Commands Are Blocked

Some agent hosts reject commands like:

```bash
cd /workspace && node script.js
```

Use direct `rapidx` commands:

```bash
rapidx self-check --json
```

Or configure the working directory through the agent host tool settings.
