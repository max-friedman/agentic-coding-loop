#!/usr/bin/env python3
"""Run the fast checks on this branch merged with origin/main, and record the pass for its head commit.

    python3 scripts/prelanding.py            # the current branch
    python3 scripts/prelanding.py --status   # has HEAD a recorded pass?

The checks run in a scratch worktree of HEAD with origin/main merged in, so what passes is what main would get.
PRELANDING_CHECKS lists them, separated by ";" (or the "prelanding": {"checks": [...]} list in .loop/config.json).
With no checks configured it fails: a check that ran nothing is no verdict. A pass is recorded in
.loop/prelanding/<sha> of the main checkout; scripts/land.sh refuses a pull request whose head has none.

Two guards run before the checks (knobs under "prelanding" in .loop/config.json):
- A gate change is reviewed on its own. A branch that changes a gate (`gate_paths`: files that decide what runs, what
  is skipped or what passes) together with product code (`code_paths`; empty: the rule is off) is refused (exit 11)
  unless the PR body has `Gate change: reviewed by <reviewer>`, naming someone independent: a fresh reviewer agent or
  the owner, never the author or the coordinator (`not_independent`). Otherwise the check and the code it checks are
  changed and reviewed together. Split the gate change into its own PR when you can.
- The stale-merge guard (`stale_revert`, scripts/stale_revert.py): a branch that undoes lines main gained since it
  forked is refused (exit 12) unless the body or a commit says `Intentional revert: <what and why>`.
The PR body comes from `gh pr view` for the current branch (PRELANDING_BODY overrides it; no PR: an empty body).

Exit: 0 passed · 1 checks failed or conflicts · 11 gate change without an independent review · 12 stale merge
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def git(*args: str, cwd: str | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def record_dir() -> Path:
    common = Path(git("rev-parse", "--git-common-dir")).resolve()
    return common.parent / ".loop" / "prelanding"


DEFAULTS = {"gate_paths": ["scripts/prelanding.py", "scripts/land.sh", ".claude/hooks/", ".claude/settings.json",
                           ".githooks/", ".github/workflows/"],
            "code_paths": [], "not_independent": ["coordinator", "author", "self", "me", "myself"],
            "stale_revert": True}  # as hooks/_loop.py's "prelanding"
GATE_CHANGE_LINE = re.compile(r"^\W*Gate change:\s*reviewed by\s+(.+?)\s*$", re.I | re.M)


def knobs(root: str) -> dict:
    try:
        cfg = json.loads(Path(root, ".loop", "config.json").read_text())
    except (OSError, ValueError):
        cfg = {}
    own = cfg.get("prelanding") if isinstance(cfg.get("prelanding"), dict) else {}
    return {**DEFAULTS, **own}


def checks(root: str) -> list[str]:
    env = os.environ.get("PRELANDING_CHECKS")
    if env:
        return [c.strip() for c in env.split(";") if c.strip()]
    return [c for c in knobs(root).get("checks") or [] if isinstance(c, str) and c.strip()]


def pr_body() -> str:
    if "PRELANDING_BODY" in os.environ:
        return os.environ["PRELANDING_BODY"]
    r = subprocess.run(["gh", "pr", "view", "--json", "body", "-q", ".body"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def gate_change_refusal(files: list[str], body: str, cfg: dict) -> str:
    """Why a gate change that comes with product code can't land, or ""."""
    gates = [f for f in files if f.startswith(tuple(cfg["gate_paths"])) or re.match(r"^scripts/[^/]*_gate\.py$", f)]
    code = [f for f in files if cfg["code_paths"] and f.startswith(tuple(cfg["code_paths"]))]
    if not gates or not code:
        return ""
    m = GATE_CHANGE_LINE.search(body or "")
    who = m.group(1).strip() if m else ""
    bad = {w.lower() for w in cfg["not_independent"]}
    if who and not ({w.strip(".,;()").lower() for w in who.split()} & bad):
        return ""
    said = f" (it names `{who}`, which isn't independent)" if who else ""
    return (f"this branch changes a gate ({', '.join(gates[:3])}{'…' if len(gates) > 3 else ''}) together with code "
            f"({', '.join(code[:3])}{'…' if len(code) > 3 else ''}){said}. A gate change is reviewed on its own: split "
            "it into its own PR (best), or have a fresh reviewer agent or the owner read the gate diff and add "
            "`Gate change: reviewed by <reviewer>` to the PR body (never the author or the coordinator).")


def main() -> int:
    head = git("rev-parse", "HEAD")
    rec = record_dir() / head
    if "--status" in sys.argv:
        print(f"prelanding: {head[:9]} {'passed' if rec.exists() else 'has no recorded pass'}")
        return 0 if rec.exists() else 1
    subprocess.run(["git", "fetch", "-q", "origin"], check=False)
    wt = tempfile.mkdtemp(prefix="prelanding-")
    git("worktree", "add", "-q", "--detach", wt, head)
    try:
        merge = subprocess.run(["git", "merge", "-q", "--no-edit", "origin/main"], cwd=wt, capture_output=True, text=True)
        if merge.returncode:
            print("prelanding: the branch conflicts with origin/main; merge main in and rerun")
            return 1
        cfg = knobs(wt)
        changed = git("diff", "--name-only", "origin/main...HEAD", cwd=wt).split()
        body = pr_body()
        why = gate_change_refusal(changed, body, cfg)
        if why:
            print(f"prelanding: {why}")
            return 11
        if cfg.get("stale_revert", True):
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            try:
                import stale_revert
            except ImportError:
                stale_revert = None
            why = stale_revert.refusal(Path(wt), head, changed, body) if stale_revert else ""
            if why:
                print(f"prelanding: {why}")
                return 12
        cmds = checks(wt)
        if not cmds:
            print('prelanding: no checks configured, so nothing would be verified. Set PRELANDING_CHECKS or '
                  '"prelanding": {"checks": ["<your test command>"]} in .loop/config.json')
            return 1
        failed = []
        for cmd in cmds:
            print(f"== {cmd}", flush=True)
            if subprocess.run(cmd, shell=True, cwd=wt).returncode:
                failed.append(cmd)
        if failed:
            print("prelanding: FAILED: " + "; ".join(failed))
            return 1
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", wt], capture_output=True)
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text(time.strftime("%Y-%m-%dT%H:%M:%S") + "\n")
    print(f"prelanding: passed, recorded for {head[:9]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
