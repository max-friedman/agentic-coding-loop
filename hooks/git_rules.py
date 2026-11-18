#!/usr/bin/env python3
"""PreToolUse hook (Bash): no bare `git stash`, and no `git merge` chained with `add`/`commit`.

- The stash stack is shared by every worktree of a repository. With several agent
  sessions in several worktrees, `git stash pop` can take another session's work.
  Set work aside with a WIP commit instead. Blocked: `git stash` (bare, push, save),
  `pop`, `apply`, `drop` and `clear`. Allowed: `list` and `show`.
- `git merge main && git add -A && git commit` commits conflict markers when the
  merge conflicts. In the project behind this repo, markers reached a pushed branch
  four times that way. Run the merge alone, check it, then add and commit.

Fails open on its own errors: a miss here is recoverable from the reflog.
"""
from __future__ import annotations

import json
import shlex
import sys

SEPARATORS = {";", "&&", "||", "|", "&", "\n"}


def commands(cmd: str) -> list[list[str]]:
    """The command split into simple commands, each a list of words."""
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|")
    lex.whitespace_split = True
    out, cur = [], []
    for word in lex:
        if word in SEPARATORS:
            out, cur = out + [cur] if cur else out, []
        else:
            cur.append(word)
    return out + [cur] if cur else out


def git_verb(words: list[str]) -> tuple[str | None, list[str]]:
    if not words or words[0] != "git":
        return None, []
    rest = words[1:]
    while rest and rest[0].startswith("-"):  # git -C dir, git -c k=v
        rest = rest[2:] if rest[0] in ("-C", "-c") else rest[1:]
    return (rest[0], rest[1:]) if rest else (None, [])


def check(cmd: str) -> str | None:
    merged = False
    for words in commands(cmd):
        verb, args = git_verb(words)
        if verb == "stash":
            sub = args[0] if args and not args[0].startswith("-") else "push"
            if sub not in ("list", "show"):
                return (f"Blocked: `git stash {sub}`. The stash stack is shared by every worktree, so another "
                        "session can take or lose your entry. Make a WIP commit instead.")
        if verb == "merge" and "--abort" not in args:
            merged = True
        elif merged and verb in ("add", "commit"):
            return ("Blocked: `git merge` chained with `git " + verb + "`. A conflicted merge would commit its "
                    "conflict markers. Run the merge alone, check for conflicts, then add and commit.")
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
        msg = check((data.get("tool_input") or {}).get("command") or "") if data.get("tool_name") == "Bash" else None
    except Exception as e:  # noqa: BLE001 - fail open
        print(f"git_rules: hook error, allowed: {e}", file=sys.stderr)
        return 0
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
