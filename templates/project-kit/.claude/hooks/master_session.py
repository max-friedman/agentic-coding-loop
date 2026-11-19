#!/usr/bin/env python3
"""Which Claude Code session is the master: the marker the master-only hooks key on (robustness plan section 8).

    python3 .claude/hooks/master_session.py register   # the master, at start and after every resume or compaction
    python3 .claude/hooks/master_session.py show       # the registered session, and whether this shell is it
    python3 .claude/hooks/master_session.py clear      # no master: the master-only hooks go quiet

`register` writes feedback/master_session.json ({"session_id", "at"}) with this shell's $CLAUDE_CODE_SESSION_ID, the
id Claude Code gives the session's Bash commands and its hooks' `session_id` (`--session-id ID` instead, when it's
missing). Optional fields the master may add by hand: `monitor_command` and `checkin_command`, the exact calls the Stop
hook's message quotes (defaults below).

`master_stop.py` (Stop) and `master_digest.py` (UserPromptSubmit) act only when the hook input's `session_id` is the
registered one **and** the input has no `agent_id`: a helper subagent of the master shares its session id but carries
an `agent_id`, so it is never blocked; other sessions (helpers in their own worktrees, the feedback loop's builders)
have other ids. No marker, or a stale one, and both hooks do nothing.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

FEEDBACK = Path(os.getenv("LOOP_HOME") or Path.home() / ".loop").expanduser() / "feedback"
MARKER = FEEDBACK / "master_session.json"

# The calls the Stop hook's message quotes, unless the marker names its own.
MONITOR_COMMAND = ('Monitor(description="master_events: the master\'s event stream", timeout_ms=1800000, '
                   'command="cd <live-checkout> && python3 -u scripts/master_events.py")')
CHECKIN_COMMAND = ('CronCreate(cron="7,37 * * * *", recurring=true, prompt="Master check-in: touch '
                   '~/.loop/feedback/master_heartbeat, then run the 30-minute checklist '
                   '(PLAYBOOK, Watching)")')


def marker(path: Optional[Path] = None) -> dict:
    """The registered master ({} when none, or unreadable)."""
    try:
        d = json.loads((path or MARKER).read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def is_master(data: dict, path: Optional[Path] = None) -> bool:
    """The hook input comes from the registered master's own turn (not one of its subagents)."""
    if data.get("agent_id"):
        return False
    sid = data.get("session_id")
    return bool(sid) and sid == marker(path).get("session_id")


def register(session_id: str, path: Optional[Path] = None) -> dict:
    p = path or MARKER
    d = marker(p)
    d.update({"session_id": session_id, "at": int(time.time())})
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(d, indent=1) + "\n")
    os.replace(tmp, p)
    return d


def main(argv: list) -> int:
    cmd = argv[0] if argv else "show"
    if cmd == "register":
        sid = argv[2] if len(argv) > 2 and argv[1] == "--session-id" else os.getenv("CLAUDE_CODE_SESSION_ID", "")
        if not sid:
            print("master_session: no $CLAUDE_CODE_SESSION_ID in this shell; pass --session-id <id> (the name of the "
                  "session's transcript file, without .jsonl)", file=sys.stderr)
            return 1
        register(sid)
        print(f"master_session: registered {sid} in {MARKER}")
        return 0
    if cmd == "clear":
        try:
            MARKER.unlink()
        except FileNotFoundError:
            pass
        print("master_session: cleared")
        return 0
    if cmd == "show":
        d = marker()
        here = os.getenv("CLAUDE_CODE_SESSION_ID", "")
        print(f"registered: {d.get('session_id') or 'none'}" + (f" (at {time.strftime('%m-%d %H:%M', time.localtime(d['at']))})" if d.get("at") else ""))
        print(f"this shell: {here or 'unknown'}" + (" (the master)" if here and here == d.get("session_id") else ""))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
