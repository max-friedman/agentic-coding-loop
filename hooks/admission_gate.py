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

Build-slot budget (opt-in, `lanes.max_build_helpers` above 0): a spawn whose prompt has `Needs: local` without `no build`
uses the machine's one build slot; one more is refused while that many running lanes do.

An owner-approved, expiring raise of one kind's cap (`lanes.override_file`, default `.loop/lane_override.json`:
`{"kind": "bug", "max": 3, "until": <epoch>, "why": "..."}`) lifts that kind's cap to `max` (at most
`lanes.override_ceiling`) until it expires; a missing, unreadable or expired file means the normal cap, and the total
cap still holds. Only the owner writes it.

Fails CLOSED on its own errors, a config file that doesn't parse included: over-spawning is the expensive failure.
A resource probe that can't be read does not block (the probe is not the thing guarded).

Finish before starting (opt-in, `finish_before_start.max_waiting_prs` above 0): a feature spawn is refused while more
open, non-draft pull requests than that wait to land (`gh pr list`; LOOP_GH_BIN overrides gh). Bug and process lanes
pass: they are what unblocks landing. A PR list that can't be read does not block.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
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
    if msg := build_refusal(tool_input, lanes, cfg):
        return msg
    total = int(cfg["lanes"]["total"])
    if len(lanes) >= total:
        return (f"Blocked: {len(lanes)} lanes running, cap {total}. Wait for one to hand back "
                "(`python3 .claude/hooks/lane_ledger.py list` shows them).")
    cap = int(cfg["lanes"]["caps"].get(kind, 0))
    raised = _loop.cap_override(kind, cfg, now)
    if raised:
        cap = raised[0]
    same = [e for e in lanes if e.get("kind") == kind]
    if len(same) >= cap:
        return (f"Blocked: {len(same)} {kind} lanes running, cap {cap}"
                + (f" (raised by the owner's override: {raised[1]})" if raised else " (lanes.caps in .loop/config.json)") + ".")
    held = {h for e in lanes for h in e.get("hotspots", [])} & hotspots
    if held:
        return f"Blocked: hotspot {', '.join(sorted(held))} is held by a running lane. Take the next item."
    return queue_refusal(kind, cfg)


def build_refusal(tool_input: dict, lanes: list[dict], cfg: dict) -> str | None:
    """The build-slot budget (opt-in, `lanes.max_build_helpers` above 0): a spawn that declares `Needs: local` without
    `no build` is refused while that many running lanes already use the build slot (the ledger's `build` flag). More
    only queue on the one slot, and each waits a whole build behind the others."""
    cap = int(cfg["lanes"].get("max_build_helpers") or 0)
    if cap <= 0 or not _loop.uses_build(str(tool_input.get("prompt") or "")):
        return None
    users = [e for e in lanes if e.get("build")]
    if len(users) < cap:
        return None
    names = ", ".join(str(e.get("description") or e.get("id")) for e in users[:6])
    return (f"Blocked: build-slot budget. {len(users)} running lanes use the build slot ({names}), the budget is {cap} "
            "(lanes.max_build_helpers). More only queue on the one slot. Send work that needs no build to a cloud lane, "
            "say `Needs: local (..., no build)` if this helper won't build, batch ready PRs into one landing, or wait "
            "for a lane to end.")


def open_ready_prs() -> list[int] | None:
    """Open, non-draft pull requests of this repo, or None when gh can't tell."""
    try:
        r = subprocess.run([os.environ.get("LOOP_GH_BIN") or "gh", "pr", "list", "--state", "open", "--limit", "200",
                            "--json", "number,isDraft"], capture_output=True, text=True, timeout=8,
                           cwd=str(_loop.project_dir()))
        if r.returncode:
            return None
        return [p["number"] for p in json.loads(r.stdout or "[]") if not p.get("isDraft")]
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return None


def queue_refusal(kind: str, cfg: dict) -> str | None:
    """Finish before starting: a feature spawn while more than max_waiting_prs ready PRs wait to land."""
    limit = int((cfg.get("finish_before_start") or {}).get("max_waiting_prs") or 0)
    if limit <= 0 or kind != "feature":
        return None
    prs = open_ready_prs()
    if prs is None or len(prs) <= limit:
        return None
    return (f"Blocked: finish before starting. {len(prs)} pull requests wait to land "
            f"({', '.join(f'#{n}' for n in prs[:8])}{'…' if len(prs) > 8 else ''}), more than {limit} "
            "(finish_before_start.max_waiting_prs). Point lanes at what unblocks landing (failed checks, flaky tests, "
            "conflicts, build speed) as `Lane: bug` or `Lane: process` instead.")


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
