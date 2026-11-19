#!/usr/bin/env python3
"""PreToolUse(Agent|Task|RemoteTrigger): a helper is spawned with the rules (PLAYBOOK "Master checklist", Spawning).

On 2026-10-18 lanes broke rules at spawn time (a helper started without the standard rules list). A helper's prompt is
its whole world, so the gate checks the spawn itself:
- Agent (older Claude Code: Task): a `model` is set (model tiering), and the prompt carries the helper rules: it
  mentions "Master checklist" or "PLAYBOOK", and "prelanding" (`scripts/prelanding.py` before hand-back); or it tells
  the helper to read `docs/process/helper-rules.md`, which carries the full list (2026-11-08).
  Exempt from the rules check (not from the model): a read-only prompt ("read-only", "do not read any other files",
  "blind review") and the read-only agent types (Explore, Plan, claude-code-guide). A `fork` inherits the
  conversation and the parent's model, so it isn't gated.
- RemoteTrigger `create`: the same rules, a `model` somewhere in the trigger's config, and the cloud no-notify line
  (it says the lane must not notify the owner: "notif" and "owner"). `run` is checked only when it carries text (a
  plain run of an existing trigger was checked when it was created); `list`, `get`, `update` aren't gated.

Fails open on its own errors (the rules in the PLAYBOOK still apply).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _shell  # noqa: E402

READ_ONLY_TYPES = {"explore", "plan", "claude-code-guide"}
READ_ONLY_PHRASES = ("read-only", "read only", "readonly", "do not read any other files", "blind review")
WHERE = ("See docs/process/PLAYBOOK.md, \"Spawning a helper\" (#spawning-a-helper) and the Master checklist's Spawning "
         "lines; cloud lanes also \"Cloud steering\" (#cloud-steering).")


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


def missing_rules(text: str) -> list[str]:
    t = text.lower()
    if "helper-rules.md" in t:  # the file carries the whole list, including prelanding
        return []
    out = []
    if "master checklist" not in t and "playbook" not in t:
        out.append("the helper rules: point it at docs/process/PLAYBOOK.md's \"Master checklist\" (or the PLAYBOOK) "
                   "and repeat the rules list, or tell it to read docs/process/helper-rules.md")
    if "prelanding" not in t:
        out.append("`python3 scripts/prelanding.py` before handing back")
    return out


def read_only(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in READ_ONLY_PHRASES)


def check(tool: str, inp: dict) -> str | None:
    missing: list[str] = []
    if tool in ("Agent", "Task"):
        kind = str(inp.get("subagent_type") or "").strip().lower()
        if kind == "fork":
            return None
        prompt = str(inp.get("prompt") or "")
        if not str(inp.get("model") or "").strip():
            missing.append("a `model` (model tiering: Opus for features, RISKY paths and the plugin; Sonnet for docs, "
                           "tests and low-risk fixes; Haiku for summaries)")
        if kind not in READ_ONLY_TYPES and not read_only(prompt):
            missing += missing_rules(prompt)
        what = "this subagent spawn"
    elif tool == "RemoteTrigger":
        action = str(inp.get("action") or "").strip().lower()
        if action not in ("create", "run"):
            return None
        body = {k: v for k, v in inp.items() if k not in ("action", "trigger_id")}
        text = "\n".join(strings(body))
        if action == "run" and not text.strip():
            return None
        if action == "create" and not has_model(body):
            missing.append("a `model` in the trigger's config (model tiering)")
        if not read_only(text):
            missing += missing_rules(text)
        t = text.lower()
        if "notif" not in t or "owner" not in t:
            missing.append("the no-notify line: \"Do not send any notifications or push messages to the owner (no push "
                           "notification, no chat, no email); report only in your final answer, which the master "
                           "reads.\"")
        what = f"this cloud lane (RemoteTrigger {action})"
    else:
        return None
    if not missing:
        return None
    return (f"Blocked by .claude/hooks/spawn_gate.py: {what} is missing " + "; ".join(missing) + ". A helper starts "
            "with no memory of this conversation, so its prompt carries every rule (2026-10-18: lanes spawned without "
            "them broke rules). Add what's missing and spawn again. Read-only research or review is exempt from the "
            "rules list when its prompt says \"read-only\". " + WHERE)


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
