#!/usr/bin/env python3
"""An outside-the-session watchdog: raise flags from local state, wake the coordinator, page the human rarely.

Generic example for LOOP.md §F, *Watching and the human*. Run it from the OS
scheduler (cron, launchd, a systemd timer) every 15 minutes: the coordinator's
own check-ins die with its session. Every flag here is a failure that once went
unseen for hours or days in the project behind §F:

  disk_low         free disk under the floor the scheduled suite needs (it once
                   skipped its device stage at 4 GB free, and the disk hit zero
                   mid-landing the same day)
  job_auth         an unattended job keeps failing on its login (one ran "green"
                   on schedule for a week while every run failed to authenticate)
  coordinator_silent  the coordinator's heartbeat is stale while work waits
  watchdog_stale   this script's own last-run stamp is old (it was once
                   installed with a trigger that fired once and never again)

Flags in WAKE_NOW wake the coordinator at once; HUMAN_NOW reaches the human at once
with the one command only they can run. Everything else escalates to the human
only after it stays open past ESCALATE_S, at most a few times a day, never at night.
"""
from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path

STATE = Path(".loop")
EVENTS = STATE / "job_events.jsonl"     # one JSON line per unattended job run: {"at", "job", "status", "error"}
HEARTBEAT = STATE / "coordinator.heartbeat"
STAMP = STATE / "watchdog.stamp"
DISK_FLOOR_GB = 12.0
HEARTBEAT_STALE_S = 45 * 60
AUTH_LOOKBACK_S = 7 * 86400
AUTH_ERROR = re.compile(r"authenticat|oauth|\blog(?:ged)?[ -]?in\b|token expired", re.I)
WAKE_NOW = {"job_auth", "coordinator_silent"}
HUMAN_NOW = {"job_auth"}


def flags(now: float) -> dict[str, str]:
    out: dict[str, str] = {}
    free = shutil.disk_usage(Path.home()).free / 1e9
    if free < DISK_FLOOR_GB:
        out["disk_low"] = f"{free:.1f} GB free (floor {DISK_FLOOR_GB:.0f})"

    if EVENTS.exists():
        events = [json.loads(line) for line in EVENTS.read_text().splitlines() if line.strip()]
        recent = [e for e in events if now - e.get("at", 0) <= AUTH_LOOKBACK_S]
        # Only failures after the last run that got through: a later success means the login is back.
        last_ok = max((e["at"] for e in recent if e.get("status") == "ok"), default=0)
        auth = [e for e in recent if e.get("status") == "failed" and e["at"] > last_ok
                and AUTH_ERROR.search(str(e.get("error", "")))]
        if auth:
            out["job_auth"] = (f"{len(auth)} runs of {sorted({e['job'] for e in auth})} failed to log in; "
                               "only the human can fix this: run the CLI's login command, then retry the jobs")

    if HEARTBEAT.exists() and now - HEARTBEAT.stat().st_mtime > HEARTBEAT_STALE_S and out:
        out["coordinator_silent"] = f"heartbeat {int((now - HEARTBEAT.stat().st_mtime) / 60)} min old with flags open"

    if STAMP.exists() and now - STAMP.stat().st_mtime > 3 * 15 * 60:
        out["watchdog_stale"] = "the previous watchdog runs did not happen; check the scheduler"
    return out


def main() -> None:
    now = time.time()
    STATE.mkdir(exist_ok=True)
    found = flags(now)
    STAMP.touch()
    for key, detail in sorted(found.items()):
        route = "HUMAN NOW" if key in HUMAN_NOW else "WAKE" if key in WAKE_NOW else "flag"
        print(f"{route:9} {key}: {detail}")
    # Wiring left to the project: wake the coordinator (e.g. a file its watcher waits on),
    # and send HUMAN_NOW flags through one notification channel the human chose.


if __name__ == "__main__":
    main()
