#!/usr/bin/env python3
"""PreToolUse(Bash): kill processes by PID, never by pattern (PLAYBOOK "Spawning a helper"; lesson 2026-10-06).

Blocks `pkill -f <pattern>` (also -fl, -9f…: any short-option cluster with f) and `killall <name>`: a pattern matches
other sessions' processes too (a helper's `pkill -f` killed the master's waiters on 2026-10-06; `killall tccd` resets
macOS permissions). Allowed: `pgrep` (read-only), `kill <pid>`, `pkill <name>` without -f (an exact process name),
`killall -l` / `killall -s` (list signals, dry run).

Fails open on its own errors (the rule in the PLAYBOOK still applies).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _shell  # noqa: E402

INSTEAD = ("Find the PIDs first (`pgrep -fl '[p]attern'`, then `ps -ww -o pid,command -p <pid>` to check each is "
           "yours), then `kill <pid>`. Kill only processes you started.")


def check(cmd: str) -> str | None:
    if "pkill" not in cmd and "killall" not in cmd:
        return None
    for _env, word, args in _shell.commands(cmd):
        base = os.path.basename(word)
        if base == "pkill" and any(a.startswith("-") and not a.startswith("--") and "f" in a[1:] for a in args):
            return ("Blocked by .claude/hooks/kill_rules.py: `pkill -f` matches every process whose command line "
                    "contains the pattern, other sessions' waiters and landers included (2026-10-06). " + INSTEAD)
        if base == "killall" and any(not a.startswith("-") for a in args) and not any(a in ("-l", "-s") for a in args):
            return ("Blocked by .claude/hooks/kill_rules.py: `killall` kills every process with that name, other "
                    "sessions' too (and `killall tccd` resets macOS permissions). " + INSTEAD)
    return None


def main() -> None:
    try:
        data = _shell.read_input()
        msg = check((data.get("tool_input") or {}).get("command") or "") if data.get("tool_name") == "Bash" else None
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("kill_rules", e)
        return
    if msg:
        _shell.block(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
