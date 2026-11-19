#!/usr/bin/env python3
"""Which Claude Code session is the coordinator: the marker coordinator_stop.py keys on.

    python3 .claude/hooks/coordinator_session.py register   # the coordinator, at start and after every resume or compaction
    python3 .claude/hooks/coordinator_session.py show       # the registered session, and whether this shell is it
    python3 .claude/hooks/coordinator_session.py clear      # no coordinator: the coordinator-only hooks go quiet

`register` writes .loop/coordinator_session.json ({"session_id", "at"}) with this shell's $CLAUDE_CODE_SESSION_ID, the
id Claude Code gives the session's Bash commands and its hooks' `session_id` (`--session-id ID` instead, when it's
missing).

coordinator_stop.py acts only when the hook input's `session_id` is the registered one **and** the input has no
`agent_id`: a subagent of the coordinator shares its session id but carries an `agent_id`, so it is never blocked;
helper sessions in their own worktrees have other ids. No marker, and the hook does nothing.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _loop  # noqa: E402


def marker_path() -> Path:
    return _loop.project_dir() / ".loop" / "coordinator_session.json"


def marker(path: Optional[Path] = None) -> dict:
    """The registered coordinator ({} when none, or unreadable)."""
    try:
        d = json.loads((path or marker_path()).read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def is_coordinator(data: dict, path: Optional[Path] = None) -> bool:
    """The hook input comes from the registered coordinator's own turn (not one of its subagents)."""
    if data.get("agent_id"):
        return False
    sid = data.get("session_id")
    return bool(sid) and sid == marker(path).get("session_id")


def register(session_id: str, path: Optional[Path] = None) -> dict:
    p = path or marker_path()
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
            print("coordinator_session: no $CLAUDE_CODE_SESSION_ID in this shell; pass --session-id <id> (the name of "
                  "the session's transcript file, without .jsonl)", file=sys.stderr)
            return 1
        register(sid)
        print(f"coordinator_session: registered {sid} in {marker_path()}")
        return 0
    if cmd == "clear":
        try:
            marker_path().unlink()
        except FileNotFoundError:
            pass
        print("coordinator_session: cleared")
        return 0
    if cmd == "show":
        d = marker()
        here = os.getenv("CLAUDE_CODE_SESSION_ID", "")
        at = f" (at {time.strftime('%m-%d %H:%M', time.localtime(d['at']))})" if d.get("at") else ""
        print(f"registered: {d.get('session_id') or 'none'}{at}")
        print(f"this shell: {here or 'unknown'}" + (" (the coordinator)" if here and here == d.get("session_id") else ""))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
