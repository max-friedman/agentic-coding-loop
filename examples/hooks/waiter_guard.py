#!/usr/bin/env python3
"""PreToolUse hook (Bash): refuse a wait loop whose `pgrep -f` pattern matches the loop itself.

Generic example for LOOP.md §F, Sizing rule 6. Claude Code runs a Bash call as
`<shell> -c '<the command>'`, and `pgrep -f` matches whole command lines, so

    until ! pgrep -f "run_suite.py"; do sleep 10; done

finds its own shell and never ends. In the project behind §F, about 90 such
orphaned waiters, some over a week old, were found holding memory while swap was
nearly full. Allowed: the bracket form `pgrep -f '[r]un_suite.py'` (the regex
matches "run_suite.py", not the "[r]un_suite.py" written in the loop), and pgrep
outside a loop. Better still: start the awaited job in the background and take its
exit notification, with no loop at all.

Wire it in .claude/settings.json:
    {"hooks": {"PreToolUse": [{"matcher": "Bash",
        "hooks": [{"type": "command", "command": "python3 .claude/hooks/waiter_guard.py"}]}]}}

Exit 2 with a message on stderr blocks the call. Fails open on its own errors:
it guards a convenience, not something irreversible.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

LOOP = re.compile(r"(?:^|[\s;&|(`'\"])(?:while|until)\s")


def pgrep_patterns(cmd: str) -> list[str]:
    """Patterns of every `pgrep -f …` call in the command (best effort, shell-tokenized)."""
    try:
        words = shlex.split(cmd.replace("$(", " ").replace(")", " ").replace(";", " ; "))
    except ValueError:
        words = cmd.split()
    out = []
    for i, w in enumerate(words):
        if w != "pgrep":
            continue
        has_f, j = False, i + 1
        while j < len(words) and words[j].startswith("-"):
            has_f = has_f or "f" in words[j].lstrip("-")
            j += 1
        if has_f and j < len(words):
            out.append(words[j])
    return out


def matches_itself(pattern: str, text: str) -> bool:
    try:
        return re.search(pattern, text) is not None
    except re.error:
        return pattern in text


def bracketed(pattern: str) -> str:
    j = next((k for k, ch in enumerate(pattern) if ch.isalnum()), None)
    return pattern if j is None else f"{pattern[:j]}[{pattern[j]}]{pattern[j + 1:]}"


def check(cmd: str) -> str | None:
    if "pgrep" not in cmd or not LOOP.search(cmd):
        return None
    for pattern in pgrep_patterns(cmd):
        if matches_itself(pattern, cmd):
            return (f"Blocked: this loop waits on `pgrep -f {pattern!r}`, which matches the loop's own shell, "
                    f"so it never ends. Use `pgrep -f '{bracketed(pattern)}'`, or better, run the job in the "
                    "background and wait for its exit notification.")
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
        cmd = (data.get("tool_input") or {}).get("command") or ""
        msg = check(cmd) if data.get("tool_name") == "Bash" else None
    except Exception as e:  # noqa: BLE001 - fail open
        print(f"waiter_guard: hook error, allowed: {e}", file=sys.stderr)
        return 0
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
