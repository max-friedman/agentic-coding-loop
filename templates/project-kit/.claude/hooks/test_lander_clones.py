#!/usr/bin/env python3
"""lander_clones.py: blocks rm -rf of a lander clone a landing still runs from.  python3 .claude/hooks/test_lander_clones.py"""

# The validation gate runs this file when one of these paths changes (scripts/validate.py reads GATE_COVERS).
# The project's Claude Code hooks (.claude/hooks/README.md): each hook's test, on any change there.
GATE_COVERS = (".claude/hooks/", ".claude/settings.json")

import json, os, subprocess as sp, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lander_clones  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


def hook(cmd, cwd="/"):
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "lander_clones.py")],
               input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd}), capture_output=True, text=True)
    return r, time.time() - t


print("lander_clones.py")
ps = ["/usr/bin/python3 /private/tmp/lander-633/scripts/land.py 633 --full", "bash scripts/land.sh 640 641",
      "/usr/bin/python3 scripts/pr_staleness.py 700"]
blocked = [
    ("rm -rf /tmp/lander-633", "/"),
    ("rm -rf /private/tmp/lander-633", "/"),
    ("rm -fr /tmp/lander-633/", "/"),
    ("rm -r -f /private/tmp/lander-641", "/"),
    ("rm -rf /tmp/lander-633/app/build", "/"),
    ("rm -rf lander-640", "/private/tmp"),
    ("rm -rf /tmp/lander-*", "/"),
    ("rm -rf /private/tmp/lander-6*", "/"),
    ("cd ~ && rm -rf /tmp/lander-633 /tmp/lander-1", "/"),
    ("sudo rm --recursive --force /tmp/lander-640", "/"),
    ("rm -rf build", "/private/tmp/lander-633"),  # inside the clone: breaks the landing too
]
allowed = [
    ("rm -rf /tmp/lander-700", "/"),          # pr_staleness.py 700 isn't a landing
    ("rm -rf /private/tmp/lander-1", "/"),    # no landing for 1
    ("rm /tmp/lander-633.log", "/"),          # not recursive
    ("rm -rf /tmp/other-633", "/"),
    ("ls /tmp/lander-633", "/"),
    ("echo 'rm -rf /tmp/lander-633'", "/"),
    ("python3 scripts/disk_headroom.py --apply", "/"),
]
for c, cwd in blocked:
    check(f"blocks: {c!r} (cwd {cwd})", lander_clones.check(c, cwd, ps) is not None)
for c, cwd in allowed:
    check(f"allows: {c!r} (cwd {cwd})", lander_clones.check(c, cwd, ps) is None, lander_clones.check(c, cwd, ps))
check("no landing running: a glob is allowed", lander_clones.check("rm -rf /tmp/lander-*", "/", ps[2:]) is None)
check("ps failed: assume a landing runs (as disk_headroom.py does)", lander_clones.check("rm -rf /tmp/lander-1", "/", ["?"]) is not None)

# End to end with a real process whose command line names land.py <N> (the hook runs its own ps).
n = "4242%d" % (os.getpid() % 1000)
dummy = sp.Popen([sys.executable, "-c", "import time; time.sleep(30)", "scripts/land.py", n])
try:
    time.sleep(0.2)
    r, dt = hook(f"rm -rf /tmp/lander-{n}")
    check("a live land.py <N>: exit 2, names disk_headroom.py", r.returncode == 2 and "disk_headroom.py --apply" in r.stderr,
          (r.returncode, r.stderr))
finally:
    dummy.kill()
    dummy.wait()
r, _ = hook(f"rm -rf /tmp/lander-{n}")
check("the same rm once that landing is gone: exit 0, no output", r.returncode == 0 and not r.stdout and not r.stderr, r.stderr)
r = sp.run([sys.executable, os.path.join(HERE, "lander_clones.py")], input="{", capture_output=True, text=True)
check("broken input: fails open (exit 1)", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))
t = time.time()
for _ in range(200):
    lander_clones.check(blocked[8][0], "/", ps)
per = (time.time() - t) / 200
check(f"fast: {per * 1000:.2f} ms a check (< 10 ms); {dt * 1000:.0f} ms with python startup and ps (< 1 s)", per < 0.01 and dt < 1, dt)

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
