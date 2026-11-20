#!/usr/bin/env python3
"""coordinator_digest.py: the coordinator's per-turn digest (lanes, watch, open assumptions); silent for anyone else.
    python3 hooks/test_coordinator_digest.py (or .claude/hooks/ once installed)"""

import json, os, subprocess as sp, sys, tempfile, time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PROJ = Path(tempfile.mkdtemp(prefix="digest-test-"))
os.environ["CLAUDE_PROJECT_DIR"] = str(PROJ)
os.environ.pop("LOOP_CONFIG", None)
os.environ.pop("LANE_LEDGER", None)
import _loop  # noqa: E402
import coordinator_digest as cd  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


L = PROJ / ".loop"
L.mkdir()
(L / "coordinator_session.json").write_text(json.dumps({"session_id": "COORD", "at": 0}))
now = time.time()
cfg = _loop.config()

print("coordinator_digest.py")
lines = cd.digest(cfg, now)
check("no ledger: 0 lanes, under the floor", "Lanes: 0 of 5" in lines[0] and "UNDER THE FLOOR" in lines[0], lines)
check("no heartbeat, no watchdog record: says so", "Heartbeat: missing" in lines[1] and "no record" in lines[1], lines)
check("no assumptions log: no owner line", not any("Assumed" in x for x in lines), lines)

(L / "lanes.json").write_text(json.dumps({"lanes": [
    {"kind": "feature", "hotspots": ["api"], "updated": now}, {"kind": "bug", "hotspots": [], "updated": now},
    {"kind": "feature", "hotspots": ["ui"], "updated": now - 7 * 3600}]}))
(L / "coordinator.heartbeat").touch()
os.utime(L / "coordinator.heartbeat", (now - 3600, now - 3600))
(L / "watchdog_flags.json").write_text(json.dumps({"checked": now - 3600, "flags": {"lanes_idle": "x", "disk_low": "y"}}))
log = PROJ / "docs" / "process" / "assumptions-log.md"
log.parent.mkdir(parents=True)
log.write_text("| Date | Decision | Why | How to revisit | Status |\n|---|---|---|---|---|\n"
               "| 2026-01-02 | a | b | c | open |\n| 2026-01-01 | d | e | f | confirmed 2026-01-03 |\n"
               "| 2026-01-01 | g | h | i | open (asked) |\n")
lines = cd.digest(cfg, now)
check("lanes by kind, stale entries dropped, hotspots held", "Lanes: 2 of 5 running (bug 1, feature 1)" in lines[0]
      and "hotspots held: api" in lines[0] and "UNDER" not in lines[0], lines[0])
check("a stale heartbeat and watchdog say so", "(STALE)" in lines[1] and "lanes_idle" in lines[1] and "last ran 60 min" in lines[1], lines[1])
check("open assumptions are counted", any(x.startswith("Assumed, unreviewed: 2 ") for x in lines), lines)


def hook(**data):
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "coordinator_digest.py")], capture_output=True, text=True,
               env={**os.environ, "CLAUDE_PROJECT_DIR": str(PROJ)}, input=json.dumps({"hook_event_name": "UserPromptSubmit", **data}))
    return r, time.time() - t


r, dt = hook(session_id="COORD")
out = json.loads(r.stdout or "{}")
ctx = out.get("hookSpecificOutput", {}).get("additionalContext", "")
check("the coordinator gets it as additionalContext", r.returncode == 0 and "Coordinator digest" in ctx and "Lanes:" in ctx, (r.stdout, r.stderr))
check(f"fast: {dt * 1000:.0f} ms with python startup (< 1 s)", dt < 1, dt)
r, _ = hook(session_id="COORD", agent_id="a1")
check("a coordinator's subagent gets nothing", r.returncode == 0 and not r.stdout, r.stdout)
r, _ = hook(session_id="OTHER")
check("another session gets nothing", r.returncode == 0 and not r.stdout, r.stdout)
r = sp.run([sys.executable, os.path.join(HERE, "coordinator_digest.py")], input="{", capture_output=True, text=True)
check("broken input: fails open (exit 1)", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
