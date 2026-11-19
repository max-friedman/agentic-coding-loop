"""Shared helpers for the project's PreToolUse hooks (see README.md): read the hook input, split a Bash
command into simple commands, find each one's command word, answer with the documented exit codes.

Not a shell parser: it understands what our commands look like (`&&`, `;`, `|`, newlines, subshells,
`$(…)`, `sh -c '…'`, env assignments, heredocs, wrappers like `timeout`/`xargs`). What happens when it
can't tokenize a command is each hook's choice: live_checkout fails closed, the others fail open.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys

# Exit codes (https://code.claude.com/docs/en/hooks): 2 blocks a PreToolUse call and shows stderr to
# Claude; anything else (1) is a non-blocking error the transcript shows.
BLOCK = 2

SHELLS = {"sh", "bash", "zsh", "dash"}
KEYWORDS = {"then", "do", "else", "elif", "if", "while", "until", "time", "!", "{", "}"}
# Wrappers whose own options come first, then the real command. Value: options that take an argument.
WRAPPERS = {
    "sudo": {"-u", "-g", "-C", "-D"},
    "env": {"-u", "-C", "-S"},
    "command": set(), "exec": set(), "builtin": set(), "nohup": set(), "caffeinate": {"-t", "-w"},
    "nice": {"-n"}, "time": set(),
    "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "gtimeout": {"-s", "-k", "--signal", "--kill-after"},
    "xargs": {"-n", "-I", "-P", "-L", "-d", "-E", "-s", "-a", "-J", "-R", "-S"},
    "watch": {"-n", "-d"},
}
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def read_input() -> dict:
    return json.load(sys.stdin)


def fail_open(name: str, err: BaseException) -> None:
    """A hook's own bug must never block work: say so on stderr and exit 1 (a non-blocking error the
    transcript shows as '<hook> hook error')."""
    print(f"{name}: hook error, letting the call through: {type(err).__name__}: {err}", file=sys.stderr)
    sys.exit(1)


def fail_closed(name: str, err: BaseException) -> None:
    """For the guards whose miss can't be undone (a shared device, a write to the live checkout): a hook
    bug blocks the call (exit 2) rather than letting it through (OWASP A10:2025, CWE-636: don't fail open)."""
    print(f"{name}: hook error, blocked for safety: {type(err).__name__}: {err}; fix .claude/hooks/{name}.py", file=sys.stderr)
    sys.exit(BLOCK)


def block(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(BLOCK)


def strip_heredocs(cmd: str) -> str:
    """Drop heredoc bodies (their lines are data, not commands); keep the line that opens them."""
    out, lines, i = [], cmd.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        delims = [m.group(2) for m in _HEREDOC.finditer(line) if not line[max(0, m.start() - 1):m.start()] == "<"]
        i += 1
        for d in delims:
            while i < len(lines) and lines[i].strip("\t ") != d:
                i += 1
            i += 1  # the delimiter line
    return "\n".join(out)


def tokens(cmd: str) -> list[str]:
    """Shell-ish tokens; separators and redirections come out as their own tokens. Raises ValueError on
    unbalanced quotes."""
    cmd = strip_heredocs(cmd).replace("`", " ; ")  # backticks: a command substitution starts a command
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|()<>\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def _is_punct(t: str) -> bool:
    return bool(t) and all(c in ";&|()<>\n" for c in t)


def segments(cmd: str) -> list[list[str]]:
    """Simple commands: lists of words, separators gone, redirections and their targets dropped, comments
    dropped."""
    out: list[list[str]] = []
    cur: list[str] = []
    toks = tokens(cmd)
    i = 0
    comment = False
    while i < len(toks):
        t = toks[i]
        if t == "\n":
            comment = False
        if comment:
            i += 1
            continue
        if _is_punct(t):
            if "<" in t or ">" in t:
                i += 2  # a redirection and its target
                continue
            if cur:
                out.append(cur)
            cur = []
        elif t in ("$", "{", "}"):
            if cur:
                out.append(cur)
            cur = []
        elif t.startswith("#") and not cur:
            comment = True
        elif t.startswith("#"):
            out.append(cur)
            cur = []
            comment = True
        else:
            cur.append(t)
        i += 1
    if cur:
        out.append(cur)
    return [s for s in out if s]


def split_command(words: list[str]) -> tuple[dict, str, list[str]]:
    """(env assignments, command word, its arguments) of one simple command, past keywords, VAR=val
    prefixes and wrappers (sudo, env, timeout, xargs…). ('', []) when there's no command."""
    env: dict = {}
    i = 0
    while i < len(words):
        w = words[i]
        if w in KEYWORDS:
            i += 1
            continue
        if _ASSIGN.match(w):
            k, _, v = w.partition("=")
            env[k] = v
            i += 1
            continue
        base = os.path.basename(w)
        if base in WRAPPERS:
            takes = WRAPPERS[base]
            i += 1
            while i < len(words) and (words[i].startswith("-") or _ASSIGN.match(words[i])):
                if _ASSIGN.match(words[i]):
                    k, _, v = words[i].partition("=")
                    env[k] = v
                elif words[i] in takes:
                    i += 1
                i += 1
            if base in ("timeout", "gtimeout") and i < len(words) and re.match(r"^[0-9.]+[smhd]?$", words[i]):
                i += 1  # the duration
            continue
        return env, w, words[i + 1:]
    return env, "", []


def shell_c_script(word: str, args: list[str]) -> str | None:
    """The script of `bash -c '<script>'` (also -lc, -ec…), else None."""
    if os.path.basename(word) not in SHELLS:
        return None
    for j, a in enumerate(args):
        if a.startswith("-") and not a.startswith("--") and "c" in a[1:]:
            return args[j + 1] if j + 1 < len(args) else None
        if not a.startswith("-"):
            return None
    return None


def commands(cmd: str, depth: int = 0):
    """Every simple command in cmd, (env, word, args), descending into `sh -c` scripts. A command whose
    word is a wrapper the caller treats as opaque is still yielded; the caller decides."""
    for seg in segments(cmd):
        env, word, args = split_command(seg)
        if not word:
            continue
        yield env, word, args
        inner = shell_c_script(word, args)
        if inner is not None and depth < 3:
            yield from commands(inner, depth + 1)


def resolve(path: str, cwd: str) -> str:
    return os.path.realpath(os.path.join(cwd, os.path.expanduser(os.path.expandvars(path))))


def within(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


_GIT_GLOBAL_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}


def git_subcommand(args: list[str]) -> list[str]:
    """`git <global options> <sub> <args>` → [sub, *args] (global options such as -C <dir> skipped); [] if none."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in _GIT_GLOBAL_WITH_ARG else 1
    return args[i:]


def gh_subcommand(args: list[str]) -> list[str]:
    """`gh [-R repo] <group> <cmd> <args>` → [group, cmd, *args]; [] if none."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in ("-R", "--repo") else 1
    return args[i:]
