#!/usr/bin/env python3
"""git_rules.py: blocks a bare stash, a merge chained with add/commit, a skipped gate and a helper's stray worktree.  python3 .claude/hooks/test_git_rules.py"""


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

import tempfile  # noqa: E402
PROJ = os.path.realpath(tempfile.mkdtemp(prefix="git-rules-proj-"))
os.makedirs(os.path.join(PROJ, ".loop"))
with open(os.path.join(PROJ, ".loop", "coordinator_session.json"), "w") as f:
    json.dump({"session_id": "COORD", "at": 0}, f)
os.environ["CLAUDE_PROJECT_DIR"] = PROJ
NAME = os.path.basename(PROJ)
CFG = git_rules._cfg()

print("git_rules.py: worktrees outside the managed dirs (a warning; a block for a helper)")
# A project outside $TMPDIR (nothing is created there: the rule only resolves paths).
P2 = "/srv/work/proj"
W = lambda c, cwd=P2: git_rules.worktree_warning(c, cwd, CFG, P2)  # noqa: E731
check("a sibling dir warns", "outside" in (W("git worktree add -b feat/x ../stray-x origin/main") or ""))
check("an absolute path elsewhere warns", W("git worktree add /srv/elsewhere/y") is not None)
check("git -C <dir> moves the base", W(f"git -C {P2} worktree add ../proj-worktrees/z", "/") is None)
check("../<repo>-worktrees is fine", W("git worktree add -b process/x ../proj-worktrees/x origin/main") is None)
check("a .claude/worktrees one is fine", W("git worktree add .claude/worktrees/agent-1") is None)
check("$TMPDIR / /tmp throwaways are fine", W("git worktree add --detach /tmp/lander-1 HEAD") is None
      and W(f"git worktree add {os.path.realpath(os.getenv('TMPDIR') or '/tmp')}/tmp.abc") is None)
check("other worktree verbs don't warn", W("git worktree remove ../stray-x") is None and W("git worktree list") is None)
check("no worktree_dirs: the rule is off", git_rules.worktree_warning("git worktree add ../stray", PROJ, {"worktree_dirs": []}, PROJ) is None)


def hook_as(cmd, **extra):
    return sp.run([sys.executable, os.path.join(HERE, "git_rules.py")], capture_output=True, text=True,
                  env={**os.environ, "CLAUDE_PROJECT_DIR": PROJ},
                  input=json.dumps({"tool_name": "Bash", "cwd": PROJ, "tool_input": {"command": cmd}, **extra}))


r = hook_as("git worktree add /srv/elsewhere/stray-q", session_id="COORD")
out = json.loads(r.stdout or "{}")
check("the coordinator's only warns (exit 0, JSON on stdout)", r.returncode == 0 and "outside" in out.get("systemMessage", "")
      and "outside" in out.get("hookSpecificOutput", {}).get("additionalContext", ""), (r.returncode, r.stdout, r.stderr))
r = hook_as("git worktree add /srv/elsewhere/stray-q", session_id="COORD", agent_id="a123")
check("a helper's stray worktree is blocked (exit 2)", r.returncode == 2 and "Blocked by" in r.stderr, (r.returncode, r.stderr))
r = hook_as(f"git worktree add ../{NAME}-worktrees/q", session_id="COORD", agent_id="a123")
check("a helper's worktree in the managed dir runs", r.returncode == 0 and not r.stderr, (r.returncode, r.stderr))

print("git_rules.py: never skip a gate")
G = lambda c, **d: git_rules.skip_gate(c, d, CFG)  # noqa: E731
for c in ["git commit --no-verify -m x", "git commit -n -m x", "git commit -anm 'x'", "git -C wt commit -n",
          "git push --no-verify origin HEAD", "cd wt && git add -A && git commit --no-verify -F body.md"]:
    check(f"blocks: {c!r}", G(c) is not None)
for c in ["git commit -m 'never use -n or --no-verify'", "git commit -m -n", "git commit -F msg -a",
          "git push -n origin HEAD", "git commit -am x", "git commit --amend --no-edit", "git log -n 3",
          "echo git commit --no-verify"]:
    check(f"allows: {c!r}", G(c) is None, G(c))
check("block_no_verify off: allowed", git_rules.skip_gate("git commit -n -m x", {}, {**CFG, "block_no_verify": False}) is None)
NP = "scripts/land.sh 12 --no-prelanding"
check("an override flag from a helper subagent is blocked", G(NP, session_id="COORD", agent_id="a1") is not None)
check("…from another session is blocked", G(NP, session_id="OTHER") is not None)
check("…from no session is blocked", G("python3 scripts/prelanding.py --skip-checks") is not None)
check("…from the registered coordinator passes", G(NP, session_id="COORD") is None, G(NP, session_id="COORD"))
check("a landing without it passes", G("scripts/land.sh 12", agent_id="a1") is None)
r = hook_as("git commit --no-verify -m x", session_id="COORD")
check("the hook blocks --no-verify (exit 2)", r.returncode == 2 and "Never skip a gate" in r.stderr, (r.returncode, r.stderr))

print("git_rules.py: gate-changing environment prefixes warn")
E = lambda c: git_rules.env_warning(c, CFG)  # noqa: E731
for c in ["WIP_LIMIT=99 gh pr create --fill", "PRELANDING_CHECKS=true python3 scripts/prelanding.py",
          "FOO_SKIP_CHECKS=1 python3 scripts/prelanding.py", "git -c core.hooksPath=/dev/null commit -m x"]:
    check(f"warns: {c!r}", E(c) is not None)
for c in ["LOOP_HOME=/tmp/x python3 tests/run.py", "DEBUG=1 make test", "git commit -m x"]:
    check(f"quiet: {c!r}", E(c) is None, E(c))
r = hook_as("WIP_LIMIT=20 gh pr create --fill", session_id="COORD")
check("the hook warns and runs (exit 0)", r.returncode == 0 and "WIP_LIMIT" in r.stdout, (r.returncode, r.stdout, r.stderr))

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
