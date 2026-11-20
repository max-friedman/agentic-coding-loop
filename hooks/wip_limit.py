#!/usr/bin/env python3
"""PreToolUse(Bash): a WIP limit on product pull requests. `gh pr create` is blocked while `wip_limit.max_open_prs`
(default 7) or more open, non-draft PRs change product code: land or close one first.

LOOP.md §F, Sizing rules 3 and 7: finished work piled up faster than it could be merged, and every extra open PR cost a
re-merge and a re-check each time the default branch moved. The limit is a backstop; watch for stale PRs too.

Product code: paths under `wip_limit.product_paths`, or, when that list is empty, every path except
`wip_limit.exempt_paths` and Markdown files. Exempt (the new PR goes through, and isn't counted for others): a
`--draft` PR, a branch whose changes touch no product code (docs-, tests- or scripts-only…), and branches starting
with one of `wip_limit.exempt_branches` (default `revert-`: a revert must never wait). `max_open_prs` 0 turns it off.

The open-PR list comes from `gh pr list` (LOOP_GH_BIN overrides gh), cached for 60 s (WIP_LIMIT_CACHE overrides the
cache file). WIP_LIMIT overrides the limit for one machine. Any error lets the call through (fails open).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _loop  # noqa: E402
import _shell  # noqa: E402

TTL_S = 60


def product(files: list[str], cfg: dict) -> bool:
    paths = tuple(cfg.get("product_paths") or ())
    exempt = tuple(cfg.get("exempt_paths") or ())
    for f in files:
        if paths:
            if f.startswith(paths) and not f.startswith(exempt):
                return True
        elif not f.startswith(exempt) and not f.endswith(".md"):
            return True
    return False


def run(cmd: list[str], cwd: str, timeout: float = 8) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:3])}: {(r.stderr or r.stdout).strip()[:200]}")
    return r.stdout


def create_args(cmd: str) -> tuple[list[str], str | None] | None:
    """(the args of the `gh pr create` in cmd, the directory a preceding cd moved to), or None when there's none."""
    here = None
    for seg in _shell.segments(cmd):
        _env, word, args = _shell.split_command(seg)
        base = os.path.basename(word)
        if base in ("cd", "pushd") and args:
            here = args[0]
        if base == "gh" and _shell.gh_subcommand(args)[:2] == ["pr", "create"]:
            return _shell.gh_subcommand(args)[2:], here
    return None


def opt(args: list[str], *names: str) -> str | None:
    for i, a in enumerate(args):
        for n in names:
            if a == n and i + 1 < len(args):
                return args[i + 1]
            if n.startswith("--") and a.startswith(n + "="):
                return a.split("=", 1)[1]
    return None


def cache_path(here: str) -> str:
    key = hashlib.sha1(os.path.realpath(here).encode()).hexdigest()[:10]
    return os.environ.get("WIP_LIMIT_CACHE") or os.path.join(tempfile.gettempdir(), f"loop-wip-{key}.json")


def open_prs(here: str) -> list[dict]:
    cache = cache_path(here)
    try:
        st = json.load(open(cache))
        if time.time() - st["at"] < TTL_S and st.get("cwd") == here:
            return st["prs"]
    except (OSError, ValueError, KeyError):
        pass
    gh = os.environ.get("LOOP_GH_BIN") or "gh"
    prs = json.loads(run([gh, "pr", "list", "--state", "open", "--limit", "100",
                          "--json", "number,title,headRefName,isDraft,files"], here))
    slim = [{"number": p.get("number"), "title": p.get("title") or "", "branch": p.get("headRefName") or "",
             "draft": bool(p.get("isDraft")), "files": [f.get("path", "") for f in p.get("files") or []]} for p in prs]
    try:
        with open(cache, "w") as f:
            json.dump({"at": time.time(), "cwd": here, "prs": slim}, f)
    except OSError:
        pass
    return slim


def check(cmd: str, cwd: str, cfg: dict | None = None) -> str | None:
    if "gh" not in cmd or "create" not in cmd:
        return None  # fast path
    found = create_args(cmd)
    if found is None:
        return None
    cfg = cfg if cfg is not None else _loop.config()["wip_limit"]
    limit = int(os.environ.get("WIP_LIMIT") or cfg.get("max_open_prs") or 0)
    if limit <= 0:
        return None
    args, cd = found
    if "--draft" in args or "-d" in args:
        return None
    here = _shell.resolve(cd, cwd) if cd else cwd
    branch = (opt(args, "--head", "-H") or run(["git", "rev-parse", "--abbrev-ref", "HEAD"], here).strip()).split(":")[-1]
    exempt = tuple(cfg.get("exempt_branches") or ())
    if exempt and branch.startswith(exempt):
        return None
    base = opt(args, "--base", "-B") or "main"
    mine = run(["git", "diff", "--name-only", f"origin/{base}...{branch}"], here).split()
    if not product(mine, cfg):
        return None
    wip = [p for p in open_prs(here) if not p["draft"] and p["branch"] != branch
           and not (exempt and p["branch"].startswith(exempt)) and product(p["files"], cfg)]
    if len(wip) < limit:
        return None
    listed = "\n".join(f"  #{p['number']} {p['title']} ({p['branch']})" for p in wip[:12])
    return (f"Blocked by .claude/hooks/wip_limit.py: {len(wip)} open pull requests already change product code (the "
            f"limit is {limit}, wip_limit.max_open_prs):\n{listed}\n"
            "Land or close one first; at the limit, do docs, tests or reviews. Drafts, PRs that change no product "
            "code, and exempt branches go through (`gh pr create --draft` still works).")


def main() -> None:
    try:
        data = _shell.read_input()
        if data.get("tool_name") != "Bash":
            sys.exit(0)
        msg = check((data.get("tool_input") or {}).get("command") or "", data.get("cwd") or os.getcwd())
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("wip_limit", e)
        return
    if msg:
        _shell.block(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
