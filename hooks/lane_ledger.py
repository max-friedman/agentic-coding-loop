#!/usr/bin/env python3
"""PostToolUse (Agent|Task) and SubagentStop hook: keeps the lane ledger `.loop/lanes.json` that admission_gate.py
counts against the caps.

- PostToolUse on a spawn adds an entry: {id, kind, hotspots, description, session_id, started, updated}. The kind and
  hotspots come from the prompt's `Lane: <kind>; Hotspot: <areas>` line, the same parse the gate uses (no line: the
  default kind). Read-only agent types and `Lane: none` aren't recorded. A spawn whose response says it already
  finished (a foreground subagent: its SubagentStop fired before this PostToolUse) isn't recorded either.
- SubagentStop removes the entry with that agent's id. When the spawn's response carried no id, it removes the oldest
  id-less entry of the same session instead, so the count stays right even if the names don't match.
- An entry older than `lanes.stale_hours` (default 6) counts as ended and is dropped on the next write: a lane whose
  stop never arrived (a crash, a killed session) can't hold a slot forever.

By hand:
    python3 .claude/hooks/lane_ledger.py list          # the running lanes
    python3 .claude/hooks/lane_ledger.py end <id>      # a lane you know has ended
    python3 .claude/hooks/lane_ledger.py clear         # empty the ledger

Fails open on its own errors (exit 1, a non-blocking error): a missed entry is cleaned by the TTL, and a spawn is
never blocked here (the gate is admission_gate.py).
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _loop  # noqa: E402

FINISHED = {"completed", "complete", "done", "failed", "error", "killed", "stopped", "cancelled", "canceled"}
ID_KEYS = ("agentId", "agent_id", "taskId", "task_id")
RECENT_STOPS = 50  # agent ids whose stop arrived before their PostToolUse


def find_id(v) -> str | None:
    """The agent id anywhere in a tool response (its shape differs between Claude Code versions)."""
    if isinstance(v, dict):
        for k in ID_KEYS:
            if isinstance(v.get(k), str) and v[k]:
                return v[k]
        for x in v.values():
            found = find_id(x)
            if found:
                return found
    if isinstance(v, list):
        for x in v:
            found = find_id(x)
            if found:
                return found
    return None


def finished(resp) -> bool:
    return isinstance(resp, dict) and str(resp.get("status") or "").lower() in FINISHED


def on_spawn(data: dict, cfg: dict, now: float, path=None) -> dict | None:
    """Record the spawn; -> the entry written, or None."""
    inp = data.get("tool_input") or {}
    kind, hotspots, _had = _loop.lane_of(inp, cfg)
    resp = data.get("tool_response")
    if kind is None or finished(resp):
        return None
    agent = find_id(resp)
    ttl = float(cfg["lanes"]["stale_hours"]) * 3600
    entry = {"id": agent or f"spawn-{uuid.uuid4().hex[:8]}", "agent_id": agent, "kind": kind,
             "hotspots": sorted(hotspots), "description": str(inp.get("description") or "")[:80],
             "session_id": data.get("session_id"), "started": now, "updated": now}
    with _loop.locked_ledger(path) as doc:
        doc["lanes"] = [e for e in doc["lanes"] if now - float(e.get("updated", 0)) < ttl]
        if agent and agent in doc["stopped"]:
            doc["stopped"].remove(agent)
            return None
        doc["lanes"].append(entry)
    return entry


def on_stop(data: dict, cfg: dict, now: float, path=None) -> dict | None:
    """Remove the stopped agent's lane; -> the entry removed, or None."""
    if str(data.get("agent_type") or "") in cfg["lanes"]["read_only_types"]:
        return None
    agent, sid = data.get("agent_id"), data.get("session_id")
    with _loop.locked_ledger(path) as doc:
        lanes = doc["lanes"]
        gone = next((e for e in lanes if agent and e.get("agent_id") == agent), None)
        if gone is None:
            idless = sorted((e for e in lanes if not e.get("agent_id") and e.get("session_id") == sid),
                            key=lambda e: e.get("started", 0))
            gone = idless[0] if idless else None
        if gone is not None:
            lanes.remove(gone)
        elif agent:  # its PostToolUse hasn't run yet (a foreground subagent): remember the stop
            doc["stopped"] = (doc["stopped"] + [agent])[-RECENT_STOPS:]
    return gone


def hook(data: dict, now: float | None = None, path=None):
    now = time.time() if now is None else now
    cfg = _loop.config()
    event = data.get("hook_event_name") or ""
    if event == "SubagentStop":
        return on_stop(data, cfg, now, path)
    if event == "PostToolUse" and data.get("tool_name") in ("Agent", "Task"):
        return on_spawn(data, cfg, now, path)
    return None


def cli(argv: list[str]) -> int:
    cfg = _loop.config()
    if argv[0] == "list":
        lanes = _loop.running(cfg)
        for e in lanes:
            age = int((time.time() - float(e.get("started", 0))) / 60)
            print(f"{e.get('id')}  {e.get('kind')}  hotspots={','.join(e.get('hotspots') or []) or 'none'}  "
                  f"{age} min  {e.get('description', '')}")
        print(f"{len(lanes)} running (cap {cfg['lanes']['total']})")
        return 0
    if argv[0] == "end" and len(argv) > 1:
        with _loop.locked_ledger() as doc:
            doc["lanes"] = [e for e in doc["lanes"] if e.get("id") != argv[1]]
        return 0
    if argv[0] == "clear":
        with _loop.locked_ledger() as doc:
            doc["lanes"], doc["stopped"] = [], []
        return 0
    print(__doc__, file=sys.stderr)
    return 2


def main() -> int:
    if len(sys.argv) > 1:
        return cli(sys.argv[1:])
    try:
        hook(json.load(sys.stdin))
    except Exception as e:  # noqa: BLE001 - fail open
        print(f"lane_ledger: hook error, ledger not updated: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
