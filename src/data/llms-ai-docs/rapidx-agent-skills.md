# RapidX Agent Skills

RapidX skills are instruction packages for AI agents. They tell the agent how to install RapidX CLI, configure credentials and MCP, verify access, and operate RapidX through the correct workflow.

Skills repository:

```text
https://github.com/LiquidityTech/ltp-rapidx-skill
```

## Included Skills

| Skill | Purpose |
|---|---|
| `ltp-rapidx-config` | Install or upgrade CLI, configure credentials, configure MCP, discover tools, run self-check, and review integration state |
| `ltp-rapidx-trading` | Use MCP or CLI for market reads, portfolio reads, order workflows, positions, algo orders, automation, preview, submit, and readback |

Use `ltp-rapidx-config` first for installation and configuration. Use `ltp-rapidx-trading` after RapidX is verified.

Skills are installed into the agent host. They are separate from `@liquiditytech/rapidx-cli` and are not shipped inside the npm package.

## Install By Agent Host

Choose the section that matches your agent host. Each section provides two paths:

- Option A: install the skills manually.
- Option B: send an instruction to the agent and let it install the skills.

### Codex

#### Option A: Install Manually

Use the Codex skill installer, or run this command in the Codex workspace:

```bash
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git \
  --skill ltp-rapidx-config ltp-rapidx-trading \
  -a codex -y
```

After installation, ask Codex to follow `ltp-rapidx-config`.

#### Option B: Ask Codex To Install

Send this to Codex:

```text
Install RapidX skills for this Codex workspace.

Run:
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git --skill ltp-rapidx-config ltp-rapidx-trading -a codex -y

After installation, follow ltp-rapidx-config first to install or upgrade @liquiditytech/rapidx-cli, configure credentials, configure MCP if supported, and run self-check.
After RapidX is verified, follow ltp-rapidx-trading for market, portfolio, order, position, algo, and automation workflows.
```

### Claude Code

#### Option A: Install Manually

```bash
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git \
  --skill ltp-rapidx-config ltp-rapidx-trading \
  -a claude-code -y
```

Manual fallback: copy both skill folders into the project or user Claude skills directory supported by the host.

After installation, ask Claude Code to follow `ltp-rapidx-config`.

#### Option B: Ask Claude Code To Install

Send this to Claude Code:

```text
Install RapidX skills for this Claude Code workspace.

Run:
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git --skill ltp-rapidx-config ltp-rapidx-trading -a claude-code -y

After installation, load ltp-rapidx-config first, complete CLI/MCP configuration and self-check, then use ltp-rapidx-trading for RapidX operations.
```

### Cursor

#### Option A: Install Manually

```bash
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git \
  --skill ltp-rapidx-config ltp-rapidx-trading \
  -a cursor -y
```

Manual fallback: copy both skill folders into the Cursor-supported skills directory for the current workspace or user profile.

After installation, ask Cursor to follow `ltp-rapidx-config`.

#### Option B: Ask Cursor To Install

Send this to Cursor:

```text
Install RapidX skills for this Cursor workspace.

Run:
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git --skill ltp-rapidx-config ltp-rapidx-trading -a cursor -y

Use ltp-rapidx-config first to set up RapidX CLI/MCP and verify access, then use ltp-rapidx-trading for trading workflows.
```

### OpenCode

#### Option A: Install Manually

```bash
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git \
  --skill ltp-rapidx-config ltp-rapidx-trading \
  -a opencode -y
```

After installation, ask OpenCode to follow `ltp-rapidx-config`.

#### Option B: Ask OpenCode To Install

Send this to OpenCode:

```text
Install RapidX skills for this OpenCode workspace.

Run:
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git --skill ltp-rapidx-config ltp-rapidx-trading -a opencode -y

Follow ltp-rapidx-config before any RapidX query or trading action.
```

### OpenClaw

#### Option A: Install Manually

RapidX skills are published to ClawHub:

```bash
openclaw skills install ltp-rapidx-config
openclaw skills install ltp-rapidx-trading
```

After installation, ask OpenClaw to follow `ltp-rapidx-config`.

#### Option B: Ask OpenClaw To Install

Send this to OpenClaw:

```text
Install RapidX skills from ClawHub for this OpenClaw workspace.

Run:
openclaw skills install ltp-rapidx-config
openclaw skills install ltp-rapidx-trading

After installation, follow ltp-rapidx-config first. Configure CLI/MCP access, run self-check, and only then use ltp-rapidx-trading.
```

### Hermes

#### Option A: Install Manually

```bash
hermes skills install LiquidityTech/ltp-rapidx-skill/skills/ltp-rapidx-config
hermes skills install LiquidityTech/ltp-rapidx-skill/skills/ltp-rapidx-trading
```

After installation, ask Hermes to follow `ltp-rapidx-config`.

#### Option B: Ask Hermes To Install

Send this to Hermes:

```text
Install both RapidX skills for this Hermes environment.

Run:
hermes skills install LiquidityTech/ltp-rapidx-skill/skills/ltp-rapidx-config
hermes skills install LiquidityTech/ltp-rapidx-skill/skills/ltp-rapidx-trading

After installation, follow ltp-rapidx-config first, then ltp-rapidx-trading.
```

### Gemini CLI

#### Option A: Install Manually

If the environment supports the general skills installer:

```bash
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git \
  --skill ltp-rapidx-config ltp-rapidx-trading \
  -a gemini-cli -y
```

If skills are not supported in the user's Gemini CLI environment, use RapidX CLI or MCP directly.

After installation, ask Gemini CLI to follow `ltp-rapidx-config`.

#### Option B: Ask Gemini CLI To Install

Send this to Gemini CLI:

```text
If this Gemini CLI environment supports Agent Skills, install RapidX skills from https://github.com/LiquidityTech/ltp-rapidx-skill.git.

Run:
npx skills add https://github.com/LiquidityTech/ltp-rapidx-skill.git --skill ltp-rapidx-config ltp-rapidx-trading -a gemini-cli -y

If skills are not supported, use @liquiditytech/rapidx-cli directly and run rapidx self-check --json before any trading workflow.
```

## Manual Installation

Clone:

```bash
git clone https://github.com/LiquidityTech/ltp-rapidx-skill.git
```

Copy both directories into the target agent's supported skills directory:

```text
skills/ltp-rapidx-config
skills/ltp-rapidx-trading
```

Reload or restart the agent after copying.

## After Installation

The agent should report one of these states before it starts market queries or trading:

| State | Meaning |
|---|---|
| `MCP_READY` | MCP server is configured, tools are discoverable, and self-check passed |
| `CLI_ONLY_READY` | MCP is unavailable, but CLI is installed, credentials resolve, and self-check passed |
| `NOT_VERIFIED` | Setup is incomplete or self-check failed |

## Upgrade

Check versions:

```bash
rapidx update check --json
```

Upgrade order:

1. Upgrade or reinstall RapidX skills.
2. Upgrade RapidX CLI.
3. Restart or reload the agent/MCP host.
4. Run `rapidx self-check --json`.
