#!/usr/bin/env python3
"""live_checkout.py against a throwaway "live checkout" (LOOP_LIVE_CHECKOUT): edits and git writes there are
blocked, worktrees and read-only git aren't.  python3 .claude/hooks/test_live_checkout.py"""

# The validation gate runs this file when one of these paths changes (scripts/validate.py reads GATE_COVERS).
# The project's Claude Code hooks (.claude/hooks/README.md): each hook's test, on any change there.
GATE_COVERS = (".claude/hooks/", ".claude/settings.json")

import json, os, subprocess as sp, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import live_checkout  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


root = os.path.realpath(tempfile.mkdtemp(prefix="live-hook-"))
live = os.path.join(root, "Projects", "app")
wt = os.path.join(live, ".claude", "worktrees", "agent-1")
sibling = os.path.join(root, "Projects", "app-worktrees", "land-5")
for d in (os.path.join(live, "service"), wt, sibling, os.path.join(root, "plugins")):
    os.makedirs(d, exist_ok=True)
link = os.path.join(root, "plugins", "service")
os.symlink(os.path.join(live, "service"), link)
ENV = {"LOOP_LIVE_CHECKOUT": live}
os.environ["HOME"] = root  # `cd $HOME/Projects/app` is the fake live checkout


def hook(payload):
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "live_checkout.py")], input=json.dumps(payload), capture_output=True, text=True,
               env={**os.environ, **ENV})
    return r, time.time() - t


edit = lambda p, cwd=wt: live_checkout.check_edit({"file_path": p}, cwd, ENV)
bash = lambda c, cwd=wt: live_checkout.check_bash(c, cwd, ENV)

print("live_checkout.py: Edit/Write")
check("blocks a file in the live checkout", edit(os.path.join(live, "CLAUDE.md")) is not None)
check("blocks a new file in a new folder there", edit(os.path.join(live, "docs", "new", "x.md")) is not None)
check("blocks a relative path that lands there", edit("../../../CLAUDE.md", cwd=wt) is not None)
check("blocks the plugin through its plugin symlink", edit(os.path.join(link, "adapter.py")) is not None)
check("allows a Claude Code worktree under .claude/worktrees/", edit(os.path.join(wt, "CLAUDE.md")) is None)
check("allows ~/Projects/app-worktrees/ (a prefix of the name, not the folder)", edit(os.path.join(sibling, "x.py")) is None)
check("allows memory and anything else outside", edit(os.path.join(root, ".claude", "projects", "m", "memory", "MEMORY.md")) is None)
check("allows NotebookEdit outside", live_checkout.check_edit({"notebook_path": "/tmp/x.ipynb"}, wt, ENV) is None)
check("blocks NotebookEdit inside", live_checkout.check_edit({"notebook_path": os.path.join(live, "n.ipynb")}, wt, ENV) is not None)

print("live_checkout.py: Bash git")
blocked = [
    ("git commit -m x", live), ("git push origin HEAD", live), ("git checkout -b feat", live), ("git merge origin/main", live),
    ("git reset --hard origin/main", live), ("git stash", live), ("git stash pop", live), ("git switch main", live),
    ("git add -A && git commit -m x", live), ("git pull", live), ("git rebase origin/main", live),
    (f"git -C {live} commit -m x", wt), (f"cd {live} && git commit -am x", wt), (f"cd {live}/docs && git add .", wt),
    (f"git -C {live} -c user.name=x commit -m y", wt), (f"git --work-tree={live} checkout -- .", wt),
    ("git -C ../../.. reset --hard", wt), (f"cd {wt}; cd {live}; git commit -m x", wt),
    (f"bash -c 'cd {live}'; git -C {live} stash push -m t", wt),
    (f"bash -c 'cd {live} && git commit -am x'", wt), ("cd $HOME/Projects/app && git commit -m x", wt),
]
for c, cwd in blocked:
    check(f"blocks {c!r} (cwd {'live' if cwd == live else 'worktree'})", bash(c, cwd) is not None)
allowed = [
    ("git status", live), ("git log --oneline -5", live), ("git diff origin/main", live), ("git fetch origin", live),
    ("git stash list", live), ("git stash show -p", live), ("git branch -a", live), ("git show HEAD:CLAUDE.md", live),
    (f"git worktree add -b x {sibling}2 origin/main", live), ("git worktree remove --force x", live), ("git worktree list", live),
    ("git commit -m x", wt), ("git push -u origin HEAD", wt), (f"git -C {wt} commit -m x", live),
    (f"cd {wt} && git commit -m x", live), (f"git -C {sibling} merge origin/main", live),
    ("scripts/land.sh 12", live), ("python3 scripts/deploy.py", live), (f"cd {live} && scripts/land.sh 12 --no-deploy", wt),
    ("echo 'git commit -m x'", live), ("grep -rn 'git reset' scripts/", live),
]
for c, cwd in allowed:
    check(f"allows {c!r} (cwd {'live' if cwd == live else 'worktree'})", bash(c, cwd) is None, bash(c, cwd))

r, dt = hook({"tool_name": "Write", "tool_input": {"file_path": os.path.join(live, "x.py"), "content": ""}, "cwd": wt})
check("Write in the live checkout: exit 2 with what to do instead", r.returncode == 2 and "worktree" in r.stderr and "land.sh" in r.stderr, r.returncode)
r, _ = hook({"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}, "cwd": live})
check("git commit with the live checkout as cwd: exit 2", r.returncode == 2 and "git commit" in r.stderr, r.stderr)
r, _ = hook({"tool_name": "Edit", "tool_input": {"file_path": os.path.join(wt, "x.py")}, "cwd": wt})
check("Edit in a worktree: exit 0, silent", r.returncode == 0 and not r.stderr and not r.stdout)
r, _ = hook({"tool_name": "Bash", "tool_input": {"command": "git commit -m 'x"}, "cwd": live})
check("unparseable command: fails closed (exit 2, 'blocked for safety')", r.returncode == 2 and "blocked for safety" in r.stderr, (r.returncode, r.stderr))
r = sp.run([sys.executable, os.path.join(HERE, "live_checkout.py")], input="{not json", capture_output=True, text=True, env={**os.environ, **ENV})
check("a crash (broken input): fails closed (exit 2), says to fix the hook", r.returncode == 2 and "hook error, blocked for safety" in r.stderr
      and "fix .claude/hooks/live_checkout.py" in r.stderr, (r.returncode, r.stderr))
r, _ = hook({"tool_name": "Bash"})
check("missing tool_input: exit 0", r.returncode == 0, r.stderr)
_, dt = hook({"tool_name": "Bash", "tool_input": {"command": f"cd {wt} && git add -A && git commit -m x && git push"}, "cwd": live})
t = time.time()
for _ in range(200):
    bash(f"cd {wt} && git add -A && git commit -m x && git push", live)
per = (time.time() - t) / 200
check(f"fast: {per * 1000:.2f} ms a check (< 10 ms); {dt * 1000:.0f} ms with python startup (< 1 s even on a loaded Mac)", per < 0.01 and dt < 1, dt)

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
