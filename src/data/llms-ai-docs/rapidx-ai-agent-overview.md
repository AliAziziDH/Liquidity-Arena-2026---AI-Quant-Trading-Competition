# RapidX AI Agent Overview

This page helps users choose the right RapidX integration path for an AI agent.

RapidX provides:

- Skills for agent guidance.
- CLI for local command execution and CLI-only agents.
- MCP for structured tool calls in MCP-capable agents.

## Which Path Should I Use?

| Situation | Use |
|---|---|
| The agent host supports skills | Install RapidX skills first |
| The agent host supports MCP | Use RapidX MCP after setup |
| The agent host does not support MCP | Use RapidX CLI with `--json` |
| A human wants to test commands manually | Use RapidX CLI |

The recommended path for most agent users is:

```text
Install RapidX skills
-> use ltp-rapidx-config for setup
-> verify CLI and credentials
-> enable MCP if the host supports MCP
-> run self-check
-> use ltp-rapidx-trading for workflows
```

## What Each Piece Does

| Component | What it does |
|---|---|
| `ltp-rapidx-config` skill | Guides installation, credential setup, MCP setup, update check, and self-check |
| `ltp-rapidx-trading` skill | Guides market reads, portfolio reads, preview-first trading, automation, and readback |
| RapidX CLI | Provides `rapidx ... --json` commands and starts MCP with `rapidx mcp serve` |
| RapidX MCP | Provides structured `rapidx/*` tools for MCP-capable agents |

## Current Release

Use this command to check the current RapidX CLI, MCP schema, and skills versions:

```bash
rapidx update check --json
```

Use `rapidx schema --json` or the MCP `rapidx/tools` tool to discover the current tool count and schemas.

## What Users Need

Before using RapidX, the user or workspace owner must provide:

```text
LTP_ACCESS_KEY
LTP_SECRET_KEY
LTP_API_HOST
```

Users should provide these through the agent host's secret mechanism when available. For chat-only clients, use a private trusted chat and rotate temporary keys after use.

## Symbol Format

RapidX tools require RapidX canonical symbols:

```text
BINANCE_PERP_<BASE>_<QUOTE>
OKX_PERP_<BASE>_<QUOTE>
```

Examples:

```text
BINANCE_PERP_BTC_USDT
BINANCE_PERP_ETH_USDT
OKX_PERP_BTC_USDT
```

If a user says a native Binance symbol such as `BTCUSDT`, agents should normalize it to `BINANCE_PERP_BTC_USDT` before calling RapidX tools.

## First Verification

Read-only verification:

```bash
rapidx self-check --json
```

MCP verification:

```text
rapidx/tools
rapidx/self-check
```

Small live-trade verification:

```bash
rapidx trade verify-live --input '<TradingVerificationInput JSON>' --json
```

`verify-live` submits a real order and requires explicit user consent. Do not use it as a routine health check.

## Where To Go Next

| Goal | Read |
|---|---|
| Install skills | RapidX Agent Skills |
| Use terminal commands | RapidX CLI |
| Configure MCP tools | RapidX MCP |
| Understand safe workflows | RapidX Agent Best Practices |
| Check all commands and tools | RapidX AI Tool Capability Reference |
| Fix setup or runtime issues | RapidX AI Troubleshooting |
