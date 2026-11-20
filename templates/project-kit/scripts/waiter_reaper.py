#!/usr/bin/env python3
"""
Kill orphaned Claude Code waiter shells: wait loops that outlived the session that started them.

A Claude Code Bash call runs as `zsh -c 'source ~/.claude/shell-snapshots/snapshot-...; ... eval '<command>''`. A waiter
that polls `pgrep -f <name>` in a while/until loop never ends when its pattern matches its own command line
(.claude/hooks/waiter_guard.py blocks those now) and outlives its session. In the project behind LOOP.md section F,
about 90 of them, up to 8 days old, were found holding memory with swap nearly full; the machine ran out of memory the
same day. This kills such a shell when all of these hold:
  - it is a shell (`zsh|bash|sh -c`) that sourced a Claude shell snapshot (`/.claude/shell-snapshots/snapshot-`);
  - its command is a `while`/`until` loop that sleeps (`sleep N; done`);
  - it has run over `waiter_reaper.max_age_hours` (6) hours;
  - its command names none of `waiter_reaper.protected` (your long-running queue or scheduled-suite scripts);
  - it is only waiting: no child process other than `sleep`/`pgrep` (a loop that runs real work right now is kept).
Only that shell's PID gets SIGTERM (its `sleep` child ends by itself). Each kill is one JSON line in
.loop/waiter_reaper.jsonl. Run it from the watchdog's schedule.

    python3 scripts/waiter_reaper.py            # what it would kill
    python3 scripts/waiter_reaper.py --apply    # kill them
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path



def _knobs() -> dict:
    """`waiter_reaper` in .loop/config.json (hooks/README.md)."""
    try:
        own = json.loads(Path(".loop", "config.json").read_text()).get("waiter_reaper", {})
    except (OSError, ValueError, AttributeError):
        own = {}
    return own if isinstance(own, dict) else {}


MAX_AGE_H = float(_knobs().get("max_age_hours", 6))
PROTECTED = tuple(_knobs().get("protected", ()))
SNAPSHOT = "/.claude/shell-snapshots/snapshot-"
SHELL = re.compile(r"^(?:\S*/)?(?:zsh|bash|sh)\s+(?:-\w+\s+)*-\w*c\s")
LOOP = re.compile(r"\b(?:while|until)\b[\s\S]*?\bsleep\s+[\d.]+[smh]?\s*;\s*done\b")
WAIT_CHILDREN = {"sleep", "pgrep"}
LOG = Path(".loop") / "waiter_reaper.jsonl"


def etime_s(etime: str) -> int:
    """ps's etime ([[dd-]hh:]mm:ss) in seconds."""
    days, _, rest = etime.strip().rpartition("-")
    parts = [int(x) for x in rest.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    return int(days or 0) * 86400 + parts[0] * 3600 + parts[1] * 60 + parts[2]


def processes() -> list[dict]:
    """[{pid, ppid, age_s, command}] for every process (empty when ps fails)."""
    try:
        out = subprocess.run(["ps", "-axww", "-o", "pid=,ppid=,etime=,command="], capture_output=True, text=True,
                             timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    procs = []
    for line in out.splitlines():
        f = line.split(None, 3)
        if len(f) == 4 and f[0].isdigit() and f[1].isdigit():
            try:
                procs.append({"pid": int(f[0]), "ppid": int(f[1]), "age_s": etime_s(f[2]), "command": f[3]})
            except ValueError:
                continue
    return procs


def is_waiter(cmd: str) -> bool:
    return bool(SHELL.match(cmd)) and SNAPSHOT in cmd and bool(LOOP.search(cmd))


def plan(procs: list[dict], max_age_h: float = MAX_AGE_H) -> list[dict]:
    """The waiter shells to kill, each with a `why`."""
    kids: dict[int, list[str]] = {}
    for p in procs:
        kids.setdefault(p["ppid"], []).append(os.path.basename(p["command"].split()[0]) if p["command"] else "")
    me = {os.getpid(), os.getppid()}
    out = []
    for p in procs:
        cmd = p["command"]
        if p["pid"] in me or p["age_s"] < max_age_h * 3600 or not is_waiter(cmd):
            continue
        if any(name in cmd for name in PROTECTED):
            continue
        busy = [k for k in kids.get(p["pid"], []) if k not in WAIT_CHILDREN]
        if busy:
            continue
        out.append({**p, "why": f"Claude Code waiter shell idle in a sleep loop for {p['age_s'] / 3600:.1f} h"})
    return out


def reap(now: float | None = None, procs=processes, kill=os.kill, log: Path | None = None) -> list[str]:
    """Kill the planned shells; one log line per kill. Returns a short line per kill (for the watchdog's log)."""
    now = time.time() if now is None else now
    log = log or LOG
    lines = []
    for p in plan(procs()):
        try:
            kill(p["pid"], signal.SIGTERM)
            result = "killed"
        except ProcessLookupError:
            continue
        except PermissionError as e:
            result = f"not killed: {e}"
        rec = {"at": int(now), "pid": p["pid"], "ppid": p["ppid"], "age_h": round(p["age_s"] / 3600, 1), "result": result,
               "command": p["command"][-300:]}
        try:
            log.parent.mkdir(parents=True, exist_ok=True)
            with open(log, "a") as f:
                f.write(json.dumps(rec) + "\n")
        except OSError:
            pass
        lines.append(f"pid {p['pid']} ({rec['age_h']} h, {result}): …{p['command'][-120:]}")
    return lines


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="kill them (default: list only)")
    ns = ap.parse_args(argv)
    if ns.apply:
        lines = reap()
        print("\n".join(f"waiter_reaper: {x}" for x in lines) or "waiter_reaper: nothing to kill")
        return 0
    found = plan(processes())
    for p in found:
        print(f"waiter_reaper: would kill pid {p['pid']} ({p['why']}): …{p['command'][-160:]}")
    if not found:
        print("waiter_reaper: nothing to kill")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
