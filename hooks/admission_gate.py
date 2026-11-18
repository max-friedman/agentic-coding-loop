#!/usr/bin/env python3
"""PreToolUse hook (Agent): the lane cap, one lane per hotspot, and resource floors.

Generic example for LOOP.md §F, Sizing rules 1, 2 and 5. A written limit did not
stop a busy coordinator from starting about eighteen agents against a cap of five;
a hook did. Later the same project ran the disk to zero and the machine out of
memory with the cap respected, so the gate also reads disk and swap.

Each spawn prompt carries one line the hook can classify without guessing:

    Lane: feature; Hotspot: checkout,api

The ledger is a JSON file of running lanes. This sketch only reads it: a
PostToolUse / SubagentStop hook (not shown) adds and removes entries, and stale
entries (no change for STALE_S) count as ended so a crashed lane can't hold a slot
forever.

Fails CLOSED on its own errors: over-spawning is the expensive failure. A resource
probe that can't be read does not block (the probe is not the thing guarded).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

LEDGER = Path(os.getenv("LANE_LEDGER", ".loop/lanes.json"))
CAPS = {"feature": 4, "bug": 1, "process": 1}
TOTAL_CAP = 5
STALE_S = 6 * 3600
MIN_FREE_DISK_GB = 15.0
MAX_SWAP_USED_GB = 6.0
READ_ONLY_TYPES = {"Explore", "Plan"}
LANE_LINE = re.compile(r"Lane:\s*(\w+)\s*;\s*Hotspot:\s*([\w,\- ]+)", re.I)


def running() -> list[dict]:
    if not LEDGER.exists():
        return []
    now = time.time()
    return [e for e in json.loads(LEDGER.read_text()).get("lanes", []) if now - e.get("updated", 0) < STALE_S]


def swap_used_gb() -> float | None:
    try:
        if sys.platform == "darwin":  # "total = 9216.00M  used = 7884.25M  free = ..."
            out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True, timeout=5).stdout
            m = re.search(r"used = ([\d.]+)M", out)
            return float(m.group(1)) / 1024 if m else None
        info = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
        kb = lambda k: float(info[k].split()[0])  # noqa: E731
        return (kb("SwapTotal") - kb("SwapFree")) / 1024 / 1024
    except Exception:  # noqa: BLE001 - unreadable probe: don't block on it
        return None


def check(tool_input: dict) -> str | None:
    if tool_input.get("subagent_type") in READ_ONLY_TYPES:
        return None
    m = LANE_LINE.search(tool_input.get("prompt") or "")
    if not m:
        return "Blocked: the spawn prompt needs a line `Lane: <feature|bug|process|none>; Hotspot: <areas|none>`."
    kind = m.group(1).lower()
    if kind == "none":
        return None
    hotspots = {h.strip() for h in m.group(2).split(",") if h.strip() and h.strip() != "none"}

    free_gb = shutil.disk_usage(Path.home()).free / 1e9
    if free_gb < MIN_FREE_DISK_GB:
        return (f"Blocked: {free_gb:.1f} GB free disk, floor {MIN_FREE_DISK_GB:.0f}. Remove merged worktrees "
                "and build output first; start nothing until it is back above the floor.")
    swap = swap_used_gb()
    if swap is not None and swap > MAX_SWAP_USED_GB:
        return f"Blocked: {swap:.1f} GB swap used, ceiling {MAX_SWAP_USED_GB:.0f}. Let a lane finish first."

    lanes = running()
    if len(lanes) >= TOTAL_CAP:
        return f"Blocked: {len(lanes)} lanes running, cap {TOTAL_CAP}. Wait for one to hand back."
    same = [e for e in lanes if e.get("kind") == kind]
    if len(same) >= CAPS.get(kind, 0):
        return f"Blocked: {len(same)} {kind} lanes running, cap {CAPS.get(kind, 0)}."
    held = {h for e in lanes for h in e.get("hotspots", [])} & hotspots
    if held:
        return f"Blocked: hotspot {', '.join(sorted(held))} is held by a running lane. Take the next item."
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
        msg = check(data.get("tool_input") or {}) if data.get("tool_name") in ("Agent", "Task") else None
    except Exception as e:  # noqa: BLE001 - fail closed
        msg = f"Blocked: admission gate error ({e}), blocked for safety. Fix the hook by PR."
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
