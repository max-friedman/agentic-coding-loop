#!/usr/bin/env python3
"""PreToolUse(Bash): never delete a lander clone a landing still runs from (two outages from manual deletes).

Blocks `rm -r` (-rf, -fr, -R, --recursive) of /tmp/lander-<N> or /private/tmp/lander-<N> (or anything inside one)
while a `land.py … <N>` (or land.sh) is running, and of a glob such as /tmp/lander-* while any landing runs. A clone
whose landing has finished is allowed, but scripts/disk_headroom.py owns that cleanup (`--apply`: it also checks for
processes inside the clone and uncommitted changes), so prefer it. Relative paths resolve against the hook's cwd.
`ps` failing counts as "a landing may be running" (as in disk_headroom.py).

Fails open on its own errors (a command it can't parse); the rule in the PLAYBOOK still applies.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _shell  # noqa: E402

LANDER = re.compile(r"^/(?:private/)?tmp/(lander-[^/]*)")
GLOB = re.compile(r"[*?\[]")


def ps_commands() -> list[str]:
    """Every running process's command line; ["?"] when ps fails."""
    try:
        r = subprocess.run(["ps", "-axww", "-o", "command="], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return ["?"]
    return r.stdout.splitlines() if r.returncode == 0 else ["?"]


def landing_running(n: str | None, cmds: list[str]) -> bool:
    """A `land.py … <n>` (or land.sh) is running; n=None: any landing. Same pattern as disk_headroom.landing_running."""
    num = re.escape(n) if n else r"\d+"
    pat = re.compile(r"\bland\.(?:py|sh)\b(?:\s+\S+)*?\s+" + num + r"(?:\s|$)")
    return any(c == "?" or pat.search(c) for c in cmds)


def _recursive(args: list[str]) -> bool:
    return any(a == "--recursive" or (a.startswith("-") and not a.startswith("--") and ("r" in a or "R" in a)) for a in args)


def targets(cmd: str, cwd: str) -> list[str]:
    """The lander-* names (lander-12, lander-*) a recursive rm in cmd deletes."""
    out = []
    for _env, word, args in _shell.commands(cmd):
        if os.path.basename(word) != "rm" or not _recursive(args):
            continue
        for a in args:
            if a.startswith("-"):
                continue
            path = os.path.realpath(os.path.join(cwd, os.path.expanduser(os.path.expandvars(a))))
            m = LANDER.match(path) or LANDER.match(os.path.normpath(os.path.join(cwd, os.path.expanduser(a))))
            if m:
                out.append(m.group(1))
    return out


def check(cmd: str, cwd: str, cmds=None) -> str | None:
    if "rm" not in cmd or ("lander-" not in cmd and "lander-" not in cwd):
        return None
    names = targets(cmd, cwd)
    if not names:
        return None
    cmds = ps_commands() if cmds is None else cmds
    for name in names:
        n = name[len("lander-"):]
        busy = landing_running(None, cmds) if GLOB.search(n) else (n.isdigit() and landing_running(n, cmds))
        if busy:
            return (f"Blocked by .claude/hooks/lander_clones.py: a landing is still running from {name} (a `land.py` "
                    f"naming {'a lander' if GLOB.search(n) else 'PR ' + n} is live, or ps failed); deleting its clone "
                    "kills the landing mid-merge (two outages). Leave lander clones to "
                    "`python3 scripts/disk_headroom.py --apply`, which removes only finished, idle, clean ones. If "
                    "the landing is dead, check with `pgrep -fl '[l]and.py'` and `ps -ww -o pid,command -p <pid>`.")
    return None


def main() -> None:
    try:
        data = _shell.read_input()
        msg = (check((data.get("tool_input") or {}).get("command") or "", data.get("cwd") or os.getcwd())
               if data.get("tool_name") == "Bash" else None)
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("lander_clones", e)
        return
    if msg:
        _shell.block(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
