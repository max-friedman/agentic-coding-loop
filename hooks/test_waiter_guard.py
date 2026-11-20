#!/usr/bin/env python3
"""waiter_guard.py: blocks waiter loops whose `pgrep -f` pattern matches the loop itself.
python3 hooks/test_waiter_guard.py (or .claude/hooks/ once installed)"""

import json, os, re, subprocess as sp, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import waiter_guard as wg  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


def hook(cmd, tool="Bash"):
    return sp.run([sys.executable, os.path.join(HERE, "waiter_guard.py")],
                  input=json.dumps({"tool_name": tool, "tool_input": {"command": cmd}}), capture_output=True, text=True)


print("waiter_guard.py: blocked (the pattern matches the loop's own command line)")
blocked = [
    'until ! pgrep -f "run_suite.py --mode slow"; do sleep 10; done',
    "while pgrep -f land.sh >/dev/null; do sleep 30; done; echo done",
    "while pgrep -fl 'check.py' > /dev/null; do sleep 5; done",
    "until ! pgrep -af make; do sleep 10; done",
    'while [ -n "$(pgrep -f device_lock.py)" ]; do sleep 5; done',
    "while true; do pgrep -f run_suite >/dev/null || break; sleep 10; done",
    "while pgrep -u ci -f 'queue.py worker'; do sleep 60; done",
    "bash -c 'while pgrep -f postcheck.py; do sleep 9; done'",
    # The plain name is spelled elsewhere in the command, so even the bracket form matches itself.
    "python3 tests/run_suite.py & while pgrep -f '[r]un_suite.py'; do sleep 10; done",
]
for c in blocked:
    m = wg.check(c)
    check(f"blocks {c!r}", m is not None and "Blocked" in m, m)
m = wg.check('until ! pgrep -f "run_suite.py --mode slow"; do sleep 10; done')
check("the message gives the bracket form", m and "[r]un_suite.py --mode slow" in m, m)
check("the message suggests run_in_background", m and "run_in_background" in m, m)
fix = wg.fixed("run_suite.py --mode slow")
check("the suggested fix can't match the loop it would be written into",
      not re.search(fix, f'until ! pgrep -f "{fix}"; do sleep 10; done'), fix)

print("waiter_guard.py: allowed")
allowed = [
    "until ! pgrep -f '[r]un_suite.py --mode slow'; do sleep 10; done",
    "while pgrep -f '[l]and.sh 123' >/dev/null; do sleep 30; done",
    "pgrep -f run_suite.py",                      # a one-off check, no loop
    "pgrep -fl land.sh && echo running",
    "while pgrep make; do sleep 10; done",       # no -f: matches process names, not command lines
    "while kill -0 1234 2>/dev/null; do sleep 5; done",
    "for f in a b; do echo $f; done",
    "echo hello",
]
for c in allowed:
    check(f"allows {c!r}", wg.check(c) is None, wg.check(c))

print("waiter_guard.py: pgrep parsing")
for text, want in (("pgrep -u ci -f 'a b'", [(True, "a b")]), ("pgrep java", [(False, "java")]),
                   ('"$(pgrep -f x.py)"', [(True, "x.py")])):
    check(f"parses {text!r}", wg.pgrep_calls(text) == want, wg.pgrep_calls(text))
check("a bad regex falls back to a substring check", wg.matches_itself("a(b", "pgrep -f 'a(b'"))

print("waiter_guard.py: the hook process")
r = hook('until ! pgrep -f "run_suite.py"; do sleep 10; done')
check("a block is exit 2 with the reason on stderr", r.returncode == 2 and "Blocked" in r.stderr, r)
r = hook("until ! pgrep -f '[r]un_suite.py'; do sleep 10; done")
check("an allowed loop exits 0", r.returncode == 0, r)
r = hook("whatever", tool="Edit")
check("other tools pass", r.returncode == 0, r)
r = sp.run([sys.executable, os.path.join(HERE, "waiter_guard.py")], input="{bad", capture_output=True, text=True)
check("bad input fails open (exit 1)", r.returncode == 1 and "hook error" in r.stderr, r)

settings = json.load(open(os.path.join(HERE, "..", "templates", "project-kit", ".claude", "settings.json")))
bash = [h["command"] for g in settings["hooks"]["PreToolUse"] if g.get("matcher") == "Bash" for h in g["hooks"]]
check("settings.json runs it on Bash", any("waiter_guard.py" in c for c in bash), bash)

print(f"\n{'FAIL' if fails else 'OK'}: {len(fails)} failed")
sys.exit(1 if fails else 0)
