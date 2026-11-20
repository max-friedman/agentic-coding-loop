#!/usr/bin/env python3
"""
Remove finished worktrees, wherever they live, so they don't fill the disk.

In the project behind LOOP.md section F the disk filled twice with worktrees: once with 48 GB of them in the managed
directory, and once with 18 helper worktrees (~16 GB) outside it that sat for days after their PRs merged because no
cleanup looked there. So this looks at every worktree of the repository (`git worktree list --porcelain`), not one
directory.

    python3 scripts/worktree_gc.py            # what it would remove
    python3 scripts/worktree_gc.py --apply    # remove them (run it from the watchdog's schedule)

A worktree on a branch goes when all of these hold:
  - it is idle `worktree_gc.idle_hours` (6): nothing committed, checked out or staged in it for that long;
  - it is clean: no uncommitted or untracked changes (`git status --porcelain` prints nothing);
  - its work is done: the branch has no commits that aren't on origin/main (merged, or never started), or its pull
    request is merged or closed with the worktree still at that PR's head (one `gh pr list` per run; LOOP_GH_BIN).
A detached worktree goes once idle and clean if its commit is on origin/main.
Never removed: the main checkout, a locked worktree, one with a `.gc-keep` file, one a process has open (`lsof`, when it
is installed), and one whose branch or path a running lane holds in the lane ledger (.loop/lanes.json).
A worktree outside `git_rules.worktree_dirs` is named "outside the managed dirs" either way. Each removal is one JSON
line in .loop/worktree_gc.jsonl. Any git error on a worktree keeps it.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def git(cwd: str, *args: str) -> str | None:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, errors="replace")
    return r.stdout if r.returncode == 0 else None


def knobs(root: str) -> dict:
    try:
        cfg = json.loads(Path(root, ".loop", "config.json").read_text())
    except (OSError, ValueError):
        cfg = {}
    own = cfg.get("worktree_gc") if isinstance(cfg.get("worktree_gc"), dict) else {}
    dirs = (cfg.get("git_rules") or {}).get("worktree_dirs", [".claude/worktrees", "../{repo}-worktrees"])
    return {"idle_hours": 6, **own, "worktree_dirs": dirs}


def worktrees(root: str) -> list[dict]:
    """[{path, head, branch, locked}] from `git worktree list --porcelain`; the first is the main checkout."""
    out, cur = [], {}
    for line in (git(root, "worktree", "list", "--porcelain") or "").splitlines() + [""]:
        if not line:
            if cur:
                out.append(cur)
            cur = {}
            continue
        key, _, val = line.partition(" ")
        if key == "worktree":
            cur = {"path": val, "head": "", "branch": "", "locked": False}
        elif key == "HEAD":
            cur["head"] = val
        elif key == "branch":
            cur["branch"] = val.removeprefix("refs/heads/")
        elif key == "locked":
            cur["locked"] = True
    return out


def idle_s(path: str, now: float) -> float | None:
    """Seconds since the worktree's HEAD, index or reflog last changed; None when its git dir can't be read."""
    gd = git(path, "rev-parse", "--absolute-git-dir")
    if not gd:
        return None
    times = []
    for name in ("HEAD", "index", "logs/HEAD"):
        try:
            times.append(os.stat(os.path.join(gd.strip(), name)).st_mtime)
        except OSError:
            pass
    return now - max(times) if times else None


def busy(path: str) -> bool:
    """A process has a file open in the worktree's top directory (lsof +d); False when lsof isn't there."""
    if not shutil.which("lsof"):
        return False
    try:
        r = subprocess.run(["lsof", "-t", "+d", path], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return True  # can't tell in time: keep it
    return bool(r.stdout.strip())


def held_by_lanes(root: str) -> set[str]:
    try:
        doc = json.loads(Path(root, ".loop", "lanes.json").read_text() or "{}")
    except (OSError, ValueError):
        return set()
    held = set()
    for e in doc.get("lanes", []) if isinstance(doc, dict) else []:
        for k in ("branch", "worktree", "path"):
            if e.get(k):
                held.add(str(e[k]))
    return held


def closed_prs(root: str) -> dict[str, str]:
    """{head sha: state} of merged or closed PRs (one gh call); {} when gh can't tell."""
    try:
        r = subprocess.run([os.environ.get("LOOP_GH_BIN") or "gh", "pr", "list", "--state", "all", "--limit", "200",
                            "--json", "headRefOid,state"], cwd=root, capture_output=True, text=True, timeout=30)
        rows = json.loads(r.stdout) if r.returncode == 0 else []
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {}
    return {p["headRefOid"]: p["state"] for p in rows if p.get("state") in ("MERGED", "CLOSED") and p.get("headRefOid")}


def managed(path: str, root: str, dirs: list[str]) -> bool:
    name = os.path.basename(os.path.realpath(root))
    for d in dirs:
        base = os.path.realpath(os.path.join(root, os.path.expanduser(d.replace("{repo}", name))))
        if os.path.realpath(path).startswith(base + os.sep):
            return True
    return "/.claude/worktrees/" in path


def plan(root: str, now: float | None = None, prs=closed_prs) -> list[dict]:
    """The worktrees to remove, each with a `why`."""
    now = time.time() if now is None else now
    cfg = knobs(root)
    trees = worktrees(root)
    held = held_by_lanes(root)
    states = None
    out = []
    for wt in trees[1:]:
        path = wt["path"]
        if wt["locked"] or not os.path.isdir(path) or os.path.exists(os.path.join(path, ".gc-keep")):
            continue
        if wt["branch"] in held or path in held:
            continue
        idle = idle_s(path, now)
        if idle is None or idle < float(cfg["idle_hours"]) * 3600:
            continue
        status = git(path, "status", "--porcelain")
        if status is None or status.strip():
            continue
        if wt["branch"]:
            ahead = git(path, "rev-list", "--count", "origin/main..HEAD")
            if ahead is None:
                continue
            if int(ahead.strip() or 0) == 0:
                why = "no commits that aren't on origin/main"
            else:
                states = prs(root) if states is None else states
                if wt["head"] not in states:
                    continue
                why = f"its PR is {states[wt['head']].lower()} at this head"
        else:
            if git(path, "merge-base", "--is-ancestor", "HEAD", "origin/main") is None:
                continue
            why = "detached at a commit on origin/main"
        if busy(path):
            continue
        where = "" if managed(path, root, cfg["worktree_dirs"]) else " (outside the managed dirs)"
        out.append({**wt, "why": f"idle {idle / 3600:.1f} h, clean, {why}{where}"})
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="remove them (default: list only)")
    ap.add_argument("--repo", default=".", help="the repository (default: the current directory)")
    ns = ap.parse_args(argv)
    root = (git(ns.repo, "rev-parse", "--show-toplevel") or ns.repo).strip()
    git(root, "fetch", "-q", "origin")
    found = plan(root)
    for wt in found:
        if not ns.apply:
            print(f"worktree_gc: would remove {wt['path']} ({wt['why']})")
            continue
        if git(root, "worktree", "remove", wt["path"]) is None:
            print(f"worktree_gc: couldn't remove {wt['path']}; kept")
            continue
        print(f"worktree_gc: removed {wt['path']} ({wt['why']})")
        log = Path(root, ".loop", "worktree_gc.jsonl")
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a") as f:
            f.write(json.dumps({"at": int(time.time()), "path": wt["path"], "branch": wt["branch"], "why": wt["why"]}) + "\n")
    if not found:
        print("worktree_gc: nothing to remove")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
