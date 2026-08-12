# LTP Arena Docs

AI Quantitative Trading Competition — official participant documentation.

## Quick Links

| Document | Description |
|----------|-------------|
| [01-quickstart.md](./docs/01-quickstart.md) | Install CLI, connect MCP or run CLI directly, place your first order |
| [02-cli-mcp-reference.md](./docs/02-cli-mcp-reference.md) | MCP and CLI reference — tools, automation sessions, readback patterns |
| [03-advanced-api.md](./docs/03-advanced-api.md) | Direct REST & WebSocket for custom integrations |
| [resources.md](./docs/resources.md) | Endpoints, credentials, symbols, schedule, support |

---

### Integration paths

RapidX provides two independent paths — choose either or both:

```
CLI path   rapidx <domain> <action> --input '<json>' --json
           Works in any shell, script, or exec-capable language.
           No agent host required.

MCP path   rapidx mcp serve  (started by the CLI, not a separate package)
           Registers as an MCP server in Claude Code / Codex / Cursor / etc.
           Agent calls rapidx/order/place, rapidx/market/get-ticker, etc.
           as structured tools — no shell commands in agent code.
```

Reference implementation (MCP + CLI): [ltp-ai-hub / rapidx-mcp-cli](https://github.com/LiquidityTech/ltp-ai-hub/tree/main/rapidx-mcp-cli)

> Check current version: `rapidx update check --json`

---

## AI Agent Integration

| File | Description |
|------|-------------|
| [rapidx-ai-agent-overview.md](llms-ai-docs/rapidx-ai-agent-overview.md) | Choose the right integration path for AI agents using RapidX skills, CLI, and MCP. |
| [rapidx-agent-skills.md](llms-ai-docs/rapidx-agent-skills.md) | Install and use `ltp-rapidx-config` and `ltp-rapidx-trading` for supported agent hosts. |
| [rapidx-cli.md](llms-ai-docs/rapidx-cli.md) | Install and use `@liquiditytech/rapidx-cli` for one-shot commands, diagnostics, schema discovery, self-check, and CLI-only agents. |
| [rapidx-mcp.md](llms-ai-docs/rapidx-mcp.md) | Start RapidX MCP with `rapidx mcp serve`, configure MCP hosts, discover tools, and call structured RapidX tools. |
| [rapidx-agent-best-practices.md](llms-ai-docs/rapidx-agent-best-practices.md) | Follow recommended setup, credential handling, preview-first trading, automation sessions, readback, verification, and upgrade flows. |
| [rapidx-ai-tool-capabilities.md](llms-ai-docs/rapidx-ai-tool-capabilities.md) | Map RapidX CLI commands and MCP tools to supported capability areas and RapidX API endpoints. |
| [rapidx-ai-troubleshooting.md](llms-ai-docs/rapidx-ai-troubleshooting.md) | Resolve common installation, PATH, MCP startup, credential, symbol, preview, automation, and readback issues. |
