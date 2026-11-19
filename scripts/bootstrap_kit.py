#!/usr/bin/env python3
"""Install the project kit into a repository: the hooks and their settings, a CLAUDE.md skeleton, process docs, the
prelanding and landing scripts, the watchdog and the state file.

    python3 scripts/bootstrap_kit.py <repo>             # install; files that already exist are left alone
    python3 scripts/bootstrap_kit.py <repo> --test      # install, then run every hook test there
    python3 scripts/bootstrap_kit.py <repo> --no-state  # skip docs/plans/LOOP_STATE.md (loop-init writes it)
    python3 scripts/bootstrap_kit.py <repo> --force     # overwrite existing files

What it copies:
  templates/project-kit/**          -> <repo>/** (CLAUDE.md, .claude/, docs/process/, scripts/)
  hooks/admission_gate.py, hooks/waiter_guard.py -> <repo>/.claude/hooks/
  hooks/watchdog.py                 -> <repo>/scripts/watchdog.py
  templates/LOOP_STATE.template.md  -> <repo>/docs/plans/LOOP_STATE.md
and adds .loop/ (the lane ledger, prelanding passes, the watchdog's stamp) to <repo>/.gitignore.

Most of templates/project-kit/ is harvested from the project the loop runs in, so it is what that project uses today.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ACL = Path(__file__).resolve().parent.parent
KIT = ACL / "templates" / "project-kit"
EXTRA = {
    "hooks/admission_gate.py": ".claude/hooks/admission_gate.py",
    "hooks/waiter_guard.py": ".claude/hooks/waiter_guard.py",
    "hooks/watchdog.py": "scripts/watchdog.py",
}
STATE = ("templates/LOOP_STATE.template.md", "docs/plans/LOOP_STATE.md")


def plan(no_state: bool) -> list[tuple[Path, str]]:
    files = [(p, p.relative_to(KIT).as_posix()) for p in sorted(KIT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    files += [(ACL / src, dest) for src, dest in EXTRA.items()]
    if not no_state:
        files.append((ACL / STATE[0], STATE[1]))
    return files


def install(repo: Path, force: bool = False, no_state: bool = False) -> tuple[list[str], list[str]]:
    written, kept = [], []
    for src, rel in plan(no_state):
        dest = repo / rel
        if dest.exists() and not force:
            kept.append(rel)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        written.append(rel)
    ignore = repo / ".gitignore"
    lines = ignore.read_text().splitlines() if ignore.exists() else []
    if ".loop/" not in lines:
        ignore.write_text("\n".join([*lines, ".loop/"]) + "\n")
        written.append(".gitignore")
    return written, kept


def run_tests(repo: Path) -> list[str]:
    failed = []
    for t in sorted((repo / ".claude" / "hooks").glob("test_*.py")):
        r = subprocess.run([sys.executable, t.name], cwd=t.parent, capture_output=True, text=True, timeout=300)
        print(f"  {'ok  ' if r.returncode == 0 else 'FAIL'}  {t.name}")
        if r.returncode:
            failed.append(t.name)
            print("        " + "\n        ".join((r.stdout + r.stderr).strip().splitlines()[-5:]))
    return failed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo", type=Path)
    ap.add_argument("--force", action="store_true", help="overwrite files that already exist")
    ap.add_argument("--no-state", action="store_true", help="don't install docs/plans/LOOP_STATE.md")
    ap.add_argument("--test", action="store_true", help="run the hook tests in the repository afterwards")
    a = ap.parse_args(argv)
    repo = a.repo.expanduser().resolve()
    if not (repo / ".git").exists():
        print(f"bootstrap_kit: {repo} is not a git repository (git init it first)", file=sys.stderr)
        return 2
    written, kept = install(repo, a.force, a.no_state)
    print(f"bootstrap_kit: {len(written)} file(s) written, {len(kept)} left as they were")
    for rel in kept:
        print(f"  kept  {rel}")
    print("Next: fill the <placeholders> in CLAUDE.md and docs/process/, set LOOP_LIVE_CHECKOUT in .claude/settings.json,"
          " and schedule scripts/watchdog.py every 15 minutes.")
    if a.test:
        print("hook tests:")
        failed = run_tests(repo)
        if failed:
            print(f"bootstrap_kit: {len(failed)} hook test(s) failed")
            return 1
        print("bootstrap_kit: every hook test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
