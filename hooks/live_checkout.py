#!/usr/bin/env python3
"""PreToolUse hook (Edit|Write|NotebookEdit, Bash): never edit or commit in the checkout a live service runs from.

If a service runs from a checkout (a plugin symlinked into its host, a server
started from the repo), an edit there is an unreviewed deploy. Every session works
in its own worktree and lands by pull request; only the deploy script changes the
live checkout.

Set LIVE_CHECKOUT to that checkout's path. Blocked: file edits under it, and git
commands that change a checkout (commit, merge, reset, checkout, stash, pull, ...)
when their directory is it. Allowed: read-only git (status, log, diff, fetch) and
`git worktree add/remove/list`, which is how sessions get their own copy.

Fails CLOSED on its own errors: an edit to a live service can't be taken back.
"""
from __future__ import annotations

import json
import os
import shlex
import sys

WRITE_VERBS = {"commit", "push", "merge", "reset", "checkout", "switch", "rebase", "cherry-pick", "revert",
               "am", "apply", "add", "rm", "mv", "restore", "clean", "pull", "stash"}


def within(path: str, root: str) -> bool:
    path, root = os.path.realpath(path), os.path.realpath(root)
    return path == root or path.startswith(root + os.sep)


def check_edit(tool_input: dict, root: str) -> str | None:
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if path and within(path, root):
        return f"Blocked: {path} is in the live checkout. Work in your own worktree (`git worktree add`) and land by PR."
    return None


def check_bash(cmd: str, cwd: str, root: str) -> str | None:
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|")
    lex.whitespace_split = True
    words, here = list(lex), cwd
    for i, word in enumerate(words):
        if word == "cd" and i + 1 < len(words):
            here = os.path.join(here, os.path.expanduser(words[i + 1]))
        if word != "git":
            continue
        rest, where = words[i + 1:], here
        if rest[:1] == ["-C"] and len(rest) > 1:
            where, rest = os.path.join(here, os.path.expanduser(rest[1])), rest[2:]
        if rest and rest[0] in WRITE_VERBS and within(where, root):
            return (f"Blocked: `git {rest[0]}` in the live checkout. Use your own worktree and land by PR; "
                    "only the deploy script changes the live checkout.")
    return None


def main() -> int:
    try:
        root = os.environ["LIVE_CHECKOUT"]
        data = json.load(sys.stdin)
        tool, ti = data.get("tool_name"), data.get("tool_input") or {}
        if tool in ("Edit", "Write", "NotebookEdit"):
            msg = check_edit(ti, root)
        elif tool == "Bash":
            msg = check_bash(ti.get("command") or "", data.get("cwd") or os.getcwd(), root)
        else:
            msg = None
    except Exception as e:  # noqa: BLE001 - fail closed
        msg = f"Blocked: live_checkout hook error ({e}), blocked for safety. Fix the hook by PR."
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
