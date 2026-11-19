#!/usr/bin/env python3
"""gh_rules.py: blocks gh pr merge and a PR based on anything but main.  python3 .claude/hooks/test_gh_rules.py"""


import json, os, subprocess as sp, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gh_rules  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


def hook(cmd):
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "gh_rules.py")],
               input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}), capture_output=True, text=True)
    return r, time.time() - t


print("gh_rules.py")
blocked = [
    "gh pr merge 1234",
    "gh pr merge 1234 --squash --delete-branch",
    "gh pr merge --auto --squash 1234",
        "git push && gh pr merge 12 --squash",
    "bash -lc 'gh pr merge 12'",
    "gh pr create --base feat/other --title x --body y",
    "gh pr create -B feat/other --fill",
    "gh pr create --base=hooks/a --fill",
    "gh pr edit 12 --base feat/other",
]
allowed = [
    "scripts/land.sh 1234",
    "scripts/land.sh 1234",
    "gh pr view 1234 --json mergeCommit",
    "gh pr list --state merged",
    "gh pr create --title x --body y",
    "gh pr create --base main --fill",
    "gh pr create -B main --fill",
    "gh pr create --base=main --draft --fill",
    "gh pr edit 12 --add-label docs",
    "echo 'never gh pr merge'",
    "git commit -m 'no gh pr merge; base main'",
    "gh pr checks 12 --watch && git merge origin/main",
]
mine = gh_rules.origin_slug(HERE)
allowed += [
    "gh pr merge 40 --repo your-github-user/agentic-coding-loop --squash",
    "gh -R your-github-user/agentic-coding-loop pr merge 40",
    "gh pr merge 40 -R https://github.com/your-github-user/agentic-coding-loop",
]
blocked += [
    f"gh pr merge 40 --repo {mine}",
    f"gh pr merge 40 -R {mine}",
    f"gh pr merge 40 --repo=https://github.com/{mine}",
]
for c in blocked:
    check(f"blocks: {c[:70]!r}", gh_rules.check(c) is not None)
for c in allowed:
    check(f"allows: {c[:70]!r}", gh_rules.check(c) is None, gh_rules.check(c))

import tempfile
other = tempfile.mkdtemp()
sp.run(["git", "init", "-q", other])
sp.run(["git", "-C", other, "remote", "add", "origin", "git@github.com:your-github-user/agentic-coding-loop.git"])
check("cwd in another repo: allowed", gh_rules.check("gh pr merge 40", other) is None)
check("cwd in this repo: blocked", gh_rules.check("gh pr merge 40", HERE) is not None)
check("cwd without a repo: blocked", gh_rules.check("gh pr merge 40", tempfile.gettempdir()) is not None)
check("slug parse", gh_rules.repo_slug("https://github.com/A/b.git") == "a/b" and gh_rules.repo_slug("git@github.com:A/b.git") == "a/b")

r, dt = hook("gh pr merge 12 --squash")
check("gh pr merge: exit 2, says land.sh", r.returncode == 2 and "scripts/land.sh <PR>" in r.stderr, (r.returncode, r.stderr))
r, _ = hook("gh pr create --base feat/x --fill")
check("a stacked PR: exit 2, says base it on main", r.returncode == 2 and "on main" in r.stderr, r.stderr)
r, _ = hook("gh pr create --fill")
check("a PR on main: exit 0, no output", r.returncode == 0 and not r.stdout and not r.stderr, r.stderr)
r = sp.run([sys.executable, os.path.join(HERE, "gh_rules.py")], input="{", capture_output=True, text=True)
check("broken input: fails open (exit 1)", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))
t = time.time()
for _ in range(200):
    gh_rules.check(blocked[4])
per = (time.time() - t) / 200
check(f"fast: {per * 1000:.2f} ms a check (< 10 ms); {dt * 1000:.0f} ms with python startup (< 1 s)", per < 0.01 and dt < 1, dt)

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
