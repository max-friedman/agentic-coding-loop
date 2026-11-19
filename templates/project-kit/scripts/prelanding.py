#!/usr/bin/env python3
"""Run the fast checks on this branch merged with origin/main, and record the pass for its head commit.

    python3 scripts/prelanding.py            # the current branch
    python3 scripts/prelanding.py --status   # has HEAD a recorded pass?

The checks run in a scratch worktree of HEAD with origin/main merged in, so what passes is what main would get.
PRELANDING_CHECKS lists them, separated by ";" (or the "prelanding": {"checks": [...]} list in .loop/config.json).
With no checks configured it fails: a check that ran nothing is no verdict. A pass is recorded in
.loop/prelanding/<sha> of the main checkout; scripts/land.sh refuses a pull request whose head has none.
"""
from __future__ import annotations

import json
import os
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


def checks(root: str) -> list[str]:
    env = os.environ.get("PRELANDING_CHECKS")
    if env:
        return [c.strip() for c in env.split(";") if c.strip()]
    try:
        cfg = json.loads(Path(root, ".loop", "config.json").read_text())
    except (OSError, ValueError):
        cfg = {}
    return [c for c in (cfg.get("prelanding") or {}).get("checks") or [] if isinstance(c, str) and c.strip()]


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
