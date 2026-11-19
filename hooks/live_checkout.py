#!/usr/bin/env python3
"""PreToolUse(Edit|Write|NotebookEdit, Bash): never edit or commit in the live checkout (CLAUDE.md, Hard rules):
the checkout a running service uses, set in LOOP_LIVE_CHECKOUT. Unset, the hook guards nothing.

- Edit/Write/NotebookEdit: blocks a file under the live checkout unless it's under its .claude/worktrees/
  (Claude Code's worktrees). Symlinks are resolved, so a symlink into it counts as live.
  ~/.claude (user settings) and a sibling folder such as <checkout>-worktrees/ are outside it.
- Bash: blocks git commands that change a checkout (commit, push, merge, reset, stash push/pop…, checkout,
  switch, rebase, pull…) when their directory (the cwd after any `cd`, or `git -C <dir>`) is the live
  checkout. Read-only git (status, log, diff, fetch…) and `git worktree add/remove/list` are fine, and so
  are scripts (land.sh, a deploy script) whose git calls run inside them, not as Bash calls.

Fails closed: a hook error
(bad input, a command it can't parse) blocks the call.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _shell  # noqa: E402

WRITE = {"commit", "push", "merge", "reset", "checkout", "switch", "rebase", "cherry-pick", "revert", "am",
         "apply", "add", "rm", "mv", "restore", "clean", "pull", "commit-tree", "update-index"}
STASH_READ = {"list", "show"}
GLOBAL_WITH_ARG = {"-c", "--namespace", "--exec-path", "--config-env"}


def live_root(environ=os.environ) -> str:
    """The live checkout's real path, or "" when LOOP_LIVE_CHECKOUT isn't set (nothing is guarded)."""
    path = environ.get("LOOP_LIVE_CHECKOUT") or ""
    return os.path.realpath(os.path.expanduser(path)) if path else ""


def is_live(path: str, root: str) -> bool:
    return bool(root) and _shell.within(path, root) and not _shell.within(path, os.path.join(root, ".claude", "worktrees"))


def check_edit(tool_input: dict, cwd: str, environ=os.environ) -> str | None:
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not path:
        return None
    root = live_root(environ)
    full = _shell.resolve(path, cwd)
    if not is_live(full, root):
        return None
    return (f"Blocked by .claude/hooks/live_checkout.py: {path} is in the live checkout ({root}), which the live "
            "service runs from: never edit it (CLAUDE.md, Hard rules).\n"
            "Edit the same file in your own worktree instead (claude --worktree, or git worktree add -b <branch> "
            "<checkout>-worktrees/<name> origin/main) and land it with scripts/land.sh.")


def git_target(args: list[str], cwd: str) -> tuple[list[str], str]:
    """(the directories this git command acts on, its subcommand + args joined) for `git <global opts> sub …`."""
    dirs, here, i = [], cwd, 0
    while i < len(args) and args[i].startswith("-"):
        a = args[i]
        if a == "-C" and i + 1 < len(args):
            here = _shell.resolve(args[i + 1], here)
            i += 2
            continue
        if a.startswith(("--git-dir=", "--work-tree=")):
            dirs.append(_shell.resolve(a.split("=", 1)[1], here))
        elif a in ("--git-dir", "--work-tree") and i + 1 < len(args):
            dirs.append(_shell.resolve(args[i + 1], here))
            i += 1
        elif a in GLOBAL_WITH_ARG:
            i += 1
        i += 1
    dirs.append(here)
    return dirs, args[i:]


def is_write(sub: list[str]) -> bool:
    if not sub:
        return False
    if sub[0] == "stash":
        return not (len(sub) > 1 and sub[1] in STASH_READ)
    if sub[0] == "branch":
        return False  # refs are shared by every worktree; doesn't touch the live checkout's files
    return sub[0] in WRITE


def check_bash(cmd: str, cwd: str, environ=os.environ) -> str | None:
    if "git" not in cmd:
        return None  # fast path
    return _walk(cmd, os.path.realpath(cwd or os.getcwd()), live_root(environ), 0)


def _walk(cmd: str, here: str, root: str, depth: int) -> str | None:
    for seg in _shell.segments(cmd):
        env, word, args = _shell.split_command(seg)
        base = os.path.basename(word)
        if base in ("cd", "pushd"):
            target = next((a for a in args if not a.startswith("-")), "~")
            if target != "-":
                here = _shell.resolve(target, here)
            continue
        inner = _shell.shell_c_script(word, args)
        if inner is not None and depth < 3:
            msg = _walk(inner, here, root, depth + 1)
            if msg:
                return msg
            continue
        if base != "git":
            continue
        dirs, sub = git_target(args, here)
        if is_write(sub) and any(is_live(d, root) for d in dirs):
            return (f"Blocked by .claude/hooks/live_checkout.py: `git {' '.join(sub[:3])}` in the live checkout ({root}). "
                    "Never commit, switch branches or change files there (CLAUDE.md, Hard rules).\n"
                    "Work in your own worktree (git worktree add -b <branch> <checkout>-worktrees/<name> "
                    "origin/main) and land it with scripts/land.sh; only your deploy step updates the live checkout.")
    return None


def main() -> None:
    try:
        data = _shell.read_input()
        tool, tin, cwd = data.get("tool_name"), data.get("tool_input") or {}, data.get("cwd") or os.getcwd()
        if tool == "Bash":
            msg = check_bash(tin.get("command") or "", cwd)
        elif tool in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
            msg = check_edit(tin, cwd)
        else:
            msg = None
    except Exception as e:  # noqa: BLE001 - fail closed: a write to the live checkout can't be undone
        _shell.fail_closed("live_checkout", e)
        return
    if msg:
        _shell.block(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
