#!/usr/bin/env python3
"""watchdog.py: lanes_idle (no lane while ready work waits) and rule_drift (a rule note newer than the written rules),
and the flags file the coordinator's digest reads.  python3 hooks/test_watchdog.py"""

import json, os, subprocess as sp, sys, tempfile, time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import watchdog as wd  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


now = time.time()
cfg = dict(wd.DEFAULTS)
tmp = Path(tempfile.mkdtemp(prefix="watchdog-test-"))

print("watchdog.py: lanes_idle")
prev = {}
check("0 lanes with ready work: not yet", wd.check_lanes_idle(now, 0, 3, prev, cfg) == {} and prev.get("idle_since") == now)
f = wd.check_lanes_idle(now + 31 * 60, 0, 3, prev, cfg)
check("…after 30 min: flagged, says never wait", "lanes_idle" in f and "never wait" in f["lanes_idle"], f)
check("a lane running clears it", wd.check_lanes_idle(now + 40 * 60, 1, 3, prev, cfg) == {} and "idle_since" not in prev)
check("no ready work: never", wd.check_lanes_idle(now, 0, 0, {"idle_since": now - 9999}, cfg) == {})
check("no ready file: never", wd.check_lanes_idle(now, 0, None, {"idle_since": now - 9999}, cfg) == {})
check("an unreadable ledger: never", wd.check_lanes_idle(now, None, 3, {"idle_since": now - 9999}, cfg) == {})
road = tmp / "ROADMAP.md"
road.write_text("| row | status |\n|---|---|\n| A1 | Ready |\n| A2 | Done |\n| A3 |  Ready  |\n")
check("ready items are counted", wd.ready_items({**cfg, "ready_file": str(road)}) == 2)
led = tmp / "lanes.json"
led.write_text(json.dumps({"lanes": [{"updated": now}, {"updated": now - 7 * 3600}]}))
check("the ledger's stale entries don't count", wd.running_lanes(led, now) == 1)
check("no ledger: 0 lanes", wd.running_lanes(tmp / "none.json", now) == 0)

print("watchdog.py: rule_drift")
notes = tmp / "notes"
notes.mkdir()
(notes / "a.md").write_text("---\nname: a\ntype: feedback\n---\nAlways do X.\n")
(notes / "b.md").write_text("---\nname: b\ntype: reference\n---\nfacts\n")
c2 = {**cfg, "rule_notes_dir": str(notes)}
got = wd.rule_notes(c2)
check("only notes that record a rule", [n for n, _ in got] == ["a"], got)
check("off without a notes dir", wd.rule_notes(cfg) is None)
check("a note newer than the docs drifts", "rule_drift" in wd.check_rule_drift(now, got, now - 3600, c2))
check("docs committed after it: no drift", wd.check_rule_drift(now, got, now + 1, c2) == {})
check("an old note doesn't count", wd.check_rule_drift(now, [("a", now - 3 * 86400)], now - 4 * 86400, c2) == {})
check("git can't tell: no flag", wd.check_rule_drift(now, got, None, c2) == {})

print("watchdog.py: the run")
proj = tmp / "proj"
(proj / ".loop").mkdir(parents=True)
(proj / ".loop" / "config.json").write_text(json.dumps({"watchdog": {"min_free_disk_gb": 0, "lanes_idle_minutes": 0}}))
(proj / "docs").mkdir()
(proj / "docs" / "ROADMAP.md").write_text("| A1 | Ready |\n")
r = sp.run([sys.executable, os.path.join(HERE, "watchdog.py")], cwd=proj, capture_output=True, text=True)
doc = json.loads((proj / ".loop" / "watchdog_flags.json").read_text())
check("it writes the flags file, lanes_idle in it, and wakes", r.returncode == 0 and "lanes_idle" in doc["flags"]
      and "WAKE" in r.stdout and doc.get("checked"), (r.returncode, r.stdout, r.stderr, doc))

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
