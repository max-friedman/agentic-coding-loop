#!/usr/bin/env python3
"""PreToolUse hook (Bash): kill only PIDs you started; no kill by name pattern.

With several agents on one machine, `pkill -f land.py` from one agent also kills the
same-named processes of every other agent. In the project behind this repo, a
helper's pattern kill took out the coordinator's landing waiters. Blocked: `pkill`
and `killall` in any form. Allowed: `kill <pid>`, with the PID you recorded when you
started the process.

Fails open on its own errors.
"""
from __future__ import annotations

import json
import shlex
import sys


def check(cmd: str) -> str | None:
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()")
    lex.whitespace_split = True
    try:
        words = list(lex)
    except ValueError:
        words = cmd.split()
    for i, word in enumerate(words):
        name = word.rsplit("/", 1)[-1]
        at_start = i == 0 or words[i - 1] in {";", "&&", "||", "|", "&", "(", "sudo", "xargs"}
        if name in ("pkill", "killall") and at_start:
            return (f"Blocked: `{name}` kills by name, including other agents' processes. "
                    "Kill only the PID you started: `kill <pid>`.")
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
        msg = check((data.get("tool_input") or {}).get("command") or "") if data.get("tool_name") == "Bash" else None
    except Exception as e:  # noqa: BLE001 - fail open
        print(f"kill_rules: hook error, allowed: {e}", file=sys.stderr)
        return 0
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
