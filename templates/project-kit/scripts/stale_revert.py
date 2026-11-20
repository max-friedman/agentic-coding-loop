#!/usr/bin/env python3
"""
The stale-merge guard: a branch whose stale or badly resolved merge silently undoes lines that main gained since it
forked is refused. (In the project behind LOOP.md §F, one stale merge quietly reverted the previous PR's lines.)

The rule: a PR is refused when, against current main, it *removes lines that main added since the PR branch forked*.
  fork   = the first parent of the branch's oldest own (non-merge) commit, so a wrong conflict resolution in a later
           "merge main" commit still counts (merge-base alone would hide it: it moves to main's tip at that merge).
  lost   = the lines added in fork..main to a file the PR also changes, that the PR's version of the file no longer has.
  Only significant lines count (not blank, not punctuation-only, 12+ characters after stripping), and a file is flagged
  only at 3 or more lost lines (LIMIT), so a one-line tweak of a neighbour never trips it.
On purpose: a line `Intentional revert: <what and why>` in the PR body or a commit message turns it off. A few git
diffs; any git error means "no finding" (fails open). scripts/prelanding.py runs it (`prelanding.stale_revert`).
"""
from __future__ import annotations

import re
import subprocess
from collections import Counter
from pathlib import Path

LIMIT = 3
MIN_LEN = 12
ON_PURPOSE = re.compile(r"^\s*Intentional revert:\s*\S", re.I | re.M)
IGNORED: tuple = ()  # paths whose lines move all the time by design (a status table, say): never flagged


def _git(cwd: Path, *args: str) -> str | None:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, errors="replace")
    return r.stdout if r.returncode == 0 else None


def significant(line: str) -> bool:
    s = line.strip()
    return len(s) >= MIN_LEN and bool(re.search(r"[A-Za-z0-9]{3}", s))


def fork_point(cwd: Path, head: str, main: str) -> str | None:
    own = (_git(cwd, "rev-list", "--no-merges", "--reverse", f"{main}..{head}") or "").split()
    if not own:
        return None
    fork = (_git(cwd, "rev-parse", f"{own[0]}^") or "").strip()
    return fork or None


def added_lines(cwd: Path, fork: str, main: str, path: str) -> Counter:
    out = _git(cwd, "diff", "-U0", "--no-color", f"{fork}..{main}", "--", path) or ""
    return Counter(l[1:].strip() for l in out.splitlines() if l.startswith("+") and not l.startswith("+++") and significant(l[1:]))


def lost_lines(cwd: Path, head: str, fork: str, main: str, files: list[str]) -> dict[str, list[str]]:
    both = set((_git(cwd, "diff", "--name-only", f"{fork}..{main}") or "").split())
    out: dict[str, list[str]] = {}
    for f in files:
        if f not in both or f in IGNORED:
            continue
        mine = _git(cwd, "show", f"{head}:{f}") or ""  # deleted by the PR: every line is lost
        have = Counter(l.strip() for l in mine.splitlines())
        gone = [l for l, n in added_lines(cwd, fork, main, f).items() if have[l] < n]
        if len(gone) >= LIMIT:
            out[f] = gone
    return out


def refusal(cwd: Path, head: str, files: list[str], body: str, main: str = "origin/main", label: str = "this branch") -> str:
    """"" or why `head` undoes lines main gained since the branch forked (and says so nowhere on purpose)."""
    fork = fork_point(cwd, head, main)
    if not fork:
        return ""
    msgs = _git(cwd, "log", "--format=%B", f"{main}..{head}") or ""
    if ON_PURPOSE.search(body or "") or ON_PURPOSE.search(msgs):
        return ""
    lost = lost_lines(cwd, head, fork, main, files)
    if not lost:
        return ""
    parts = []
    for f, lines in list(lost.items())[:3]:
        who = (_git(cwd, "log", "-1", "--format=%h %s", f"-S{lines[0]}", f"{fork}..{main}", "--", f) or "").strip()
        parts.append(f"{f}: {len(lines)} lines main added are gone (e.g. {lines[0][:60]!r}; added by {who or 'a PR merged since'})")
    return (f"{label} undoes lines that were merged to main since it forked: " + "; ".join(parts) +
            ". Probably a stale or badly resolved merge: merge origin/main again keeping both sides, push, and rerun. "
            "If removing them is the point, put a line `Intentional revert: <what and why>` in the PR body.")
