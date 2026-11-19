#!/usr/bin/env python3
"""git_rules.py: blocks a bare stash and a merge chained with add/commit.  python3 .claude/hooks/test_git_rules.py"""

# The validation gate runs this file when one of these paths changes (scripts/validate.py reads GATE_COVERS).
# The project's Claude Code hooks (.claude/hooks/README.md): each hook's test, on any change there.
GATE_COVERS = (".claude/hooks/", ".claude/settings.json")

import json, os, subprocess as sp, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import git_rules  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


def hook(cmd):
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "git_rules.py")],
               input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}), capture_output=True, text=True)
    return r, time.time() - t


print("git_rules.py: stash")
blocked = [
    "git stash",
    "git stash -u",
    "git stash push",
    "git stash push -u",
    "git stash pop",
    "git stash pop stash@{2}",
    "git stash clear",
    "git stash save 'wip'",
    "git stash apply",
    "git stash drop",
    "git stash branch tmp",
    "git -C ../other stash pop",
    "cd app && git stash && make test && git stash pop",
    "bash -c 'git stash'",
    "git status; git stash",
]
allowed = [
    "git stash push -u -m 'hooks-wip-1'",
    "git stash push -m hooks-wip-1",
    "git stash push --message=hooks-wip-1",
    "git stash -u -m hooks-wip-1",
    "git stash push -um hooks-wip-1",
    "git stash list",
    "git stash list --format='%H %gs'",
    "git stash show -p stash@{1}",
    "git stash apply 3f2a9c1",
    "git stash apply stash@{1}",
    "git stash drop stash@{1}",
    "git stash branch tmp stash@{1}",
    "echo 'never git stash pop'",
    "grep -rn 'git stash' docs/",
    "git commit -m 'docs: never git stash pop'",
]
for c in blocked:
    check(f"blocks: {c!r}", git_rules.check(c) is not None)
for c in allowed:
    check(f"allows: {c!r}", git_rules.check(c) is None, git_rules.check(c))

print("git_rules.py: merge chained with add/commit")
blocked_m = [
    "git merge origin/main && git commit -am 'merge main'",
    "git merge --no-edit origin/main; git add -A; git commit --no-edit",
    "git fetch origin && git merge origin/main && git add . && git push",
    "git -C wt merge origin/main && git -C wt commit --no-edit",
    "git merge origin/main\ngit commit -m x",
]
allowed_m = [
    "git merge origin/main",
    "git merge --no-edit origin/main && git push",
    "git add -A && git commit -m x && git merge origin/main",  # commit before the merge
    "git merge --abort && git commit -m x",
    "git merge-base HEAD origin/main && git commit -m x",
    "git commit -m 'merge main in' && git push",
    "gh pr merge 5; git commit -m x",  # not git merge (gh_rules.py handles gh pr merge)
]
for c in blocked_m:
    check(f"blocks: {c[:70]!r}", git_rules.check(c) is not None)
for c in allowed_m:
    check(f"allows: {c[:70]!r}", git_rules.check(c) is None, git_rules.check(c))

r, dt = hook("git stash pop")
check("a stash pop: exit 2, says how to stash safely", r.returncode == 2 and "git stash push -u -m" in r.stderr
      and "apply <sha>" in r.stderr, (r.returncode, r.stderr))
r, _ = hook("git merge origin/main && git commit -am x")
check("merge && commit: exit 2, says to check conflicts first", r.returncode == 2 and "diff-filter=U" in r.stderr, r.stderr)
r, _ = hook("git stash list")
check("stash list: exit 0, no output", r.returncode == 0 and not r.stdout and not r.stderr, r.stderr)
r = sp.run([sys.executable, os.path.join(HERE, "git_rules.py")], input="{", capture_output=True, text=True)
check("broken input: fails open (exit 1)", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))
r = sp.run([sys.executable, os.path.join(HERE, "git_rules.py")],
           input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git stash 'unbalanced"}}), capture_output=True, text=True)
check("a command it can't tokenize: fails open (exit 1)", r.returncode == 1, (r.returncode, r.stderr))
t = time.time()
for _ in range(200):
    git_rules.check(blocked_m[2])
per = (time.time() - t) / 200
check(f"fast: {per * 1000:.2f} ms a check (< 10 ms); {dt * 1000:.0f} ms with python startup (< 1 s)", per < 0.01 and dt < 1, dt)

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
