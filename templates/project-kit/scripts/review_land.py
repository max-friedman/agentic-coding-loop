#!/usr/bin/env python3
"""Land a reviewed PR: put the reviewer's line in its body, bring its exact branch up to main, run prelanding, land it.

    python3 scripts/review_land.py <PR> --line "Fidelity: OK (<reviewer>, <what they checked>)"
    python3 scripts/review_land.py <PR> --line "..." --dry-run   # say what it would do; change nothing

Why: a coordinator did these steps by hand, or with a wrapper in its scratch space, and it broke again and again on
branch names: a stale local branch with the PR's name, one checked out in another worktree, a worktree made on a
branch that wasn't the PR's. This does them in order and stops at the first thing it can't do safely:

1. the PR's exact head branch and commit (gh: headRefName, headRefOid), fetched from origin; if origin's head isn't
   the PR's head, it stops (the PR moved);
2. a worktree on that branch: the one that already has it checked out (it must be clean; never the live checkout,
   LOOP_LIVE_CHECKOUT), else `review-<PR>` under `review_land.worktree_dir` on the existing local branch, else a new
   local branch from origin's. A local branch behind origin is fast-forwarded; one with commits the PR lacks stops
   (push them, or delete the branch);
3. origin/main merged in when the branch is behind it, then pushed; a conflict aborts the merge and stops with the
   files: resolve them on the branch by hand;
4. the review line set in the PR body (replacing an earlier line of the same name; else before `## Release note`,
   else at the end), through a per-PR body file ($TMPDIR/<PR>/body.md, never a shared path);
5. scripts/prelanding.py in that worktree; on a pass, `review_land.after` (default `scripts/land.sh {pr}`; point it at
   your queue's add command if you run a queue).

It writes only the line it is given: the review is the reviewer's (a fresh agent or the owner, never the author or the
coordinator), and prelanding still judges the line (`prelanding.review_lines`). It changes no gate.
Exit: 0 landed or queued (or --dry-run), 1 prelanding failed, 2 usage or setup, 3 conflict with main, 4 branch state
(diverged, dirty, or not the PR's head), 5 the `after` command failed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULTS = {"worktree_dir": "../{repo}-worktrees", "after": "scripts/land.sh {pr}"}  # as hooks/_loop.py's "review_land"
LINE = re.compile(r"^\s*([A-Za-z][\w -]{0,40}):\s*(.+?)\s*$")
RELEASE_NOTE = re.compile(r"^#{1,6}\s*release notes?\s*$", re.I | re.M)


class Stop(Exception):
    def __init__(self, code: int, msg: str):
        super().__init__(msg)
        self.code = code


def say(msg: str) -> None:
    print(f"review_land: {msg}", flush=True)


def knobs(root: Path = REPO) -> dict:
    try:
        own = json.loads((root / ".loop" / "config.json").read_text()).get("review_land", {})
    except (OSError, ValueError, AttributeError):
        own = {}
    return {**DEFAULTS, **(own if isinstance(own, dict) else {})}


def git(cwd: Path, *a: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        raise Stop(2, f"git {' '.join(a[:3])} failed: {(r.stderr or r.stdout).strip()[-300:]}")
    return r


def out(cwd: Path, *a: str) -> str:
    return git(cwd, *a).stdout.strip()


def is_ancestor(cwd: Path, a: str, b: str) -> bool:
    return git(cwd, "merge-base", "--is-ancestor", a, b, check=False).returncode == 0


def pr_info(n: int) -> dict:
    r = subprocess.run(["gh", "pr", "view", str(n), "--json", "number,headRefName,headRefOid,body,state,isCrossRepository"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode:
        raise Stop(2, f"gh pr view {n} failed: {(r.stderr or r.stdout).strip()[-300:]}")
    return json.loads(r.stdout or "{}")


def edit_body(n: int, path: Path) -> None:
    r = subprocess.run(["gh", "pr", "edit", str(n), "--body-file", str(path)], cwd=REPO, capture_output=True, text=True)
    if r.returncode:
        raise Stop(2, f"gh pr edit {n} failed: {(r.stderr or r.stdout).strip()[-300:]}")


# ---- the review line

def parse_line(line: str) -> tuple[str, str]:
    """(name, the whole line) of `Name: verdict`."""
    m = LINE.match(line or "")
    if not m or not m.group(2).strip():
        raise Stop(2, '--line must be "<Name>: <verdict>", e.g. "Fidelity: OK (fresh-reviewer, checked a, b)"')
    return m.group(1).strip(), f"{m.group(1).strip()}: {m.group(2).strip()}"


def set_line(body: str, name: str, line: str) -> str:
    """The body with `line` as its only `name:` line: in place of the first earlier one, else before
    `## Release note`, else at the end."""
    body = body or ""
    rx = re.compile(r"^[ \t>*_-]*" + re.escape(name) + r":\**[ \t]*.*$", re.I | re.M)
    if rx.search(body):
        first = [True]

        def put(_m):
            if first[0]:
                first[0] = False
                return line
            return "\x00"
        return re.sub(r"\x00\n?", "", rx.sub(put, body))
    m = RELEASE_NOTE.search(body)
    if m:
        return body[:m.start()] + line + "\n\n" + body[m.start():]
    return body.rstrip("\n") + "\n\n" + line + "\n"


def body_file(n: int, tmp: Optional[Path] = None) -> Path:
    d = (tmp or Path(os.getenv("TMPDIR") or tempfile.gettempdir())) / str(n)
    d.mkdir(parents=True, exist_ok=True)
    return d / "body.md"


# ---- the worktree on the PR's branch

def worktree_of(repo: Path, branch: str) -> Optional[Path]:
    path = None
    for line in out(repo, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree "):])
        elif line == f"branch refs/heads/{branch}" and path is not None:
            return path
    return None


def checkout(repo: Path, n: int, branch: str, head: str, worktrees: Path, dry: bool = False) -> Path:
    """A clean worktree on `branch` at the PR's head `head` (steps 1-2)."""
    git(repo, "fetch", "-q", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}")
    remote = out(repo, "rev-parse", f"refs/remotes/origin/{branch}")
    if remote != head:
        raise Stop(4, f"origin's {branch} is at {remote[:9]}, the PR's head is {head[:9]}: the PR moved; run this again")
    wt = worktree_of(repo, branch)
    local = git(repo, "rev-parse", "-q", "--verify", f"refs/heads/{branch}", check=False).stdout.strip()
    live = os.getenv("LOOP_LIVE_CHECKOUT")
    if wt is not None and live and wt.resolve() == Path(live).expanduser().resolve():
        raise Stop(4, f"{branch} is checked out in the live checkout {live}, which is never edited")
    if wt is not None:
        if git(wt, "status", "--porcelain", "--untracked-files=no").stdout.strip():
            raise Stop(4, f"{wt} has {branch} checked out with uncommitted changes: commit or discard them first")
        say(f"using {wt}, which has {branch} checked out")
    else:
        wt = worktrees / f"review-{n}"
        if wt.exists():
            raise Stop(4, f"{wt} exists but isn't on {branch}: remove it (git worktree remove {wt}) and run this again")
        if dry:
            say(f"would add {wt} on {'the existing local ' if local else 'a new local '}{branch}")
            return wt
        worktrees.mkdir(parents=True, exist_ok=True)
        if local:
            git(repo, "worktree", "add", "-q", str(wt), branch)
            say(f"added {wt} on the existing local branch {branch}")
        else:
            git(repo, "worktree", "add", "-q", "-b", branch, str(wt), f"refs/remotes/origin/{branch}")
            git(wt, "branch", "-q", f"--set-upstream-to=origin/{branch}", check=False)
            say(f"added {wt} on a new local {branch} from origin")
    cur = out(wt, "rev-parse", "HEAD")
    if cur != head:
        if not is_ancestor(wt, cur, head):
            extra = out(wt, "rev-list", "--count", f"{head}..{cur}")
            raise Stop(4, f"the local {branch} has {extra} commit(s) the PR doesn't ({cur[:9]} vs {head[:9]}): push them "
                          "if they belong to the PR, or delete that branch, then run this again")
        if not dry:
            git(wt, "merge", "-q", "--ff-only", f"refs/remotes/origin/{branch}")
        say(f"fast-forwarded the stale local {branch} from {cur[:9]} to {head[:9]}")
    if not dry and out(wt, "rev-parse", "HEAD") != head:
        raise Stop(4, f"{wt} isn't at the PR's head {head[:9]} after syncing")
    return wt


