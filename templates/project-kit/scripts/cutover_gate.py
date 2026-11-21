#!/usr/bin/env python3
"""The cutover readiness gate: a cutover switches features on for users, so the build they run must contain them, the
release pipeline must be able to ship the next one, and the switched code must have passed the whole suite recently.

Why: a cutover once switched features on while the release pipeline sat paused for days and users still ran an old
build, so nothing changed for them; the config said "on" and nobody checked the shipped build. Its whole-suite pass
had to be run by hand at the last minute.

    python3 scripts/cutover_gate.py            # this checkout's HEAD against origin/main
    python3 scripts/cutover_gate.py --base X   # against another base

A cutover is a PR whose body matches `cutover.when_body` (default `^\W*Cutover:`, so on by default) or that changes `cutover.when_paths`
(your feature-switch config, say). For one, three checks, each refusing with what to do:

1. the release pipeline isn't paused (`release.paused_file`): land the fix, let it pass its checks, then resume it
   (`release.resume_command`) and wait for its build;
2. a cutover that changes no shipped code (a config switch) needs the build users run (`release.published_file`) to
   contain every shipped change (`release.shipped_paths`, not tests) up to the cutover's base, i.e. where the branch
   meets main: else the switch turns on code users don't have. A cutover that changes shipped code ships in the
   pipeline's next build after it lands, which check 1 keeps possible;
3. a whole-suite pass within `cutover.pass_max_age_hours` (24) on a commit that contains the cutover's base, read from
   `cutover.passes_file`: JSON lines `{"at": epoch, "commit": sha, "full": true, "failed": n, "failures": [names]}`
   that your suite runner appends. A run passes with 0 failures, or when every named failure is known red
   (`cutover.known_red_file`: `{"scenarios": [...]}`). `cutover.suite_command` is quoted as how to run one.
   With no passes file set, a cutover is refused: no proof is no verdict.

The release knobs unset: checks 1 and 2 say so and pass. prelanding.py runs this after its checks (exit 14; a branch
that isn't a cutover passes at once). Exit 0 ready (or not a cutover), 1 refused.

The ordered cutover checklist: the pipeline running -> the build users run has main's shipped changes -> a whole-suite
pass in 24 h on the base -> the review line (`prelanding.review_lines`) -> land. After it lands, check that the build
users actually run is the published one.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Optional

REPO = Path(__file__).resolve().parent.parent
RELEASE = {"paused_file": "", "published_file": "", "shipped_paths": [],
           "not_shipped_pattern": r"(^|/)tests?/|(^|/)test_[^/]*$", "resume_command": ""}  # hooks/_loop.py's "release"
CUTOVER = {"when_body": r"^\W*Cutover:", "when_paths": [], "passes_file": "", "pass_max_age_hours": 24,
           "known_red_file": "", "suite_command": ""}  # as hooks/_loop.py's "cutover"


def knobs(root: Path) -> tuple[dict, dict]:
    try:
        cfg = json.loads((root / ".loop" / "config.json").read_text())
    except (OSError, ValueError):
        cfg = {}
    own = lambda k: cfg.get(k) if isinstance(cfg.get(k), dict) else {}  # noqa: E731
    return {**RELEASE, **own("release")}, {**CUTOVER, **own("cutover")}


def read_json(p: Path) -> Optional[dict]:
    try:
        d = json.loads(p.read_text())
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) else None


def read_jsonl(p: Path) -> list[dict]:
    out = []
    try:
        lines = p.read_text().splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict):
            out.append(r)
    return out


def git(repo: Path, *a: str) -> Optional[str]:
    try:
        r = subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def contains(repo: Path, commit: str, base: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", base, commit], cwd=repo, capture_output=True).returncode == 0


def ships(f: str, rel: dict) -> bool:
    paths = rel.get("shipped_paths") or []
    return (not paths or f.startswith(tuple(paths))) and not re.search(rel.get("not_shipped_pattern") or r"$^", f)


def missing_shipped(repo: Path, published: str, base: str, rel: dict) -> Optional[list[str]]:
    """First-parent commits up to `base` after the published build's commit (its merge base with base) that changed a
    shipped file, oldest first, as "sha subject". None when git can't say."""
    mb = git(repo, "merge-base", published, base)
    if not mb:
        return None
    paths = rel.get("shipped_paths") or []
    out = git(repo, "log", "--first-parent", "-m", "--reverse", "--name-only", "--format=@%h %s", f"{mb}..{base}",
              *(["--", *paths] if paths else []))
    if out is None:
        return None
    got, cur, hit = [], "", False
    for line in out.splitlines() + ["@"]:
        if line.startswith("@"):
            if cur and hit and cur not in got:
                got.append(cur)
            cur, hit = line[1:], False
        elif line.strip() and ships(line.strip(), rel):
            hit = True
    return got


def is_cutover(files: list[str], body: str, cut: dict) -> list[str]:
    why = []
    if cut.get("when_body") and re.search(cut["when_body"], body or "", re.I | re.M):
        why.append("the body declares a cutover")
    hit = [f for f in files if cut.get("when_paths") and f.startswith(tuple(cut["when_paths"]))]
    if hit:
        why.append(f"it changes {', '.join(hit[:3])}")
    return why


def when(t) -> str:
    try:
        return time.strftime("%m-%d %H:%M", time.localtime(float(t)))
    except (TypeError, ValueError):
        return "?"


