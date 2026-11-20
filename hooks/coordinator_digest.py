#!/usr/bin/env python3
"""UserPromptSubmit (coordinator only): a "before you act" digest of a few lines on every coordinator turn.

A busy coordinator forgot facts that sat in files: lanes under the floor, an open watchdog flag, an expired watch,
decisions it had made for the owner and never surfaced. This puts them in front of it on every turn, including the
turns Claude Code starts by itself (a cron, a background task ending), as facts, not commands. Lines:
  lanes      running lanes in the ledger (.loop/lanes.json, lane_ledger.py) by kind, the hotspots held, and
             "UNDER THE FLOOR" below `digest.min_lanes`
  watch      the heartbeat's age (.loop/coordinator.heartbeat) and the watchdog's open flags and last run
             (.loop/watchdog_flags.json, which scripts/watchdog.py writes)
  owner      `Assumed, unreviewed: N`: the rows of the assumptions log (`digest.assumptions_log`) whose last cell starts
             with `open`. The coordinator never waits on the owner: it decides, logs the call there, and keeps going;
             the owner reviews the open rows when they have time.
Local files only (no git, gh or ps): a few ms. Only the registered coordinator (coordinator_session.py), never its
subagents or helper sessions. Its own error: fails open (exit 1, nothing added); a source it can't read is left out.
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
import _shell  # noqa: E402
import coordinator_session as cs  # noqa: E402

HEARTBEAT_STALE_S = 45 * 60
WATCHDOG_STALE_S = 45 * 60


def mins(s: float) -> str:
    s = max(0, int(s))
    return f"{s // 60} min" if s < 5400 else f"{s / 3600:.1f} h"


def read_json(p: Path):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def open_assumptions(path: Path) -> Optional[int]:
    """The assumptions log's table rows whose last cell starts with `open`; None without the file."""
    try:
        text = path.read_text()
    except OSError:
        return None
    n = 0
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[-1].lower().startswith("open"):
            n += 1
    return n


def lanes_line(cfg: dict, now: float) -> str:
    try:
        lanes = _loop.running(cfg, now)
    except (OSError, ValueError):
        return "Lanes: unknown (the ledger doesn't parse)"
    kinds: dict = {}
    for e in lanes:
        kinds[e.get("kind") or "?"] = kinds.get(e.get("kind") or "?", 0) + 1
    held = sorted({h for e in lanes for h in e.get("hotspots", [])})
    floor = int(cfg["digest"]["min_lanes"])
    line = f"Lanes: {len(lanes)} of {cfg['lanes']['total']} running"
    if kinds:
        line += " (" + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items())) + ")"
    if held:
        line += "; hotspots held: " + ", ".join(held)
    if len(lanes) < floor:
        line += f"; UNDER THE FLOOR ({floor}): start the next ready item"
    return line


def digest(cfg: dict, now: float, root: Optional[Path] = None) -> list:
    root = root or _loop.project_dir()
    lines = [lanes_line(cfg, now)]
    hb = root / ".loop" / "coordinator.heartbeat"
    try:
        age = now - hb.stat().st_mtime
        watch = f"Heartbeat: {mins(age)} old" + (" (STALE)" if age > HEARTBEAT_STALE_S else "")
    except OSError:
        watch = "Heartbeat: missing"
    w = read_json(root / ".loop" / "watchdog_flags.json")
    if isinstance(w, dict):
        flags = sorted((w.get("flags") or {}).keys())
        watch += "; watchdog flags: " + (", ".join(flags) if flags else "none")
        if w.get("checked") and now - float(w["checked"]) > WATCHDOG_STALE_S:
            watch += f"; the watchdog last ran {mins(now - float(w['checked']))} ago (STALE: check its scheduler)"
    else:
        watch += "; watchdog: no record (.loop/watchdog_flags.json)"
    lines.append(watch)
    log = cfg["digest"]["assumptions_log"]
    n = open_assumptions(root / log)
    if n is not None:
        lines.append(f"Assumed, unreviewed: {n} ({log})")
    return lines


def main() -> None:
    try:
        data = _shell.read_input()
        if cs.is_coordinator(data):
            text = ("Coordinator digest (.claude/hooks/coordinator_digest.py), facts as of " + time.strftime("%H:%M")
                    + ":\n" + "\n".join(digest(_loop.config(), time.time())))
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}))
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("coordinator_digest", e)
        return
    sys.exit(0)


if __name__ == "__main__":
    main()
