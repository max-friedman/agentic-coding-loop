#!/usr/bin/env python3
"""PreToolUse(Bash): pull requests reach main only one way (CLAUDE.md, Hard rules; docs/process/landing.md).

Blocks:
- Only when `gh_rules.block_pr_merge` is true in `.loop/config.json` (default off: it's a landing-process opinion):
  `gh pr merge` (any flags, --auto too) aimed at THIS repo (no `--repo`/`-R` and the working directory's origin is this
  repo, or `--repo` names it; the name comes from this checkout's git remote): PRs land with `scripts/land.sh <PR>`, which checks the head passed
  prelanding and merges under the landing lock. land.sh's own `gh pr merge` runs inside the script, not as a Bash call,
  so it isn't affected. A merge aimed at another repository (`--repo owner/other`, or a cwd whose origin is another
  repo) is allowed: land.sh only lands this repo's PRs. If the target can't be told, it is blocked.
- `gh pr create` / `gh pr edit` with a `--base` (`-B`) other than main: a PR stacked on another PR's branch is
  auto-closed when that branch is deleted on merge (twice). Base every PR on main.

Fails open on its own errors (a miss is a PR merged or based the wrong way, which the coordinator sees and fixes).
"""
from __future__ import annotations

import functools
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _loop  # noqa: E402
import _shell  # noqa: E402

MAIN = {"main", "origin/main"}


def base_of(args: list[str]) -> str | None:
    """The --base/-B value in a gh pr create/edit's args, else None."""
    for i, a in enumerate(args):
        if a in ("--base", "-B"):
            return args[i + 1] if i + 1 < len(args) else ""
        if a.startswith("--base="):
            return a.split("=", 1)[1]
        if a.startswith("-B") and len(a) > 2:
            return a[2:]
    return None


def repo_slug(url: str) -> str | None:
    """`owner/name` of a GitHub remote URL (https or ssh), lowercased; None if it isn't one."""
    m = re.search(r"github\.com[:/]+([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", url.strip())
    return f"{m.group(1)}/{m.group(2)}".lower() if m else None


@functools.lru_cache(maxsize=16)
def origin_slug(cwd: str | None) -> str | None:
    try:
        out = subprocess.run(["git", "remote", "get-url", "origin"], cwd=cwd or None, capture_output=True,
                             text=True, timeout=3).stdout
    except Exception:  # noqa: BLE001
        return None
    return repo_slug(out)


def repo_flag(args: list[str]) -> str | None:
    """The -R/--repo value anywhere in a gh command's args, else None."""
    for i, a in enumerate(args):
        if a in ("-R", "--repo"):
            return args[i + 1] if i + 1 < len(args) else ""
        if a.startswith("--repo="):
            return a.split("=", 1)[1]
        if a.startswith("-R") and len(a) > 2:
            return a[2:]
    return None


def targets_this_repo(args: list[str], cwd: str | None) -> bool:
    """True unless the gh command is positively aimed at another repository."""
    mine = origin_slug(os.path.dirname(os.path.abspath(__file__)))
    flag = repo_flag(args)
    if flag is not None:
        theirs = repo_slug("github.com/" + flag.split("github.com/")[-1]) if flag else None
        return theirs is None or mine is None or theirs == mine
    there = origin_slug(cwd)
    return there is None or mine is None or there == mine


def merge_blocked() -> bool:
    """The repo-wide `gh pr merge` block is opt-in (`gh_rules.block_pr_merge` in .loop/config.json); a config that
    can't be read leaves it off, like every other failure of this hook."""
    try:
        return bool(_loop.config()["gh_rules"]["block_pr_merge"])
    except Exception:  # noqa: BLE001
        return False


def check(cmd: str, cwd: str | None = None) -> str | None:
    if "gh" not in cmd or ("merge" not in cmd and "base" not in cmd and "-B" not in cmd):
        return None
    for _env, word, args in _shell.commands(cmd):
        if os.path.basename(word) != "gh":
            continue
        sub = _shell.gh_subcommand(args)
        if sub[:2] == ["pr", "merge"] and merge_blocked() and targets_this_repo(args, cwd):
            return ("Blocked by .claude/hooks/gh_rules.py: `gh pr merge` is off limits here (gh_rules.block_pr_merge is on in .loop/config.json). Land with "
                    "`scripts/land.sh <PR>`: it checks the PR's head passed prelanding and merges it under the landing "
                    "lock (docs/process/landing.md). A helper hands back instead; the coordinator runs land.sh.")
        if sub[:2] in (["pr", "create"], ["pr", "edit"]):
            base = base_of(sub[2:])
            if base is not None and base not in MAIN:
                return (f"Blocked by .claude/hooks/gh_rules.py: `--base {base}` stacks this PR on another branch; when "
                        "that branch merges and is deleted, GitHub closes this PR (it happened twice). Base every PR "
                        "on main (drop --base, or `--base main`); if it needs another PR's change, wait for that one "
                        "to land and merge main in.")
    return None


def main() -> None:
    try:
        data = _shell.read_input()
        msg = check((data.get("tool_input") or {}).get("command") or "", data.get("cwd")) if data.get("tool_name") == "Bash" else None
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("gh_rules", e)
        return
    if msg:
        _shell.block(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
