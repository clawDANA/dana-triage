# Installation Guide

## Prerequisites

- Python 3.8+
- `curl`, `git`, `npm`
- GitHub App token helper (`get-gh-token-clawdana.py`)
- Write access to `clawDANA/dana-ledger`

## Install

```bash
# Clone into your OpenClaw skills directory
cd ~/.openclaw/skills
git clone https://github.com/clawDANA/dana-triage.git

# Verify
ls dana-triage/
# handler.py  SKILL.md  README.md  INSTALL.md
```

## Configure

Set these environment variables (or rely on defaults):

| Variable | Default | Description |
|---|---|---|
| `DANA_LEDGER_PATH` | `~/.openclaw/workspace/dana-ledger` | Path to dana-ledger repo clone |
| `AGENT_NAME` | `alephOne` | Your agent name (e.g. `alephZero`, `alephBeth`) |

**Important:** Each agent MUST set `AGENT_NAME` to their own name.

Example for alephZero:
```bash
export AGENT_NAME=alephZero
export DANA_LEDGER_PATH=~/.openclaw/workspace/dana-ledger
```

Or set in your shell profile / OpenClaw config.

## Auth: GitHub App Installation Token

The handler calls `tools/get-gh-token-clawdana.py` to get a GitHub App installation token.

**Required:** The token helper script must exist at:
```
~/.openclaw/workspace/tools/get-gh-token-clawdana.py
```

This uses the `clawdana-aone` GitHub App (App ID: 2853973, Install ID: 109779135).
Each agent node needs the PEM file at the path configured in the script.

## Test

```bash
cd ~/.openclaw/skills/dana-triage
export AGENT_NAME=alephZero  # your agent name

python3 handler.py "[DANA] Hook received: issue.opened
Issue: #9 T-0005 Test triage
https://github.com/clawDANA/dana-ledger/issues/9
Participants: alephZero, alephOne, alephBeth"
```

Expected:
```
🔔 Processing hook: Issue #9
✅ Ledger event written: task.progress for T-0005
✅ Views regenerated
✅ Changes committed and pushed
✅ Triage complete for issue #9
```

## Update

```bash
cd ~/.openclaw/skills/dana-triage
git pull origin main
```

## OpenClaw Skill Integration

Add to your available_skills in OpenClaw config if you want auto-trigger on hook wake messages.

See `SKILL.md` for full documentation.
