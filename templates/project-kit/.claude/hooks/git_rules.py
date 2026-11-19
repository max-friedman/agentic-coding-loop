#!/usr/bin/env python3
"""PreToolUse(Bash): git commands that have cost us work (CLAUDE.md worktree note; memory "Check merges before committing").

Blocks:
- A git stash that can take or lose someone else's entry. The stash stack is shared by the main checkout and every
  worktree, and other sessions push and pop it concurrently. Blocked: bare `git stash` (or `git stash -u` …),
  `git stash push` without `-m <tag>`, `pop`, `clear`, `save`, and a bare `apply` / `drop` / `branch <name>` (they
  take stash@{0}, which may be another session's). Allowed: `git stash push -u -m <tag>`, `list`, `show`,
  `apply <sha>`, `drop stash@{n}`, `create`, `store`.
- `git merge …` followed by `git add` / `git commit` in the same command: a conflicted merge gets its conflict markers
  committed (pushed 4 times). Run the merge alone, check for conflicts, then add and commit. `git merge --abort` and
  a commit that comes before the merge are fine.

Fails open on its own errors (a miss is recoverable: a popped stash is still a dangling commit, a bad commit can be
amended before it lands); the rules in CLAUDE.md and the memory still apply.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _shell  # noqa: E402

STASH_OK = {"list", "show", "create", "store"}
STASH_NEEDS_REF = {"apply": 1, "drop": 1, "branch": 2}  # positional args needed to name an entry (not stash@{0} by default)
STASH_NEVER = {
    "pop": "pops the top entry, which may be another session's, and drops it",
    "clear": "deletes every session's stash entries",
    "save": "is the old form; its entries have no tag you can find again",
}
HOW_TO_STASH = ("Prefer a temporary WIP commit. If you must stash: `git stash push -u -m \"<unique-tag>\"`, then "
                "`git stash list --format='%H %gs'` to capture your entry's sha, restore with `git stash apply <sha>` "
                "(not pop), and drop it with `git stash drop stash@{n}` after re-finding n by its tag.")


def _has_message(args: list[str]) -> bool:
    for a in args:
        if a in ("-m", "--message") or a.startswith("--message="):
            return True
        if a.startswith("-") and not a.startswith("--") and "m" in a[1:]:
            return True  # -um <tag>, -m<tag>
    return False


def check_stash(rest: list[str]) -> str | None:
    """Why `git stash <rest>` is blocked, or None."""
    if rest and not rest[0].startswith("-"):
        verb, args = rest[0], rest[1:]
    else:
        verb, args = "push", rest  # `git stash` / `git stash -u -m x` is `git stash push …`
    if verb in STASH_OK:
        return None
    if verb in STASH_NEVER:
        return f"`git stash {verb}` {STASH_NEVER[verb]}."
    if verb in STASH_NEEDS_REF:
        if len([a for a in args if not a.startswith("-")]) >= STASH_NEEDS_REF[verb]:
            return None
        return f"a `git stash {verb}` that names no entry acts on stash@{{0}}, which may be another session's."
    if verb == "push":
        if _has_message(args):
            return None
        return "a stash without `-m <tag>` can't be told apart from other sessions' entries."
    return None  # an unknown verb: git itself complains


def check(cmd: str) -> str | None:
    if "git" not in cmd or ("stash" not in cmd and "merge" not in cmd):
        return None
    merged = False
    for _env, word, args in _shell.commands(cmd):
        if os.path.basename(word) != "git":
            continue
        sub = _shell.git_subcommand(args)
        if not sub:
            continue
        if sub[0] == "stash":
            why = check_stash(sub[1:])
            if why:
                return (f"Blocked by .claude/hooks/git_rules.py: {why} The stash stack is shared by every worktree and "
                        f"session (CLAUDE.md worktree note).\n{HOW_TO_STASH}")
        elif sub[0] == "merge" and not any(a in ("--abort", "--quit") for a in sub[1:]):
            merged = True
        elif sub[0] in ("add", "commit") and merged:
            return (f"Blocked by .claude/hooks/git_rules.py: `git merge` then `git {sub[0]}` in one command commits "
                    "whatever the merge left, conflict markers included (pushed 4 times). Run the merge on its own, "
                    "check `git diff --name-only --diff-filter=U` (and grep for '<<<<<<<'), resolve, then add and "
                    "commit in a separate command.")
    return None


def main() -> None:
    try:
        data = _shell.read_input()
        msg = check((data.get("tool_input") or {}).get("command") or "") if data.get("tool_name") == "Bash" else None
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("git_rules", e)
        return
    if msg:
        _shell.block(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
