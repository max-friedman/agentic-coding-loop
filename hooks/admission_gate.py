#!/usr/bin/env python3
"""PreToolUse hook (Agent|Task): the lane cap, one lane per hotspot, and resource floors.

LOOP.md §F, Sizing rules 1, 2 and 5. A written limit did not stop a busy coordinator from starting about eighteen
agents against a cap of five; a hook did. Later the same project ran the disk to zero and the machine out of memory
with the cap respected, so the gate also reads disk and swap.

A spawn prompt says what kind of lane it starts and what it touches, in one line:

    Lane: feature; Hotspot: checkout,api

A prompt without the line counts as `lanes.default_kind` with no hotspot, and the call goes through with a warning
(set `lanes.require_lane_line` to block instead). `Lane: none` and the read-only agent types are never counted.

The running lanes come from the ledger, `.loop/lanes.json`, which `lane_ledger.py` writes: PostToolUse adds a lane
when a spawn starts, SubagentStop removes it, and an entry older than `lanes.stale_hours` counts as ended, so a crashed
lane can't hold a slot forever. The caps, the floors and the default kind are knobs in `.loop/config.json`
(hooks/README.md lists them).

Fails CLOSED on its own errors, a config file that doesn't parse included: over-spawning is the expensive failure.
A resource probe that can't be read does not block (the probe is not the thing guarded).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _loop  # noqa: E402


def check(tool_input: dict, cfg: dict | None = None, now: float | None = None) -> str | None:
    """Why this spawn is blocked, or None."""
    cfg = cfg or _loop.config()
    kind, hotspots, had_line = _loop.lane_of(tool_input, cfg)
    if kind is None:
        return None
    if not had_line and cfg["lanes"]["require_lane_line"]:
        return ("Blocked: the spawn prompt needs a line `Lane: <kind>; Hotspot: <areas|none>` "
                "(lanes.require_lane_line is on in .loop/config.json).")

    min_disk, max_swap = _loop.floors(cfg)
    free_gb = shutil.disk_usage(Path.home()).free / 1e9
    if free_gb < min_disk:
        return (f"Blocked: {free_gb:.1f} GB free disk, floor {min_disk:g}. Remove merged worktrees "
                "and build output first; start nothing until it is back above the floor.")
    swap = _loop.swap_used_gb()
    if swap is not None and swap > max_swap:
        return f"Blocked: {swap:.1f} GB swap used, ceiling {max_swap:g}. Let a lane finish first."

    lanes = _loop.running(cfg, now)
    total = int(cfg["lanes"]["total"])
    if len(lanes) >= total:
        return (f"Blocked: {len(lanes)} lanes running, cap {total}. Wait for one to hand back "
                "(`python3 .claude/hooks/lane_ledger.py list` shows them).")
    cap = int(cfg["lanes"]["caps"].get(kind, 0))
    same = [e for e in lanes if e.get("kind") == kind]
    if len(same) >= cap:
        return f"Blocked: {len(same)} {kind} lanes running, cap {cap} (lanes.caps in .loop/config.json)."
    held = {h for e in lanes for h in e.get("hotspots", [])} & hotspots
    if held:
        return f"Blocked: hotspot {', '.join(sorted(held))} is held by a running lane. Take the next item."
    return None


def warn(tool_input: dict, cfg: dict | None = None) -> str | None:
    """A note for a spawn that goes through on a default: no Lane: line."""
    cfg = cfg or _loop.config()
    kind, _hot, had_line = _loop.lane_of(tool_input, cfg)
    if kind is None or had_line:
        return None
    return (f"admission_gate: no `Lane: <kind>; Hotspot: <areas>` line in the spawn prompt, so it counts as a "
            f"{kind} lane with no hotspot. Add the line so the cap and the hotspot check see what it touches.")


def main() -> int:
    try:
        data = json.load(sys.stdin)
        msg = note = None
        if data.get("tool_name") in ("Agent", "Task"):
            cfg = _loop.config()
            inp = data.get("tool_input") or {}
            msg = check(inp, cfg)
            note = None if msg else warn(inp, cfg)
    except Exception as e:  # noqa: BLE001 - fail closed
        msg = f"Blocked: admission gate error ({type(e).__name__}: {e}), blocked for safety. Fix the hook or the config."
    if msg:
        print(msg, file=sys.stderr)
        return 2
    if note:
        print(json.dumps({"systemMessage": note}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
