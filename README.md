# dana-triage — Quick Reference

Automated triage for clawDANA GitHub hooks. Parses hook messages, fetches issues, writes ledger events.

## Quick Test

```bash
cd ~/.openclaw/skills/dana-triage
python3 handler.py "[DANA] Hook received: issue.opened
Issue: #9 T-0005 Test
https://github.com/clawDANA/dana-ledger/issues/9
Participants: alephOne"
```

## Integration

From OpenClaw hook session:
```python
import subprocess
hook_msg = """[DANA] Hook received: issue.opened
Issue: #9 Title
https://github.com/clawDANA/dana-ledger/issues/9
Participants: alephOne"""

subprocess.run([
    "python3",
    "/home/ubuntu/.openclaw/skills/dana-triage/handler.py",
    hook_msg
])
```

## See SKILL.md for full documentation
