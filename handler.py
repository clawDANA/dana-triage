#!/usr/bin/env python3
"""
DANA Hook Triage Handler

Automatically triages incoming GitHub hooks (issue/discussion events) and writes
structured ledger events to dana-ledger.

Usage:
    python3 handler.py <hook_message>
    
    OR via stdin:
    echo "[DANA] Hook received: ..." | python3 handler.py

Environment variables:
    DANA_LEDGER_PATH: Path to dana-ledger repo (default: ~/workspace/dana-ledger)
    AGENT_NAME: Agent name for ledger events (default: alephOne)
"""

import sys
import os
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Configuration
LEDGER_PATH = Path(os.getenv("DANA_LEDGER_PATH", 
                              os.path.expanduser("~/.openclaw/workspace/dana-ledger")))
AGENT_NAME = os.getenv("AGENT_NAME", "alephOne")
GH_TOKEN_SCRIPT = os.path.expanduser("~/.openclaw/workspace/tools/get-gh-token-clawdana.py")


def parse_hook_message(message: str) -> dict:
    """Extract structured data from dana-hook-receiver message."""
    lines = message.strip().split("\n")
    data = {}
    
    for line in lines:
        if line.startswith("[DANA] Hook received:"):
            data["event"] = line.split(":", 1)[1].strip()
        elif line.startswith("Issue: #"):
            match = re.match(r"Issue: #(\d+)\s*(.*)", line)
            if match:
                data["issue_number"] = int(match.group(1))
                data["issue_title"] = match.group(2).strip()
        elif line.startswith("https://github.com/"):
            data["url"] = line.strip()
        elif line.startswith("Participants:"):
            participants = line.split(":", 1)[1].strip()
            data["participants"] = [p.strip() for p in participants.split(",")]
    
    return data


def fetch_issue(issue_number: int) -> dict:
    """Fetch full issue content via GitHub API."""
    token = subprocess.check_output(["python3", GH_TOKEN_SCRIPT], text=True).strip()
    
    cmd = [
        "curl", "-s",
        "-H", f"Authorization: token {token}",
        f"https://api.github.com/repos/clawDANA/dana-ledger/issues/{issue_number}"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch issue: {result.stderr}")
    
    return json.loads(result.stdout)


def extract_task_id(title: str) -> str:
    """Extract T-NNNN from issue title."""
    match = re.search(r"(T-\d+)", title)
    return match.group(1) if match else "UNKNOWN"


def triage_issue(hook_data: dict, issue: dict) -> dict:
    """
    Perform triage: analyze issue and decide on action.
    
    Returns ledger event dict.
    """
    task_id = extract_task_id(issue["title"])
    participants = hook_data.get("participants", [])
    
    # Check if I'm a participant
    if AGENT_NAME not in participants:
        return {
            "event": "task.blocked",
            "reason": f"{AGENT_NAME} not in participants list: {', '.join(participants)}",
            "text": f"Issue {issue['number']} received but {AGENT_NAME} is not listed as participant. Cannot claim task.",
            "artifact": issue["html_url"]
        }
    
    # Extract labels
    labels = [label["name"] for label in issue.get("labels", [])]
    priority = next((l for l in labels if l.startswith("priority:")), "normal")
    area = next((l for l in labels if l.startswith("area:")), "unknown")
    kind = next((l for l in labels if l.startswith("kind:")), "unknown")
    
    # Parse body for concrete asks
    body = issue.get("body", "")
    
    # Determine next action
    if "Hook Triage" in issue["title"]:
        # Meta-task: implementing the triage system itself
        next_action = "Create dana-triage skill with handler.py (automated triage) + integrate with hook wake flow"
        horizon = "today"
        risks = "None - have GitHub API access + ledger write capability"
    elif "Hook Reaction" in issue["title"]:
        next_action = "Test dana-triage handler on this issue as first test case"
        horizon = "now"
        risks = "None - this is the test"
    else:
        # General task triage
        next_action = f"Read full issue body, extract requirements, define first concrete step"
        horizon = "today"
        risks = "May need additional context from other agents"
    
    return {
        "event": "task.progress",
        "task": task_id,
        "text": (f"Hook triage completed for issue #{issue['number']}. "
                 f"Priority: {priority}, Area: {area}, Kind: {kind}. "
                 f"Participants: {', '.join(participants)}. "
                 f"Next action: {next_action}. "
                 f"Horizon: {horizon}. Risks: {risks}."),
        "artifact": issue["html_url"]
    }


def write_ledger_event(event_data: dict):
    """Append event to ledger/events.jsonl."""
    ledger_file = LEDGER_PATH / "ledger" / "events.jsonl"
    
    # Add timestamp and agent
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": AGENT_NAME,
        **event_data
    }
    
    # Append to ledger
    with open(ledger_file, "a") as f:
        f.write(json.dumps(event) + "\n")
    
    print(f"✅ Ledger event written: {event['event']} for {event.get('task', 'N/A')}")


def regenerate_views():
    """Run npm run views to update generated files."""
    result = subprocess.run(
        ["npm", "run", "views"],
        cwd=LEDGER_PATH,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to regenerate views: {result.stderr}")
    
    print("✅ Views regenerated")


def commit_and_push(message: str):
    """Commit changes and push to main."""
    # Get token
    token = subprocess.check_output(["python3", GH_TOKEN_SCRIPT], text=True).strip()
    
    # Set remote URL with token
    subprocess.run(
        ["git", "remote", "set-url", "origin",
         f"https://x-access-token:{token}@github.com/clawDANA/dana-ledger.git"],
        cwd=LEDGER_PATH,
        check=True
    )
    
    # Add all changes
    subprocess.run(["git", "add", "-A"], cwd=LEDGER_PATH, check=True)
    
    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=LEDGER_PATH,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0 and "nothing to commit" not in result.stdout:
        raise RuntimeError(f"Failed to commit: {result.stderr}")
    
    # Push
    subprocess.run(["git", "push", "origin", "main"], cwd=LEDGER_PATH, check=True)
    
    print("✅ Changes committed and pushed")


def main():
    # Read hook message from args or stdin
    if len(sys.argv) > 1:
        hook_message = " ".join(sys.argv[1:])
    else:
        hook_message = sys.stdin.read()
    
    # Parse hook message
    hook_data = parse_hook_message(hook_message)
    
    if not hook_data.get("issue_number"):
        print("❌ No issue number found in hook message")
        sys.exit(1)
    
    print(f"🔔 Processing hook: Issue #{hook_data['issue_number']}")
    
    # Fetch full issue
    issue = fetch_issue(hook_data["issue_number"])
    
    # Perform triage
    event = triage_issue(hook_data, issue)
    
    # Write to ledger
    write_ledger_event(event)
    
    # Regenerate views
    regenerate_views()
    
    # Commit and push
    task_id = extract_task_id(issue["title"])
    commit_msg = f"{task_id}: {AGENT_NAME} automated triage (hook handler)"
    commit_and_push(commit_msg)
    
    print(f"✅ Triage complete for issue #{hook_data['issue_number']}")


if __name__ == "__main__":
    main()
