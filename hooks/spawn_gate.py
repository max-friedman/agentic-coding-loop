#!/usr/bin/env python3
"""PreToolUse(Agent|Task|RemoteTrigger): a helper is spawned with what it needs. Every check is opt-in.

A helper starts with no memory of the coordinator's conversation, so its prompt is its whole world. In the project
behind this kit, lanes spawned without the rules list broke rules within the hour. Turn on the checks your project
wants in `.loop/config.json` under `spawn_gate` (hooks/README.md lists the knobs):

- `require_model`: an Agent spawn sets `model` (model tiering), and a RemoteTrigger `create` names one in its config.
- `require_rules`: the prompt carries the rules. `rules_markers` lists alternatives; each is a list of phrases that
  must all appear (case-insensitive). Default: it names `helper-rules.md`, or it names the playbook and `prelanding`.
- `require_no_notify`: a cloud lane (RemoteTrigger) says it won't notify the owner (it mentions "notif" and "owner").

With none on (the default), the hook allows every spawn. Exempt from the rules check: a read-only prompt ("read-only",
"blind review", "do not read any other files") and the read-only agent types (`lanes.read_only_types`). A `fork`
inherits the conversation and the parent's model, so it is never gated. RemoteTrigger `run` is checked only when it
carries text; `list`, `get`, `update` aren't gated.

Fails open on its own errors.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _loop  # noqa: E402
import _shell  # noqa: E402

READ_ONLY_PHRASES = ("read-only", "read only", "readonly", "do not read any other files", "blind review")


def strings(v) -> list[str]:
    """Every string value in a JSON value (a RemoteTrigger body's prompt can sit anywhere in its config)."""
    if isinstance(v, str):
        return [v]
    if isinstance(v, dict):
        return [s for x in v.values() for s in strings(x)]
    if isinstance(v, list):
        return [s for x in v for s in strings(x)]
    return []


def has_model(v) -> bool:
    if isinstance(v, dict):
        return any((k == "model" and isinstance(x, str) and x.strip()) or has_model(x) for k, x in v.items())
    if isinstance(v, list):
        return any(has_model(x) for x in v)
    return False


def missing_rules(text: str, markers: list) -> list[str]:
    t = text.lower()
    if any(all(p.lower() in t for p in alt) for alt in markers):
        return []
    wanted = " or ".join(" + ".join(f'"{p}"' for p in alt) for alt in markers)
    return [f"the helper rules (the prompt mentions {wanted})"]


def read_only(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in READ_ONLY_PHRASES)


def check(tool: str, inp: dict, cfg: dict | None = None) -> str | None:
    cfg = cfg or _loop.config()
    g = cfg["spawn_gate"]
    read_only_types = {t.lower() for t in cfg["lanes"]["read_only_types"]}
    missing: list[str] = []
    if tool in ("Agent", "Task"):
        kind = str(inp.get("subagent_type") or "").strip().lower()
        if kind == "fork":
            return None
        prompt = str(inp.get("prompt") or "")
        if g["require_model"] and not str(inp.get("model") or "").strip():
            missing.append("a `model` (spawn_gate.require_model)")
        if g["require_rules"] and kind not in read_only_types and not read_only(prompt):
            missing += missing_rules(prompt, g["rules_markers"])
        what = "this subagent spawn"
    elif tool == "RemoteTrigger":
        action = str(inp.get("action") or "").strip().lower()
        if action not in ("create", "run"):
            return None
        body = {k: v for k, v in inp.items() if k not in ("action", "trigger_id")}
        text = "\n".join(strings(body))
        if action == "run" and not text.strip():
            return None
        if g["require_model"] and action == "create" and not has_model(body):
            missing.append("a `model` in the trigger's config (spawn_gate.require_model)")
        if g["require_rules"] and not read_only(text):
            missing += missing_rules(text, g["rules_markers"])
        t = text.lower()
        if g["require_no_notify"] and ("notif" not in t or "owner" not in t):
            missing.append("a line saying the lane sends no notifications to the owner and reports only in its final "
                           "answer (spawn_gate.require_no_notify)")
        what = f"this cloud lane (RemoteTrigger {action})"
    else:
        return None
    if not missing:
        return None
    return (f"Blocked by .claude/hooks/spawn_gate.py: {what} is missing " + "; ".join(missing) + ". A helper starts "
            "with no memory of this conversation, so its prompt carries every rule. Add what's missing and spawn again. "
            "Read-only research or review is exempt from the rules check when its prompt says \"read-only\". The checks "
            "are set in .loop/config.json (spawn_gate).")


def main() -> None:
    try:
        data = _shell.read_input()
        msg = check(str(data.get("tool_name") or ""), data.get("tool_input") or {})
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("spawn_gate", e)
        return
    if msg:
        _shell.block(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
