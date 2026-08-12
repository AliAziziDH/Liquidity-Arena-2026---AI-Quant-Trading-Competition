# RapidX Agent Best Practices

This page describes how users and agents should operate RapidX in common scenarios.

## Scenario 1: First-Time Setup

Use `ltp-rapidx-config`.

The agent should:

1. Install or upgrade `@liquiditytech/rapidx-cli`.
2. Configure `LTP_ACCESS_KEY`, `LTP_SECRET_KEY`, and `LTP_API_HOST`.
3. Check whether the host supports MCP.
4. Run `rapidx self-check --json`.
5. If MCP is available, run `rapidx/tools` and `rapidx/self-check`.
6. Report one state: `MCP_READY`, `CLI_ONLY_READY`, or `NOT_VERIFIED`.

The agent should not trade while the runtime is `NOT_VERIFIED`.

## Scenario 2: Read-Only Queries

For MCP-capable agents, prefer MCP tools.

For CLI-only agents, use:

```bash
rapidx <domain> <action> --input '<json>' --json
```

Read-only workflows should still include evidence. The agent should report which command or tool produced the result.

Common readback commands and tools:

| Goal | CLI | MCP tool |
|---|---|---|
| Portfolio overview | `rapidx portfolio overview --json` | `rapidx/portfolio/overview` |
| Portfolio assets | `rapidx portfolio assets --json` | `rapidx/portfolio/assets` |
| Open orders | `rapidx order open-orders --json` | `rapidx/order/open-orders` |
| Order detail | `rapidx order query --input '<json>' --json` | `rapidx/order/query` |
| Positions | `rapidx position query --json` | `rapidx/position/query` |
| Executions | `rapidx transaction executions --input '<json>' --json` | `rapidx/transaction/executions` |
| Open algo orders | `rapidx algo open-orders --json` | `rapidx/algo/open-orders` |
| Algo order detail | `rapidx algo query --input '<json>' --json` | `rapidx/algo/query` |

## Scenario 3: Human-Confirmed Trading

Use preview-first writes.

Agent workflow:

1. Query current state.
2. Build input from `rapidx schema --json` or `rapidx/tools`.
3. Call preview.
4. Present the preview summary to the user.
5. Submit only after user confirmation.
6. Read back final state.

Order example:

```text
order place-preview -> order place -> order query -> transaction executions if filled
order replace-preview -> order replace -> order query
order cancel-preview -> order cancel -> order query or order open-orders
```

Preview ids are runtime-local. Do not mix CLI preview with MCP submit.

## Scenario 4: Automated Trading

Use automation sessions when the user wants the agent to trade within a pre-approved scope.

The user should define:

- symbols
- max notional per order
- max total notional
- duration
- allowed actions
- allowed order types

Agent workflow:

```text
automation start
-> preview with automationSessionId
-> submit with previewId and continueConsentId
-> readback
-> automation status when needed
-> automation extend or stop
```

Automation does not skip preview. It lets a matching preview use the active automation session instead of asking for another chat confirmation per order.

## Scenario 5: Order State Confirmation

Do not treat a submit response as final state.

After write operations:

| Operation | Readback |
|---|---|
| place | `order query`, then `transaction executions` if filled |
| replace | `order query` |
| cancel | `order query` or `order open-orders` |
| cancel-all | `order open-orders` |
| close position | `position query` |
| algo place/replace/cancel | `algo query` or `algo open-orders` |

Cancel can be asynchronous. A successful cancel response can mean the cancel request was accepted, not that the order is already terminal.

## Scenario 6: Credentials In Chat Clients

Preferred order:

1. Agent host user-provided secrets.
2. MCP config environment variables managed by the workspace.
3. Shell environment variables managed by the user.
4. Private trusted chat only when no safer channel exists.

For chat-only clients such as Telegram:

- Explain that chat services may store messages.
- Use private chat only.
- Never use group chats or public channels.
- Recommend rotating or revoking temporary keys after the session or event ends.
- Never print full keys back to the user.

## Scenario 7: Upgrade

Run:

```bash
rapidx update check --json
```

Upgrade order:

1. Upgrade or reinstall RapidX skills.
2. Upgrade RapidX CLI.
3. Restart or reload the agent/MCP host.
4. Run CLI self-check with `rapidx self-check --json`.
5. If MCP is enabled, run MCP self-check with `rapidx/self-check`.

## Agent Rules

- Use runtime schema before constructing inputs.
- Use RapidX canonical symbols.
- Use MCP tools when MCP is available.
- Use CLI with `--json` when MCP is unavailable.
- Read back after writes.
- Do not trade when self-check is `NOT_VERIFIED`.
- Do not fake results.
