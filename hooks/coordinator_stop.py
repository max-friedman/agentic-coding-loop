#!/usr/bin/env python3
"""Stop (coordinator only): the coordinator's turn doesn't end while what wakes it is gone.

Nothing wakes an idle session but a background task or a session cron, so the end of a turn is the last moment to
notice that the quiet watch (the background task that wakes it) ended or the check-in was never re-created. In the project behind this kit, re-arming
them slipped three times, each followed by another written rule; this hook replaced the rules. Claude Code's Stop input
lists the session's `background_tasks` and `session_crons` to tell "done" from "paused waiting for background work"
(https://code.claude.com/docs/en/hooks#stop-input).

Opt-in: does nothing unless `coordinator.require_checks` is true in `.loop/config.json` (it assumes you run a
coordinator session with a quiet watch and a recurring check-in).

It blocks (`{"decision": "block", "reason": …}`: Claude gets the reason as its next instruction) when:
  (a) no in-flight background task matches `coordinator.monitor_pattern` (its description, command or name);
  (b) no recurring session cron's prompt matches `coordinator.checkin_pattern`.
The reason quotes the call to make: `coordinator.monitor_command` / `coordinator.checkin_command` in
.loop/config.json (hooks/README.md lists the knobs).

Only the coordinator: the input's session_id is the one coordinator_session.py registered and there's no agent_id.
Loops: nothing while `stop_hook_active`; each condition blocks at most once per `coordinator.cooldown_minutes` per
session; Claude Code's own cap ends the turn after a run of continuations. An array missing from the input (an older
Claude Code) is no evidence: that condition is skipped. Each turn end's view is saved in .loop/coordinator_stop.json.
Fails open on its own errors (exit 1, a non-blocking error; the turn ends).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _loop  # noqa: E402
import _shell  # noqa: E402
import coordinator_session as cs  # noqa: E402

DONE = {"completed", "complete", "done", "failed", "killed", "stopped", "cancelled", "canceled", "error", "exited"}


def state_path() -> Path:
    return _loop.project_dir() / ".loop" / "coordinator_stop.json"


def monitor_running(tasks: list, pattern: str) -> bool:
    rx = re.compile(pattern, re.I)
    for t in tasks:
        if not isinstance(t, dict) or str(t.get("status") or "").lower() in DONE:
            continue
        if rx.search(" ".join(str(t.get(k) or "") for k in ("description", "command", "name"))):
            return True
    return False


def checkin_scheduled(crons: list, pattern: str) -> bool:
    rx = re.compile(pattern, re.I)
    return any(isinstance(c, dict) and c.get("recurring") and rx.search(str(c.get("prompt") or "")) for c in crons)


def present(data: dict, cfg: dict) -> dict:
    """{condition: present?} for the conditions the input can answer."""
    c = cfg["coordinator"]
    seen = {}
    if isinstance(data.get("background_tasks"), list):
        seen["monitor"] = monitor_running(data["background_tasks"], c["monitor_pattern"])
    if isinstance(data.get("session_crons"), list):
        seen["checkin"] = checkin_scheduled(data["session_crons"], c["checkin_pattern"])
    return seen


def reason(gone: list, cfg: dict) -> str:
    c = cfg["coordinator"]
    lines = ["Coordinator Stop hook (.claude/hooks/coordinator_stop.py): nothing will wake this session. Before ending "
             "the turn:"]
    if "monitor" in gone:
        lines.append(f"- Restart the quiet watch (no running background task matches /{c['monitor_pattern']}/): "
                     f"{c['monitor_command']}.")
    if "checkin" in gone:
        lines.append(f"- Re-create the recurring check-in (no recurring cron's prompt matches /{c['checkin_pattern']}/): "
                     f"{c['checkin_command']}.")
    lines.append("Then run the check-in checklist (docs/process/PLAYBOOK.md) and end the turn.")
    return "\n".join(lines)


def load_state(path: Path, sid: str) -> dict:
    try:
        d = json.loads(path.read_text())
    except (OSError, ValueError):
        d = {}
    if not isinstance(d, dict) or d.get("session_id") != sid:
        d = {"session_id": sid}
    d.setdefault("blocked", {})
    return d


def save_state(path: Path, d: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(d) + "\n")
        os.replace(tmp, path)
    except OSError:
        pass


def decide(data: dict, now: float, marker_path: Optional[Path] = None, state: Optional[Path] = None,
           cfg: Optional[dict] = None) -> Optional[str]:
    """The block reason, or None to let the turn end."""
    if not cs.is_coordinator(data, marker_path):
        return None
    cfg = cfg or _loop.config()
    sp = state or state_path()
    st = load_state(sp, data["session_id"])
    seen = present(data, cfg)
    st["last"] = dict(seen, at=int(now))  # always, opt-in or not: the watchdog reads it to tell a stalled coordinator
    if not cfg["coordinator"].get("require_checks"):
        save_state(sp, st)
        return None
    cooldown = float(cfg["coordinator"]["cooldown_minutes"]) * 60
    gone = [] if data.get("stop_hook_active") else \
        [c for c, ok in seen.items() if not ok and now - float(st["blocked"].get(c) or 0) >= cooldown]
    for c in gone:
        st["blocked"][c] = int(now)
    save_state(sp, st)
    return reason(gone, cfg) if gone else None


def main() -> None:
    try:
        why = decide(_shell.read_input(), time.time())
        if why:
            print(json.dumps({"decision": "block", "reason": why}))
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("coordinator_stop", e)
        return
    sys.exit(0)


if __name__ == "__main__":
    main()
