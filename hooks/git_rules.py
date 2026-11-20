#!/usr/bin/env python3
"""PreToolUse(Bash): git commands that have cost work when several sessions share one repository (CLAUDE.md, Hard rules).

Blocks:
- A git stash that can take or lose someone else's entry. The stash stack is shared by the main checkout and every
  worktree, and other sessions push and pop it concurrently. Blocked: bare `git stash` (or `git stash -u` …),
  `git stash push` without `-m <tag>`, `pop`, `clear`, `save`, and a bare `apply` / `drop` / `branch <name>` (they
  take stash@{0}, which may be another session's). Allowed: `git stash push -u -m <tag>`, `list`, `show`,
  `apply <sha>`, `drop stash@{n}`, `create`, `store`.
- `git merge …` followed by `git add` / `git commit` in the same command: a conflicted merge gets its conflict markers
  committed (pushed 4 times). Run the merge alone, check for conflicts, then add and commit. `git merge --abort` and
  a commit that comes before the merge are fine.
- Skipping a gate ("never skip a gate"; `git_rules.block_no_verify`): `git commit --no-verify` / `-n` (also inside a
  short-flag cluster such as `-anm`) and `git push --no-verify` (push's `-n` is --dry-run and passes). And an override
  flag of a landing script (`git_rules.coordinator_only_flags` on `git_rules.landers`, e.g. `land.sh --no-prelanding`)
  from anyone but the registered coordinator: a hook input with an `agent_id` (a helper) or another session's id.
  The landing script should check and log its overrides too; this hook is the first line.
- A helper's `git worktree add <path>` outside `git_rules.worktree_dirs` (default `.claude/worktrees` and
  `../<repo>-worktrees`) and $TMPDIR (`git_rules.block_stray_worktree`). Helper worktrees elsewhere were never swept:
  18 of them (~16 GB) sat for days after their PRs merged. From the coordinator or another session it only warns.

Warns (doesn't block): that worktree add from a non-helper, and a command prefixed with a gate-changing environment
variable (`git_rules.gate_env`, or any name with SKIP / NO_VERIFY / NO_GATE / DISABLE_GATE / BYPASS in it) or
`git -c core.hooksPath=…`. A warning goes to the session (additionalContext) and the user (systemMessage); the call runs.

Fails open on its own errors (a miss is recoverable: a popped stash is still a dangling commit, a bad commit can be
amended before it lands); the rule in CLAUDE.md still applies.
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _loop  # noqa: E402
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


GATE_ENV_RE = re.compile(r"(^|_)(SKIP|NO_VERIFY|NO_GATE|DISABLE_GATES?|BYPASS)(_|$)")
COMMIT_SHORT_WITH_ARG = set("mFCctS")  # commit's short options whose value follows (the rest of the cluster or the next word)
COMMIT_LONG_WITH_ARG = {"--message", "--file", "--author", "--date", "--reuse-message", "--reedit-message", "--fixup",
                        "--squash", "--template", "--cleanup", "--trailer", "--pathspec-from-file"}


def _cfg() -> dict:
    try:
        return _loop.config()["git_rules"]
    except Exception:  # noqa: BLE001 - an unreadable config: the defaults
        return dict(_loop.DEFAULTS["git_rules"])


def commit_no_verify(rest: list[str]) -> bool:
    skip = False
    for a in rest:
        if skip:
            skip = False
            continue
        if a == "--":
            return False
        if a == "--no-verify":
            return True
        if a in COMMIT_LONG_WITH_ARG:
            skip = True
        elif a.startswith("-") and not a.startswith("--") and len(a) > 1:
            for j, ch in enumerate(a[1:], 1):
                if ch == "n":
                    return True
                if ch in COMMIT_SHORT_WITH_ARG:
                    skip = j == len(a) - 1  # `-m x`: the value is the next word; `-mx`: it was the rest of this one
                    break
    return False


def _is_coordinator(data: dict) -> bool:
    try:
        import coordinator_session
        return coordinator_session.is_coordinator(data)
    except Exception:  # noqa: BLE001 - no marker module: nobody is the coordinator
        return False


def skip_gate(cmd: str, data: dict, cfg: dict | None = None) -> str | None:
    """Why this command skips a gate, or None."""
    cfg = cfg or _cfg()
    flags = list(cfg.get("coordinator_only_flags") or [])
    if "no-verify" not in cmd and "commit" not in cmd and not any(f in cmd for f in flags):
        return None
    landers = tuple(cfg.get("landers") or ())
    for _env, word, args in _shell.commands(cmd):
        if os.path.basename(word) == "git" and cfg.get("block_no_verify", True):
            sub = _shell.git_subcommand(args)
            if sub[:1] == ["commit"] and commit_no_verify(sub[1:]):
                return ("Blocked by .claude/hooks/git_rules.py: `git commit --no-verify` (or `-n`) skips the pre-commit "
                        "gate. Never skip a gate: fix what it found, or fix the gate itself in its own pull request.")
            if sub[:1] == ["push"] and "--no-verify" in sub[1:]:
                return ("Blocked by .claude/hooks/git_rules.py: `git push --no-verify` skips the push hooks. Never skip a "
                        "gate: fix what it found, or fix the gate itself in its own pull request.")
        prog = next((a for a in [word] + args if os.path.basename(a) in landers), "")
        used = [a for a in args if any(a == f or a.startswith(f + "=") for f in flags)]
        if prog and used and (data.get("agent_id") or not _is_coordinator(data)):
            return (f"Blocked by .claude/hooks/git_rules.py: `{used[0]}` on {os.path.basename(prog)} is the coordinator's "
                    "override only; a helper or another session can't skip the landing gate. Run "
                    "`python3 scripts/prelanding.py` on the final head and land after it passes; if the gate is wrong, "
                    "hand back with its output.")
    return None


def env_warning(cmd: str, cfg: dict | None = None) -> str | None:
    cfg = cfg or _cfg()
    named = set(cfg.get("gate_env") or ())
    hits = []
    for env, word, args in _shell.commands(cmd):
        hits += [k for k in env if k in named or GATE_ENV_RE.search(k)]
        if os.path.basename(word) == "git":
            hits += [args[i + 1] for i, a in enumerate(args[:-1])
                     if a == "-c" and args[i + 1].lower().startswith("core.hookspath")]
    if not hits:
        return None
    return (f"Warning from .claude/hooks/git_rules.py: {', '.join(sorted(set(hits)))} on this command changes or "
            "disables a gate. Never skip, stub or loosen a gate (docs/process/helper-rules.md); if it's a test's own "
            "setting, set it in the test, not on the command line.")


_WT_ADD_WITH_ARG = {"-b", "-B", "--reason"}


def managed_roots(cfg: dict | None = None, project: str | None = None) -> list[str]:
    """The configured worktree dirs (`git_rules.worktree_dirs`), resolved against the project."""
    cfg = cfg or _cfg()
    proj = os.path.realpath(project or str(_loop.project_dir()))
    return [os.path.realpath(_shell.resolve(os.path.expanduser(d.replace("{repo}", os.path.basename(proj))), proj))
            for d in cfg.get("worktree_dirs") or ()]


def worktree_roots(cfg: dict | None = None, project: str | None = None) -> list[str]:
    """Where a worktree may go: the managed dirs, plus temp dirs for throwaways."""
    tmp = [os.getenv("TMPDIR") or "/tmp", "/tmp", "/private/tmp", "/var/folders", "/private/var/folders"]
    return managed_roots(cfg, project) + [os.path.realpath(r) for r in tmp if r]


def worktree_warning(cmd: str, cwd: str = "", cfg: dict | None = None, project: str | None = None) -> str | None:
    """A `git worktree add` whose path is outside the managed dirs: the warning (a helper's call blocks on it), else None."""
    if "worktree" not in cmd or "git" not in cmd:
        return None
    cfg = cfg or _cfg()
    if not cfg.get("worktree_dirs"):
        return None
    for _env, word, args in _shell.commands(cmd):
        if os.path.basename(word) != "git":
            continue
        here, i = cwd or os.getcwd(), 0
        while i < len(args) and args[i].startswith("-"):  # git's global options: -C <dir> moves the base
            if args[i] == "-C" and i + 1 < len(args):
                here = _shell.resolve(args[i + 1], here)
            i += 2 if args[i] in _shell._GIT_GLOBAL_WITH_ARG else 1
        sub = _shell.git_subcommand(args)
        if sub[:2] != ["worktree", "add"]:
            continue
        rest, i, path = sub[2:], 0, None
        while i < len(rest):
            a = rest[i]
            if a in _WT_ADD_WITH_ARG:
                i += 2
                continue
            if a.startswith("-"):
                i += 1
                continue
            path = a
            break
        if not path:
            continue
        full = os.path.realpath(_shell.resolve(path, here))
        if any(_shell.within(full, r) for r in worktree_roots(cfg, project)) or "/.claude/worktrees/" in full + "/":
            continue
        dirs = ", ".join(cfg.get("worktree_dirs") or ())
        return (f"Warning from .claude/hooks/git_rules.py: this worktree goes to {full}, outside the managed "
                f"worktree dirs ({dirs}; git_rules.worktree_dirs). Put worktrees there and remove yours once the PR is "
                "queued: worktrees elsewhere are easy to forget, and forgotten ones fill the disk.")
    return None


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
                        f"session (CLAUDE.md, Hard rules).\n{HOW_TO_STASH}")
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
        cmd = (data.get("tool_input") or {}).get("command") or "" if data.get("tool_name") == "Bash" else ""
        cfg = _cfg()
        msg = (check(cmd) or skip_gate(cmd, data, cfg)) if cmd else None
        wt = worktree_warning(cmd, str(data.get("cwd") or ""), cfg) if cmd and not msg else None
        if wt and data.get("agent_id") and cfg.get("block_stray_worktree", True):
            msg, wt = wt.replace("Warning from", "Blocked by", 1) + " A helper's worktree goes there or nowhere.", None
        warn = " ".join(w for w in (wt, env_warning(cmd, cfg) if cmd and not msg else None) if w) or None
    except Exception as e:  # noqa: BLE001 - fail-open
        _shell.fail_open("git_rules", e)
        return
    if msg:
        _shell.block(msg)
    if warn:
        print(json.dumps({"systemMessage": warn,
                          "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": warn}}))
    sys.exit(0)


if __name__ == "__main__":
    main()
