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
  lanes_idle       no lane in the ledger (.loop/lanes.json) for `watchdog.lanes_idle_minutes`,
                   ready work listed (`watchdog.ready_file`) or not: the coordinator once sat
                   idle about two hours waiting on an answer from the human, and later twice
                   more while the ready list had no ready row only because its statuses were
                   stale, so a flag that needed ready rows never fired. It never waits: it
                   picks its recommendation, logs it in the assumptions log, and starts lanes.
                   With no ready row the detail says to fix the list's statuses first. It
                   starts "COORDINATOR STALLED" when the coordinator's last turn
                   (.loop/coordinator_stop.json, the Stop hook's record) also ended that long
                   ago: a heartbeat its wait script touches looks fresh while nothing happens
  release_paused   the release pipeline's pause is on (`release.paused_file`, written by the
                   project's pipeline): no new build reaches users. The detail names the cause
                   and `release.resume_command`. Coordinator only, until
  release_stuck    the pause has lasted `release.stuck_hours` (24): it reaches the human at
                   once and wakes the coordinator (a pipeline once sat paused ten days unseen,
                   while a cutover switched features on for users who still ran the old build)
  build_stale      the build users run (`release.published_file`) lacks a shipped change
                   (`release.shipped_paths`, not tests) that reached `release.good_ref` over
                   `release.stale_days` (2) ago
  rule_drift       a private rule note of the coordinator's (`watchdog.rule_notes_dir`, e.g.
                   its memory directory; off when unset) changed in the last day and no
                   commit to the written rules (`watchdog.rule_docs`) is newer: rules that
                   live only in one session's notes are lost with it, and no hook enforces them

Each run writes the open flags to .loop/watchdog_flags.json ({"checked", "flags": {key: {"since", "detail"}}}),
which the coordinator's per-turn digest (coordinator_digest.py) reads.

Flags in WAKE_NOW wake the coordinator at once; HUMAN_NOW reaches the human at once
with the one command only they can run. COORDINATOR_ONLY flags never reach the human.
Everything else escalates to the human only after it stays open past ESCALATE_S, at
most a few times a day, never at night.
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
COORD_STOP = STATE / "coordinator_stop.json"  # coordinator_stop.py: {"last": {"at": the coordinator's last turn end}}
DEFAULTS = {"min_free_disk_gb": 12, "lanes_idle_minutes": 30, "ready_file": "docs/ROADMAP.md",
            "ready_pattern": r"\|\s*Ready\s*\|", "rule_notes_dir": "", "rule_note_pattern": r"^\s*type:\s*feedback\b",
            "rule_docs": ["docs/process", "CLAUDE.md"], "rule_drift_hours": 24}  # as hooks/_loop.py's "watchdog"
RELEASE_DEFAULTS = {"paused_file": "", "published_file": "", "good_ref": "origin/main", "shipped_paths": [],
                    "not_shipped_pattern": r"(^|/)tests?/|(^|/)test_[^/]*$", "resume_command": "",
                    "stuck_hours": 24, "stale_days": 2}  # as hooks/_loop.py's "release"


def config(section: str = "watchdog", defaults: dict = DEFAULTS) -> dict:
    """A section of .loop/config.json (hooks/README.md) over its defaults."""
    try:
        own = json.loads((STATE / "config.json").read_text()).get(section, {})
    except (OSError, ValueError, AttributeError):
        own = {}
    return {**defaults, **(own if isinstance(own, dict) else {})}


CFG = config()
RCFG = config("release", RELEASE_DEFAULTS)
DISK_FLOOR_GB = float(CFG["min_free_disk_gb"])
HEARTBEAT_STALE_S = 45 * 60
AUTH_LOOKBACK_S = 7 * 86400
AUTH_ERROR = re.compile(r"authenticat|oauth|\blog(?:ged)?[ -]?in\b|token expired", re.I)
WAKE_NOW = {"job_auth", "coordinator_silent", "lanes_idle", "release_stuck"}
HUMAN_NOW = {"job_auth", "release_stuck"}
COORDINATOR_ONLY = {"release_paused"}  # the coordinator's to fix; never escalated to the human


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


def last_turn(path: Path = COORD_STOP) -> float | None:
    """When the coordinator's last turn ended (coordinator_stop.py's record); None when unknown."""
    try:
        return float((_read(path).get("last") or {}).get("at")) or None
    except (TypeError, ValueError):
        return None


def check_lanes_idle(now: float, lanes: int | None, ready: int | None, prev: dict, cfg: dict,
                     turn: float | None = None) -> dict[str, str]:
    """lanes_idle once 0 lanes has lasted lanes_idle_minutes, ready work or not; `prev` keeps when it started.
    "COORDINATOR STALLED" when the coordinator's last turn (`turn`) ended that long ago too."""
    if lanes or lanes is None:
        prev.pop("idle_since", None)
        return {}
    since = float(prev.get("idle_since") or now)
    prev["idle_since"] = since
    window = float(cfg["lanes_idle_minutes"]) * 60
    if now - since < window:
        return {}
    head = "COORDINATOR STALLED: " if turn is not None and now - turn >= window else ""
    when = "" if turn is None else f"; the coordinator's last turn ended {int((now - turn) // 60)} min ago"
    rule = "never wait on the human; pick your recommendation, log it in the assumptions log, start lanes"
    idle = f"{head}0 lanes for {int((now - since) // 60)} min"
    if ready:
        return {"lanes_idle": f"{idle} with {ready} ready items{when}: {rule}"}
    if ready is None:
        return {"lanes_idle": f"{idle} (no ready list at {cfg['ready_file']}){when}: {rule}"}
    return {"lanes_idle": f"{idle} and no ready item in {cfg['ready_file']}{when}: its statuses are stale or every "
                          f"item waits on the human; update the statuses, then {rule}"}


