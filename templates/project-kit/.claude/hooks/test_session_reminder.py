#!/usr/bin/env python3
"""session_reminder.py: the context-loss reminder on compact/resume.  python3 .claude/hooks/test_session_reminder.py"""

# The validation gate runs this file when one of these paths changes (scripts/validate.py reads GATE_COVERS).
# The project's Claude Code hooks (.claude/hooks/README.md): each hook's test, on any change there.
GATE_COVERS = (".claude/hooks/", ".claude/settings.json")

import json, os, subprocess as sp, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import session_reminder as s  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


def hook(source):
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "session_reminder.py")],
               input=json.dumps({"hook_event_name": "SessionStart", "source": source}), capture_output=True, text=True)
    return r, time.time() - t


print("session_reminder.py")
text = s.reminder("compact", ["land.py 633 --full"])
for want in ("Master checklist", "After a context loss", "30-minute checklist", "Monitor", "check-in", "nightly", "disk", "land.py 633 --full"):
    check(f"the reminder mentions {want!r}", want in text, text)
check("no landings: says none", "Landings running now: none." in s.reminder("resume", []))
for src in ("compact", "resume"):
    r, dt = hook(src)
    check(f"{src}: exit 0, the reminder on stdout", r.returncode == 0 and "After a context loss" in r.stdout, (r.returncode, r.stdout, r.stderr))
for src in ("startup", "clear", ""):
    r, _ = hook(src)
    check(f"{src or 'no source'}: exit 0, nothing printed", r.returncode == 0 and not r.stdout, r.stdout)
r = sp.run([sys.executable, os.path.join(HERE, "session_reminder.py")], input="{", capture_output=True, text=True)
check("broken input: fails open (exit 1), never 2", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))
check(f"fast: {dt * 1000:.0f} ms with python startup and ps (< 1 s)", dt < 1, dt)

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