def suite_pass(base: str, now: float, runs: list[dict], red: set[str], max_age_s: float,
               has: Callable[[str, str], bool]) -> tuple[bool, str]:
    """(passed, what was found): the newest whole-suite run within max_age_s on a commit containing base that passed."""
    seen = []
    bad = []
    for i, r in enumerate(runs, 1):
        try:
            float(r.get("at") or 0), int(r.get("failed") or 0)
        except (TypeError, ValueError):
            bad.append(i)
    if bad:
        return False, (f"the passes file has malformed run(s) at line(s) {', '.join(map(str, bad[:5]))} (`at` must be "
                       "epoch seconds, `failed` a number): fix the runner that writes it, then run this again")
    for r in sorted(runs, key=lambda r: float(r.get("at") or 0), reverse=True):
        if not r.get("full"):
            continue
        at = float(r.get("at") or 0)
        if now - at > max_age_s:
            break
        sha = str(r.get("commit") or "")
        if not sha or not has(sha, base):
            seen.append(f"{when(at)} at {sha[:9] or '?'} (doesn't contain the base {base[:9]})")
            continue
        failed = int(r.get("failed") or 0)
        if failed == 0:
            return True, f"whole-suite pass {when(at)} at {sha[:9]}"
        names = r.get("failures")
        if isinstance(names, list) and len(names) >= failed and not set(map(str, names)) - red:
            return True, f"whole-suite run {when(at)} at {sha[:9]}: its {failed} failure(s) are all known red"
        new = sorted(set(map(str, names)) - red) if isinstance(names, list) else None
        seen.append(f"{when(at)} at {sha[:9]}: {failed} failed" + (f", not known red: {', '.join(new[:5])}" if new else
                                                                   ", unnamed" if new is None else ""))
    hours = int(max_age_s // 3600)
    return False, (f"no whole-suite run in {hours} h" if not seen else f"no passing one in {hours} h: " + "; ".join(seen[:3]))


def refusal(repo: Path, files: list[str], body: str, base: str, head: str = "HEAD", now: Optional[float] = None,
            say: Callable[[str], None] = print, has: Optional[Callable[[str, str], bool]] = None,
            root: Optional[Path] = None) -> str:
    """Why this cutover isn't ready, or "" (also "" when it isn't a cutover). Says the pipeline's state for one.
    `repo` is where git runs (prelanding's scratch worktree); `root` the checkout whose .loop/ holds the knobs and
    the pipeline's files (default: repo)."""
    root = root or repo
    rel, cut = knobs(root)
    why = is_cutover(files, body, cut)
    if not why:
        return ""
    now = time.time() if now is None else now
    base_sha = git(repo, "merge-base", head, base) or git(repo, "rev-parse", base) or base
    paused = read_json(root / rel["paused_file"]) if rel.get("paused_file") else None
    pub = (read_json(root / rel["published_file"]) if rel.get("published_file") else None) or {}
    say(f"cutover ({'; '.join(why)}): release pipeline "
        + ("not configured (release.paused_file / published_file)" if not rel.get("paused_file") and not rel.get("published_file")
           else (f"PAUSED since {when(paused.get('at'))} ({paused.get('why') or 'no cause recorded'})" if paused else "running")
           + (f"; users run {pub.get('version') or str(pub.get('commit') or '?')[:9]}" if pub else "; nothing published")))
    if paused:
        resume = f"`{rel['resume_command']}`" if rel.get("resume_command") else "resume it"
        return (f"this cutover would switch features on while the release pipeline is paused "
                f"({paused.get('why') or 'no cause recorded'}, since {when(paused.get('at'))}): no build with them can "
                f"reach users. Land the fix, let it pass its checks, then {resume} and wait for its build.")
    if rel.get("published_file") and not any(ships(f, rel) for f in files):
        commit = str(pub.get("commit") or "")
        lacks = missing_shipped(repo, commit, base_sha, rel) if commit else None
        if lacks is None:
            return (f"this cutover changes no shipped code, so users must already run a build with the features it "
                    f"switches on, but the published build can't be read ({rel['published_file']}, or its commit isn't "
                    "in this checkout: git fetch).")
        if lacks:
            return (f"this cutover changes no shipped code, but the build users run ({pub.get('version') or commit[:9]}) "
                    f"lacks {len(lacks)} shipped change(s) on main: {'; '.join(lacks[:4])}{' …' if len(lacks) > 4 else ''}. "
                    "The switch would turn on code users don't have: wait for the pipeline's next build, then run this again.")
    how = f" Run one: `{cut['suite_command']}`." if cut.get("suite_command") else ""
    if not cut.get("passes_file"):
        return ("a cutover needs a recent whole-suite pass on its base, and `cutover.passes_file` isn't set, so there is "
                "no record to read: have your suite runner append its runs there (see scripts/cutover_gate.py)." + how)
    red = {str(s) for s in ((read_json(root / cut["known_red_file"]) or {}).get("scenarios") or [])} \
        if cut.get("known_red_file") else set()
    ok, found = suite_pass(base_sha, now, read_jsonl(root / cut["passes_file"]), red,
                           float(cut["pass_max_age_hours"]) * 3600, has or (lambda c, b: contains(repo, c, b)))
    if not ok:
        return (f"a cutover needs a whole-suite pass within {cut['pass_max_age_hours']} h on a commit that contains its "
                f"base ({base_sha[:9]}, where the branch meets main): {found}.{how}")
    say(f"cutover: {found}")
    return ""


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--body", type=Path, help="the PR body (default: the PR of this branch, via gh)")
    a = ap.parse_args(argv)
    body = a.body.read_text() if a.body else (subprocess.run(["gh", "pr", "view", "--json", "body", "-q", ".body"],
                                                             cwd=REPO, capture_output=True, text=True).stdout or "")
    files = (git(REPO, "diff", "--name-only", f"{a.base}...HEAD") or "").split()
    why = refusal(REPO, files, body, a.base)
    if why:
        print(f"cutover_gate: {why}")
        return 1
    print("cutover_gate: ready (or not a cutover)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