# ------------------------------------------------------------------ the release pipeline


def _git(*a: str) -> str | None:
    try:
        r = subprocess.run(["git", *a], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def shipped_commits_behind(published: str, good: str, rcfg: dict) -> list[tuple[str, int]] | None:
    """First-parent commits after the published build's commit (its merge base with `good`) up to `good` that
    changed a shipped path, oldest first, as (sha, commit time). None when git can't say."""
    base = (_git("merge-base", published, good) or "").strip()
    if not base:
        return None
    paths = list(rcfg.get("shipped_paths") or [])
    out = _git("log", "--first-parent", "-m", "--reverse", "--name-only", "--format=@%H %ct", f"{base}..{good}",
               *(["--", *paths] if paths else []))
    if out is None:
        return None
    skip = re.compile(rcfg.get("not_shipped_pattern") or r"$^")
    got: list[tuple[str, int]] = []
    sha, ct, ships = "", 0, False
    for line in out.splitlines() + ["@"]:
        if line.startswith("@"):
            if sha and ships and (not got or got[-1][0] != sha):
                got.append((sha, ct))
            parts = line[1:].split()
            sha, ct, ships = (parts[0], int(parts[1]), False) if len(parts) == 2 else ("", 0, False)
        elif line.strip() and not skip.search(line.strip()):
            ships = True
    return got


def release_info(rcfg: dict) -> dict | None:
    """{paused, published, behind} from the pipeline's files; None when the release knobs are unset."""
    if not rcfg.get("paused_file") and not rcfg.get("published_file"):
        return None
    paused = _read(Path(rcfg["paused_file"])) if rcfg.get("paused_file") else {}
    published = _read(Path(rcfg["published_file"])) if rcfg.get("published_file") else {}
    behind = None
    if published.get("commit"):
        good = (_git("rev-parse", "--verify", "-q", rcfg["good_ref"]) or "").strip()
        behind = shipped_commits_behind(str(published["commit"]), good, rcfg) if good else None
    return {"paused": paused or None, "published": published, "behind": behind}


def check_release(now: float, info: dict | None, rcfg: dict) -> dict[str, str]:
    """release_paused (release_stuck after stuck_hours), build_stale."""
    if not info:
        return {}
    out: dict[str, str] = {}
    resume = rcfg.get("resume_command") or "the pipeline's resume command"
    paused = info.get("paused")
    if paused:
        try:
            at = float(paused.get("at") or now)
        except (TypeError, ValueError):
            at = now
        detail = (f"the release pipeline is paused since {time.strftime('%m-%d %H:%M', time.localtime(at))} "
                  f"({paused.get('why') or 'no cause recorded'}): no new build reaches users. Once the fix has "
                  f"landed and passed its checks: {resume}")
        out["release_paused"] = detail
        if now - at >= float(rcfg["stuck_hours"]) * 3600:
            out["release_stuck"] = f"paused {int((now - at) // 3600)} h: " + detail
    behind = info.get("behind")
    if behind and now - behind[0][1] >= float(rcfg["stale_days"]) * 86400:
        pub = info.get("published") or {}
        n = len(behind)
        out["build_stale"] = (f"the build users run ({pub.get('version') or str(pub.get('commit'))[:9]}) lacks {n} "
                              f"shipped change{'s' if n != 1 else ''} on {rcfg['good_ref']}, the oldest merged "
                              f"{int((now - behind[0][1]) // 86400)} d ago ({behind[0][0][:9]}): users run old code, so "
                              "a cutover changes nothing for them" + (f"; the pipeline is paused: {resume}" if paused else ""))
    return out


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
    out.update(check_lanes_idle(now, running_lanes(LANES, now), ready_items(CFG), prev, CFG, last_turn()))
    FLAGS_STATE.clear()
    FLAGS_STATE.update({k: v for k, v in prev.items() if k == "idle_since"})
    notes = rule_notes(CFG)
    out.update(check_rule_drift(now, notes, docs_changed_at(CFG) if notes else None, CFG))
    out.update(check_release(now, release_info(RCFG), RCFG))
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
        route = ("HUMAN NOW" if key in HUMAN_NOW else "WAKE" if key in WAKE_NOW
                 else "coord" if key in COORDINATOR_ONLY else "flag")
        print(f"{route:9} {key}: {detail}")
    # Wiring left to the project: wake the coordinator (e.g. a file its watcher waits on),
    # and send HUMAN_NOW flags through one notification channel the human chose.


if __name__ == "__main__":
    main()
