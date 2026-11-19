#!/usr/bin/env python3
"""Stop (master only): the master's turn doesn't end while what wakes it is gone (robustness plan section 8, PR 1).

The master re-arming its Monitor and its check-in cron slipped 3 times, each time followed by another written rule.
Nothing wakes an idle session but a background task or a session cron, so the turn's end is the last moment to notice.
Claude Code's Stop input lists the session's `background_tasks` and `session_crons` precisely "to distinguish 'session
is done' from 'session is paused waiting for background work'" (https://code.claude.com/docs/en/hooks#stop-input).

It blocks (`{"decision": "block", "reason": …}`: Claude gets the reason as its next instruction) when:
  (a) no in-flight background task mentions `master_events` / `events_loop` (its description, command or name):
      the pipeline Monitor expired or was never armed;
  (b) no recurring session cron's prompt is a check-in (check-in / checkin / checklist / heartbeat).
  (c) TODO(robustness plan PR 3): lanes under the floor (4) while `scripts/next_lanes.py` has startable work, naming
      the rows. next_lanes.py doesn't exist yet; until it does, the lane floor is master_digest.py's line and the
      watchdog's lanes_low.
The reason quotes the exact call to make (the marker's `monitor_command` / `checkin_command`, else master_session.py's
defaults).

Only the master: the input's session_id is the one in feedback/master_session.json and there's no agent_id
(master_session.py). Helpers, the master's subagents and the feedback loop never see it.
Loops: nothing while `stop_hook_active` (Claude Code is already continuing because of a stop hook); each condition
blocks at most once per COOLDOWN_S (15 min) per session; Claude Code's own cap ends the turn after 8 continuations in a
row. An array missing from the input (the task registry unreachable, an older Claude Code) is no evidence: that
condition is skipped. Each turn end's view is saved (feedback/master_stop.json) for master_digest.py.
Its own error: fails open (exit 1, a non-blocking error; the turn ends).
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
import _shell  # noqa: E402
import master_session as ms  # noqa: E402

STATE = ms.FEEDBACK / "master_stop.json"
COOLDOWN_S = 15 * 60
MONITOR_RE = re.compile(r"master[_ ]events|events_loop", re.I)
CHECKIN_RE = re.compile(r"check-?in|checklist|heartbeat", re.I)
DONE = {"completed", "complete", "done", "failed", "killed", "stopped", "cancelled", "canceled", "error", "exited"}


def monitor_running(tasks: list) -> bool:
    for t in tasks:
        if not isinstance(t, dict) or str(t.get("status") or "").lower() in DONE:
            continue
        text = " ".join(str(t.get(k) or "") for k in ("description", "command", "name"))
        if MONITOR_RE.search(text):
            return True
    return False


def checkin_scheduled(crons: list) -> bool:
    return any(isinstance(c, dict) and c.get("recurring") and CHECKIN_RE.search(str(c.get("prompt") or ""))
               for c in crons)


def missing(data: dict) -> dict:
    """{condition: present?} for the conditions the input can answer."""
    seen = {}
    if isinstance(data.get("background_tasks"), list):
        seen["monitor"] = monitor_running(data["background_tasks"])
    if isinstance(data.get("session_crons"), list):
        seen["checkin"] = checkin_scheduled(data["session_crons"])
    # TODO(robustness plan PR 3): seen["lanes"] = lanes >= 4 or not next_lanes.startable(), once next_lanes.py exists.
    return seen


def reason(gone: list, mark: dict) -> str:
    lines = ["Master Stop hook (.claude/hooks/master_stop.py): nothing will wake this session. Before ending the turn:"]
    if "monitor" in gone:
        lines.append("- Re-arm the master_events Monitor (no background task runs master_events): "
                     + (mark.get("monitor_command") or ms.MONITOR_COMMAND)
                     + ". Keep \"master_events\" in its description.")
    if "checkin" in gone:
        lines.append("- Re-create the recurring 30-minute check-in (no recurring check-in cron in this session): "
                     + (mark.get("checkin_command") or ms.CHECKIN_COMMAND) + ".")
    lines.append("Then run the 30-minute checklist (PLAYBOOK, Watching) and end the turn.")
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


def decide(data: dict, now: float, marker_path: Optional[Path] = None, state_path: Optional[Path] = None) -> Optional[str]:
    """The block reason, or None to let the turn end."""
    if not ms.is_master(data, marker_path):
        return None
    sp = state_path or STATE
    st = load_state(sp, data["session_id"])
    seen = missing(data)
    st["last"] = dict(seen, at=int(now))
    gone = [] if data.get("stop_hook_active") else \
        [c for c, ok in seen.items() if not ok and now - float(st["blocked"].get(c) or 0) >= COOLDOWN_S]
    for c in gone:
        st["blocked"][c] = int(now)
    save_state(sp, st)
    return reason(gone, ms.marker(marker_path)) if gone else None


def main() -> None:
    try:
        why = decide(_shell.read_input(), time.time())
        if why:
            print(json.dumps({"decision": "block", "reason": why}))
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("master_stop", e)
        return
    sys.exit(0)


if __name__ == "__main__":
    main()
