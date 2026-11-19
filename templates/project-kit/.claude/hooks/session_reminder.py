#!/usr/bin/env python3
"""SessionStart (matcher compact|resume): after a context loss, put the rebuild steps back in context.

A compacted or resumed session forgets what it had armed (the PR/landing Monitor, the 30-minute check-in) and the
checklist it ran. This prints a short reminder on stdout, which Claude Code adds to the session's context: re-read
the PLAYBOOK's "After a context loss" section and the master's 30-minute checklist, re-arm the Monitor and the
check-in, check the nightly and the disk, and the landings running now (from `ps`; a few ms). It never blocks
(SessionStart can't); on its own error it fails open (exit 1, nothing added).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _shell  # noqa: E402

SOURCES = {"compact", "resume"}
LAND = re.compile(r"\bscripts/land\.py\b(.*)")


def landers() -> list[str]:
    """`land.py <args>` of each running landing (args only), or [] when ps fails."""
    try:
        r = subprocess.run(["ps", "-axww", "-o", "command="], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return []
    out = []
    for line in r.stdout.splitlines():
        m = LAND.search(line)
        if m and "python" in line:
            out.append("land.py" + m.group(1).rstrip())
    return out


def reminder(source: str, running: list[str]) -> str:
    lines = [
        f"Context was lost ({source}). Before carrying on (.claude/hooks/session_reminder.py):",
        "- The master: re-read docs/process/PLAYBOOK.md's \"Master checklist\" (top of the file) and \"After a context "
        "loss: rebuilding the master's state\", then rebuild the state it lists (open PRs and their landers, helpers, "
        "uncommitted helper worktrees) and run the 30-minute checklist (\"Watching\").",
        "- Re-arm the pipeline Monitor (PRs, landings, memory, disk) and the 30-minute check-in; neither survives.",
        "- The master: re-register its session for the master-only hooks: "
        "`python3 .claude/hooks/master_session.py register`.",
        "- Check last night's nightly ran the device suite (validate.json) and free disk (>= 12 GB before the nightly: "
        "`python3 scripts/disk_headroom.py`).",
        "- A helper: re-read your task message and CLAUDE.md, then carry on from the next step.",
    ]
    lines.append("- Landings running now: " + ("; ".join(running) if running else "none") + ".")
    lines.append("Then carry on without waiting for a prompt.")
    return "\n".join(lines)


def main() -> None:
    try:
        data = _shell.read_input()
        source = data.get("source") or ""
        if source in SOURCES:
            print(reminder(source, landers()))
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("session_reminder", e)
        return
    sys.exit(0)


if __name__ == "__main__":
    main()
