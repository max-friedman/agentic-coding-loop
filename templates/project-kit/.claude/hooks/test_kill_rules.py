#!/usr/bin/env python3
"""kill_rules.py: blocks pkill -f and killall.  python3 .claude/hooks/test_kill_rules.py"""

# The validation gate runs this file when one of these paths changes (scripts/validate.py reads GATE_COVERS).
# The project's Claude Code hooks (.claude/hooks/README.md): each hook's test, on any change there.
GATE_COVERS = (".claude/hooks/", ".claude/settings.json")

import json, os, subprocess as sp, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kill_rules  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


def hook(cmd):
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "kill_rules.py")],
               input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}), capture_output=True, text=True)
    return r, time.time() - t


print("kill_rules.py")
blocked = [
    "pkill -f land.py",
    "pkill -fl 'wait_for'",
    "pkill -9 -f make",
    "pkill -9f make",
    "sudo pkill -f server",
    "sleep 1; pkill -f monitor.sh",
    "killall tccd",
    "killall -9 qemu-system-aarch64",
    "bash -c 'killall java'",
]
allowed = [
    "pgrep -fl '[l]and.py'",
    "kill 12345",
    "kill -9 12345 12346",
    "pkill make",  # an exact process name, no -f
    "pkill -x qemu-system-aarch64",
    "killall -l",
    "killall -s java",  # dry run: lists what it would kill
    "echo 'never pkill -f'",
    "grep -n 'killall' docs/process/PLAYBOOK.md",
]
for c in blocked:
    check(f"blocks: {c!r}", kill_rules.check(c) is not None)
for c in allowed:
    check(f"allows: {c!r}", kill_rules.check(c) is None, kill_rules.check(c))

r, dt = hook("pkill -f land.py")
check("pkill -f: exit 2, says find the pid and kill it", r.returncode == 2 and "kill <pid>" in r.stderr, (r.returncode, r.stderr))
r, _ = hook("killall tccd")
check("killall: exit 2", r.returncode == 2 and "killall" in r.stderr, r.stderr)
r, _ = hook("kill 12345")
check("kill <pid>: exit 0, no output", r.returncode == 0 and not r.stdout and not r.stderr, r.stderr)
r = sp.run([sys.executable, os.path.join(HERE, "kill_rules.py")], input="{", capture_output=True, text=True)
check("broken input: fails open (exit 1)", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))
t = time.time()
for _ in range(200):
    kill_rules.check(blocked[5])
per = (time.time() - t) / 200
check(f"fast: {per * 1000:.2f} ms a check (< 10 ms); {dt * 1000:.0f} ms with python startup (< 1 s)", per < 0.01 and dt < 1, dt)

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