def merge_main(wt: Path, branch: str, dry: bool = False) -> bool:
    """origin/main merged in when the branch is behind it, then pushed (step 3). True when it merged."""
    git(wt, "fetch", "-q", "origin", "main")
    if is_ancestor(wt, "origin/main", "HEAD"):
        say("the branch already contains origin/main")
        return False
    if dry:
        say("would merge origin/main into it and push")
        return False
    m = git(wt, "merge", "-q", "--no-edit", "origin/main", check=False)
    if m.returncode:
        files = git(wt, "diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
        git(wt, "merge", "--abort", check=False)
        raise Stop(3, f"merging origin/main into {branch} conflicts in: {', '.join(files) or m.stderr.strip()[-200:]}. "
                      f"Resolve it on the branch (in {wt}: git merge origin/main), push, and run this again")
    git(wt, "push", "-q", "origin", f"HEAD:refs/heads/{branch}")
    say(f"merged origin/main and pushed {out(wt, 'rev-parse', '--short', 'HEAD')}")
    return True


# ---- main

def run(n: int, review: str, repo: Path = REPO, worktrees: Optional[Path] = None, after: Optional[str] = None,
        info: Callable[[int], dict] = pr_info, edit: Callable[[int, Path], None] = edit_body,
        cmd: Optional[Callable[[list[str], Path], int]] = None, tmp: Optional[Path] = None, dry: bool = False) -> int:
    cmd = cmd or (lambda c, cwd: subprocess.run(c, cwd=cwd).returncode)
    cfg = knobs(repo)
    if worktrees is None:
        worktrees = (repo / cfg["worktree_dir"].format(repo=repo.name)).resolve()
    after = after if after is not None else cfg["after"]
    name, line = parse_line(review)
    pr = info(n)
    if pr.get("state") and pr["state"] != "OPEN":
        raise Stop(2, f"#{n} is {pr['state'].lower()}, not open")
    if pr.get("isCrossRepository"):
        raise Stop(2, f"#{n} comes from a fork: land it by hand")
    branch, head = pr.get("headRefName") or "", pr.get("headRefOid") or ""
    if not branch or not head:
        raise Stop(2, f"gh gave no head branch for #{n}")
    wt = checkout(repo, n, branch, head, worktrees, dry)
    if wt.exists():
        merge_main(wt, branch, dry)
    else:
        say("would merge origin/main into it if it is behind, and push")
    then = shlex.split(after.format(pr=n)) if after else []
    if dry:
        say(f"would set `{line}` in #{n}'s body, run prelanding in {wt}, then: {' '.join(then) or 'nothing'}")
        return 0
    new = set_line(pr.get("body") or "", name, line)
    if new != (pr.get("body") or ""):
        f = body_file(n, tmp)
        f.write_text(new)
        edit(n, f)
        say(f"set `{line}` in #{n}'s body (via {f})")
    else:
        say(f"#{n}'s body already has `{line}`")
    rc = cmd([sys.executable, str(wt / "scripts" / "prelanding.py")], wt)
    if rc:
        say(f"prelanding exited {rc}: not landed (fix what it says, then run this again)")
        return 1
    if then:
        rc = cmd(then, wt)
        if rc:
            say(f"{' '.join(then)} exited {rc}")
            return 5
        say(f"#{n}: {' '.join(then)} done")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pr", type=int)
    ap.add_argument("--line", required=True, help='the reviewer\'s line, e.g. "Fidelity: OK (fresh-reviewer, checked a, b)"')
    ap.add_argument("--dry-run", action="store_true", help="say what it would do; change nothing")
    a = ap.parse_args(argv)
    try:
        return run(a.pr, a.line, dry=a.dry_run)
    except Stop as e:
        say(str(e))
        return e.code


if __name__ == "__main__":
    sys.exit(main())
