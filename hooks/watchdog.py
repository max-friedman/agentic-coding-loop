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
  lanes_idle       no lane in the ledger (.loop/lanes.json) for `watchdog.lanes_idle_minutes`
                   while ready work is listed (`watchdog.ready_file`): the coordinator once
                   sat idle about two hours waiting on an answer from the human. It never
                   waits: it picks its recommendation, logs it in the assumptions log, and
                   starts lanes
  rule_drift       a private rule note of the coordinator's (`watchdog.rule_notes_dir`, e.g.
                   its memory directory; off when unset) changed in the last day and no
                   commit to the written rules (`watchdog.rule_docs`) is newer: rules that
                   live only in one session's notes are lost with it, and no hook enforces them

Each run writes the open flags to .loop/watchdog_flags.json ({"checked", "flags": {key: {"since", "detail"}}}),
which the coordinator's per-turn digest (coordinator_digest.py) reads.

Flags in WAKE_NOW wake the coordinator at once; HUMAN_NOW reaches the human at once
with the one command only they can run. Everything else escalates to the human
only after it stays open past ESCALATE_S, at most a few times a day, never at night.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path

STATE = Path(".loop")
EVENTS = STATE / "job_events.jsonl"     # one JSON line per unattended job run: {"at", "job", "status", "error"}
HEARTBEAT = STATE / "coordinator.heartbeat"
STAMP = STATE / "watchdog.stamp"
FLAGS = STATE / "watchdog_flags.json"
LANES = STATE / "lanes.json"
DEFAULTS = {"min_free_disk_gb": 12, "lanes_idle_minutes": 30, "ready_file": "docs/ROADMAP.md",
            "ready_pattern": r"\|\s*Ready\s*\|", "rule_notes_dir": "", "rule_note_pattern": r"^\s*type:\s*feedback\b",
            "rule_docs": ["docs/process", "CLAUDE.md"], "rule_drift_hours": 24}  # as hooks/_loop.py's "watchdog"


def config() -> dict:
    """The `watchdog` knobs in .loop/config.json (hooks/README.md) over the defaults."""
    try:
        own = json.loads((STATE / "config.json").read_text()).get("watchdog", {})
    except (OSError, ValueError, AttributeError):
        own = {}
    return {**DEFAULTS, **(own if isinstance(own, dict) else {})}


CFG = config()
DISK_FLOOR_GB = float(CFG["min_free_disk_gb"])
HEARTBEAT_STALE_S = 45 * 60
AUTH_LOOKBACK_S = 7 * 86400
AUTH_ERROR = re.compile(r"authenticat|oauth|\blog(?:ged)?[ -]?in\b|token expired", re.I)
WAKE_NOW = {"job_auth", "coordinator_silent", "lanes_idle"}
HUMAN_NOW = {"job_auth"}


def running_lanes(path: Path = LANES, now: float | None = None, stale_h: float = 6) -> int | None:
    """Lanes in the ledger, minus entries older than stale_h (lanes.stale_hours); None when it can't be read."""
    now = time.time() if now is None else now
    try:
        doc = json.loads(path.read_text() or "{}") if path.exists() else {}
        return sum(1 for e in doc.get("lanes", []) if now - float(e.get("updated", 0)) < stale_h * 3600)
    except (OSError, ValueError, AttributeError, TypeError):
        return None


def ready_items(cfg: dict) -> int | None:
    """Lines of the ready file that match the ready pattern; None without the file."""
    try:
        text = Path(cfg["ready_file"]).read_text(errors="replace")
    except OSError:
        return None
    rx = re.compile(cfg["ready_pattern"])
    return sum(1 for line in text.splitlines() if rx.search(line))


def check_lanes_idle(now: float, lanes: int | None, ready: int | None, prev: dict, cfg: dict) -> dict[str, str]:
    """lanes_idle once 0 lanes with ready work has lasted lanes_idle_minutes; `prev` keeps when it started."""
    if not lanes and lanes is not None and ready:
        since = float(prev.get("idle_since") or now)
        prev["idle_since"] = since
        if now - since >= float(cfg["lanes_idle_minutes"]) * 60:
            return {"lanes_idle": f"0 lanes for {int((now - since) // 60)} min with {ready} ready items: never wait "
                                  "on the human; pick your recommendation, log it in the assumptions log, start lanes"}
        return {}
    prev.pop("idle_since", None)
    return {}


def rule_notes(cfg: dict) -> list[tuple[str, float]] | None:
    """(name, mtime) of the notes that record a rule; None when no notes dir is set or it can't be read."""
    d = cfg.get("rule_notes_dir") or ""
    if not d:
        return None
    rx = re.compile(cfg["rule_note_pattern"], re.M)
    try:
        files = list(Path(d).expanduser().glob("*.md"))
    except OSError:
        return None
    out = []
    for f in files:
        try:
            head, at = f.read_text(errors="replace")[:600], f.stat().st_mtime
        except OSError:
            continue
        if rx.search(head):
            out.append((f.stem, at))
    return out


def docs_changed_at(cfg: dict) -> float | None:
    """The newest commit time touching the written rules; None when git can't tell."""
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%ct", "HEAD", "--", *cfg["rule_docs"]],
                           capture_output=True, text=True, timeout=20)
        return float(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return None


def check_rule_drift(now: float, notes: list[tuple[str, float]] | None, docs_at: float | None, cfg: dict) -> dict[str, str]:
    if not notes or docs_at is None:
        return {}
    window = float(cfg["rule_drift_hours"]) * 3600
    drift = sorted(n for n, at in notes if now - at < window and at > docs_at)
    if not drift:
        return {}
    return {"rule_drift": f"{len(drift)} rule note{'s' if len(drift) != 1 else ''} changed with no commit to the "
                          f"written rules since ({', '.join(drift[:5])}{'…' if len(drift) > 5 else ''}): write the "
                          "rule into the process docs, by pull request, today"}


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

    prev = _read(FLAGS)
    out.update(check_lanes_idle(now, running_lanes(LANES, now), ready_items(CFG), prev, CFG))
    FLAGS_STATE.clear()
    FLAGS_STATE.update({k: v for k, v in prev.items() if k == "idle_since"})
    notes = rule_notes(CFG)
    out.update(check_rule_drift(now, notes, docs_changed_at(CFG) if notes else None, CFG))
    return out


FLAGS_STATE: dict = {}


def _read(p: Path) -> dict:
    try:
        d = json.loads(p.read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def write_flags(now: float, found: dict[str, str], path: Path = FLAGS) -> None:
    old = (_read(path).get("flags") or {})
    doc = {"checked": int(now), **FLAGS_STATE,
           "flags": {k: {"since": (old.get(k) or {}).get("since") or int(now), "detail": v} for k, v in found.items()}}
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1) + "\n")
    tmp.replace(path)


def main() -> None:
    now = time.time()
    STATE.mkdir(exist_ok=True)
    found = flags(now)
    STAMP.touch()
    write_flags(now, found)
    for key, detail in sorted(found.items()):
        route = "HUMAN NOW" if key in HUMAN_NOW else "WAKE" if key in WAKE_NOW else "flag"
        print(f"{route:9} {key}: {detail}")
    # Wiring left to the project: wake the coordinator (e.g. a file its watcher waits on),
    # and send HUMAN_NOW flags through one notification channel the human chose.


if __name__ == "__main__":
    main()
