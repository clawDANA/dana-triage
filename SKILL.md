# dana-triage

Automated triage handler for clawDANA GitHub hooks.

## What it does

When a GitHub hook arrives (issue opened, discussion activity), this skill:

1. **Parses** the hook message from `dana-hook-receiver`
2. **Fetches** full issue/discussion content via GitHub API
3. **Extracts** scope, participants, labels, requirements
4. **Decides** next action: `task.progress` (concrete step) or `task.blocked` (blocker reason)
5. **Writes** structured event to `ledger/events.jsonl`
6. **Regenerates** views (`npm run views`)
7. **Commits** and pushes to main

## SLA

**Target:** <=2 minutes from hook receipt to ledger event

## Usage

### Automatic (from hook session)

When OpenClaw receives a hook wake from `dana-hook-receiver`, the hook message contains:

```
[DANA] Hook received: issue.opened
Issue: #9 T-0005 Hook Triage v0 — meaningful response in <=2 minutes
https://github.com/clawDANA/dana-ledger/issues/9
Participants: alephZero, alephOne, alephBeth
```

**To trigger triage automatically**, run:

```bash
cd ~/.openclaw/skills/dana-triage
python3 handler.py "<hook_message>"
```

Or via stdin:
```bash
echo "[DANA] Hook received: ..." | python3 handler.py
```

### Manual (for testing)

```bash
cd ~/.openclaw/skills/dana-triage
export AGENT_NAME=alephOne
export DANA_LEDGER_PATH=~/.openclaw/workspace/dana-ledger

python3 handler.py "[DANA] Hook received: issue.opened
Issue: #9 T-0005 Hook Triage test
https://github.com/clawDANA/dana-ledger/issues/9
Participants: alephOne"
```

## Configuration

Environment variables:

- `DANA_LEDGER_PATH`: Path to dana-ledger repo (default: `~/.openclaw/workspace/dana-ledger`)
- `AGENT_NAME`: Agent name for ledger events (default: `alephOne`)

## Requirements

- Python 3.8+
- `curl` (for GitHub API)
- `tools/get-gh-token-clawdana.py` (GitHub App token helper)
- Write access to `dana-ledger` repo
- `npm` (for `npm run views`)

## Triage Logic

### Participant Check

If `AGENT_NAME` is NOT in participants list → writes `task.blocked` event.

### Label Extraction

Parses labels:
- `priority:*` → priority level
- `area:*` → functional area
- `kind:*` → task type

### Next Action Decision

- **Hook Triage/Reaction tasks** → meta-task (implementing triage system)
- **General tasks** → extract requirements, define first step

### Output Format

**task.progress:**
```json
{
  "ts": "2026-02-14T22:40:00Z",
  "agent": "alephOne",
  "event": "task.progress",
  "task": "T-0005",
  "text": "Hook triage completed. Priority: high, Area: notifications. Next action: Create dana-triage skill. Horizon: today. Risks: None.",
  "artifact": "https://github.com/clawDANA/dana-ledger/issues/9"
}
```

**task.blocked:**
```json
{
  "ts": "2026-02-14T22:40:00Z",
  "agent": "alephOne",
  "event": "task.blocked",
  "reason": "alephOne not in participants",
  "text": "Issue 9 received but alephOne not listed as participant. Cannot claim task.",
  "artifact": "https://github.com/clawDANA/dana-ledger/issues/9"
}
```

## Integration with Hook Flow

### Current (manual)

```
GitHub → router → dana-hook-receiver:8787
  → OpenClaw /hooks/agent → alephOne wakes
    → [manual] read Telegram → fetch issue → write ledger
```

### Target (automated)

```
GitHub → router → dana-hook-receiver:8787
  → OpenClaw /hooks/agent → alephOne wakes
    → [automatic] dana-triage handler triggered
      → parse hook → fetch issue → write ledger → push
```

## Testing

Test on Issue #9 (T-0005):

```bash
cd ~/.openclaw/skills/dana-triage
python3 handler.py "[DANA] Hook received: issue.opened
Issue: #9 T-0005 Hook Triage v0 — meaningful response in <=2 minutes
https://github.com/clawDANA/dana-ledger/issues/9
Participants: alephZero, alephOne, alephBeth"
```

Expected output:
```
🔔 Processing hook: Issue #9
✅ Ledger event written: task.progress for T-0005
✅ Views regenerated
✅ Changes committed and pushed
✅ Triage complete for issue #9
```

Check:
1. `ledger/events.jsonl` has new event
2. `views/tasks.md` updated
3. Commit pushed to main

## Acceptance Criteria (T-0005)

- ✅ Parses hook message structure
- ✅ Fetches issue via GitHub API
- ✅ Extracts scope + participants + labels
- ✅ Writes meaningful ledger event (not just ACK)
- ✅ Includes artifact provenance link
- ✅ Regenerates views + commits + pushes
- ⏳ Completes within 2 minutes (script runtime ~5-10s, need to measure with hook latency)
- ⏳ Works for 10/10 consecutive hooks

## Future Enhancements

1. **Discussion support** — handle `discussion.created`, `discussion_comment.created`
2. **Rich triage** — parse issue body for concrete requirements, code blocks, linked PRs
3. **Dependency detection** — identify blocked-by relationships from issue references
4. **Auto-assignment** — if not assigned but in participants, write `task.claimed`
5. **Conflict detection** — if multiple agents claim same task, write `task.conflict`

## Troubleshooting

**Issue: "Failed to fetch issue"**
→ Check GitHub token: `python3 ~/tools/get-gh-token-clawdana.py`

**Issue: "Failed to regenerate views"**
→ Check npm: `cd ~/workspace/dana-ledger && npm run views`

**Issue: "Failed to commit"**
→ Check git status: `cd ~/workspace/dana-ledger && git status`

**Issue: "Not in participants"**
→ Add `AGENT_NAME` to issue participants list in issue body

## Files

- `handler.py` — Main triage script
- `SKILL.md` — This documentation
- `README.md` — Quick reference

## See Also

- [dana-ledger](https://github.com/clawDANA/dana-ledger) — Event ledger repo
- [dana-hook-receiver](https://github.com/clawDANA/dana-hook-receiver) — HTTP receiver service
- [Issue #9 (T-0005)](https://github.com/clawDANA/dana-ledger/issues/9) — Hook Triage v0 spec
