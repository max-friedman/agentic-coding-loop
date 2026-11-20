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

Wiring: templates/project-kit/.claude/settings.json. The pgrep parser reads `pgrep` inside `$(...)` and skips
options that take a value (`pgrep -u <user> -f <pattern>`). templates/project-kit/scripts/waiter_reaper.py kills old
waiter shells that got through.

Exit 2 with a message on stderr blocks the call. Fails open on its own errors:
it guards a convenience, not something irreversible.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _shell  # noqa: E402

LOOP = re.compile(r"(?:^|[\s;&|(`'\"])(?:while|until)\s")
PGREP = re.compile(r"\bpgrep\b")
ARG_OPTS = set("uUgGPtFsdJ")  # pgrep options that take a value
_TOKEN = re.compile(r"""'([^']*)'|"((?:[^"\\]|\\.)*)"|([^\s;&|()"'`]+)""")


def pgrep_calls(cmd: str) -> list[tuple[bool, str]]:
    """[(has -f, pattern)] for every `pgrep` in the text (also inside "$(...)", where shell tokenizing can't see it)."""
    out = []
    for m in PGREP.finditer(cmd):
        i, has_f, pattern = m.end(), False, None
        while True:
            while i < len(cmd) and cmd[i] in " \t":
                i += 1
            t = _TOKEN.match(cmd, i)
            if not t:
                break
            word = next(g for g in t.groups() if g is not None)
            i = t.end()
            if word.startswith("--"):
                continue
            if word.startswith("-") and len(word) > 1:
                letters = word[1:]
                has_f = has_f or "f" in letters
                if letters.isalpha() and letters[-1] in ARG_OPTS:  # `-u <user>`: the value is the next word
                    while i < len(cmd) and cmd[i] in " \t":
                        i += 1
                    nxt = _TOKEN.match(cmd, i)
                    if nxt:
                        i = nxt.end()
                continue
            pattern = word
            break
        if pattern is not None:
            out.append((has_f, pattern))
    return out


def matches_itself(pattern: str, text: str) -> bool:
    try:
        return re.search(pattern, text) is not None
    except re.error:
        return pattern in text


def fixed(pattern: str) -> str:
    """The bracket-trick form of a pattern: its first letter in a one-letter class."""
    j = next((k for k, ch in enumerate(pattern) if ch.isalnum()), None)
    return pattern if j is None else f"{pattern[:j]}[{pattern[j]}]{pattern[j + 1:]}"


def check(cmd: str) -> str | None:
    if "pgrep" not in cmd or not LOOP.search(cmd):
        return None
    loop_at = LOOP.search(cmd).start()
    body = cmd[loop_at:]
    for has_f, pattern in pgrep_calls(body):
        if not has_f or not matches_itself(pattern, cmd):
            continue
        return (f"Blocked: this loop waits on `pgrep -f {pattern!r}`, which matches the loop's own shell, "
                f"so it never ends. Use `pgrep -f '{fixed(pattern)}'` (and don't spell the plain name elsewhere in the "
                "same command), or better, run the job in the background (run_in_background) and wait for its exit "
                "notification.")
    return None


def main() -> None:
    try:
        data = _shell.read_input()
        msg = check((data.get("tool_input") or {}).get("command") or "") if data.get("tool_name") == "Bash" else None
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("waiter_guard", e)
        return
    if msg:
        _shell.block(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
