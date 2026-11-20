#!/usr/bin/env python3
"""Install the project kit into a repository: the hooks and their settings, a CLAUDE.md skeleton, process docs, the
prelanding and landing scripts, the watchdog, the knobs file and the state file.

    python3 scripts/bootstrap_kit.py <repo> --dry-run   # print what would change; write nothing
    python3 scripts/bootstrap_kit.py <repo>             # install; files that already exist are left alone
    python3 scripts/bootstrap_kit.py <repo> --test      # install, then run the hook tests (from this repo's hooks/)
    python3 scripts/bootstrap_kit.py <repo> --no-state  # skip docs/plans/LOOP_STATE.md (loop-init writes it)
    python3 scripts/bootstrap_kit.py <repo> --force     # overwrite existing hooks, scripts and docs (never CLAUDE.md)

Safe on a real repository:
  .claude/settings.json   merged, never replaced: missing env keys, matchers and hook commands are added; nothing
                          existing is dropped or reordered; the old file is saved as settings.json.bak-<time>. A file
                          it can't merge safely (not JSON, or an unexpected shape) stops the install, untouched.
  CLAUDE.md               never overwritten. If it exists the kit's skeleton goes to CLAUDE.loop.md; with --force it is
                          appended to CLAUDE.md as a marked section (replaced in place on the next --force).
  test_*.py               not copied: --test runs them from this repo's hooks/ against the installed hooks' behaviour.
  opinionated hooks       off until .loop/config.json turns them on (gh_rules.block_pr_merge,
                          coordinator.require_checks); admission_gate stays on (hooks/README.md).

What it copies:
  hooks/*.py (every hook and its helpers, not the tests) -> <repo>/.claude/hooks/   (hooks/ is the only copy of each hook)
  hooks/watchdog.py                 -> <repo>/scripts/watchdog.py (not a hook: the OS scheduler runs it)
  templates/project-kit/**          -> <repo>/** (CLAUDE.md, .claude/settings.json, docs/process/, scripts/; not its tests)
  templates/LOOP_STATE.template.md  -> <repo>/docs/plans/LOOP_STATE.md
writes <repo>/.loop/config.json with every knob at its default (hooks/README.md documents them), and adds .loop/ (the
knobs, the lane ledger, prelanding passes, the watchdog's stamp) to <repo>/.gitignore.

The hooks are generic versions of the ones a private project runs; the scripts are a starter version of its landing
pattern (README.md says which parts the kit ships and which it only describes).
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
import subprocess
import sys
from pathlib import Path

ACL = Path(__file__).resolve().parent.parent
KIT = ACL / "templates" / "project-kit"
HOOKS = ACL / "hooks"
NOT_HOOKS = {"watchdog.py": "scripts/watchdog.py"}
STATE = ("templates/LOOP_STATE.template.md", "docs/plans/LOOP_STATE.md")


SETTINGS = ".claude/settings.json"
MARK_BEGIN = "<!-- agentic-coding-loop:begin -->"
MARK_END = "<!-- agentic-coding-loop:end -->"


class Refuse(Exception):
    """The install can't proceed without risking the project's own files."""


def plan(no_state: bool) -> list[tuple[Path, str]]:
    files = [(p, NOT_HOOKS.get(p.name, f".claude/hooks/{p.name}")) for p in sorted(HOOKS.glob("*.py"))
             if not p.name.startswith("test_")]
    files += [(p, p.relative_to(KIT).as_posix()) for p in sorted(KIT.rglob("*"))
              if p.is_file() and "__pycache__" not in p.parts and not p.name.startswith("test_")]
    if not no_state:
        files.append((ACL / STATE[0], STATE[1]))
    return files


def _script(cmd: str) -> str:
    """The hook script a command line runs (its last path component), to tell the kit's hook from a look-alike."""
    for word in reversed(cmd.replace('"', " ").split()):
        if word.endswith(".py"):
            return word.rsplit("/", 1)[-1]
    return cmd


def merge_settings(existing: dict, kit: dict) -> tuple[dict, list[str]]:
    """`existing` with the kit's env keys, matchers and hook commands added. Nothing is removed or reordered; a hook
    already present (same script under the same matcher) is left as the project has it. Raises Refuse on a shape it
    can't extend without guessing. Returns (merged, what was added)."""
    out, added = json.loads(json.dumps(existing)), []
    if not isinstance(out, dict):
        raise Refuse("the top level is not a JSON object")
    env = out.setdefault("env", {})
    if not isinstance(env, dict):
        raise Refuse('"env" is not an object')
    for k, v in kit.get("env", {}).items():
        if k not in env:
            env[k] = v
            added.append(f"env {k}")
    hooks = out.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise Refuse('"hooks" is not an object')
    for event, entries in kit.get("hooks", {}).items():
        have = hooks.setdefault(event, [])
        if not isinstance(have, list) or not all(isinstance(e, dict) and isinstance(e.get("hooks", []), list) for e in have):
            raise Refuse(f'"hooks.{event}" is not a list of {{matcher, hooks[]}} entries')
        for entry in entries:
            matcher = entry.get("matcher")
            same = next((e for e in have if e.get("matcher") == matcher), None)
            if same is None:
                have.append(json.loads(json.dumps(entry)))
                added.append(f"{event} [{matcher or 'all'}]: " + ", ".join(_script(h["command"]) for h in entry["hooks"]))
                continue
            present = {_script(h.get("command", "")) for h in same.get("hooks", []) if isinstance(h, dict)}
            for h in entry["hooks"]:
                if _script(h["command"]) not in present:
                    same.setdefault("hooks", []).append(dict(h))
                    added.append(f"{event} [{matcher or 'all'}]: {_script(h['command'])}")
    return out, added


def install_settings(repo: Path, dry: bool) -> str:
    dest = repo / SETTINGS
    kit = json.loads((KIT / SETTINGS).read_text())
    if not dest.exists():
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(KIT / SETTINGS, dest)
        return f"created {SETTINGS}"
    try:
        merged, added = merge_settings(json.loads(dest.read_text(encoding="utf-8")), kit)
    except (ValueError, Refuse) as e:
        raise Refuse(f"{SETTINGS} was NOT changed and the kit is NOT wired: {e}. Nothing else was installed. Add the "
                     f"entries from {KIT / SETTINGS} by hand, or fix the file and run again.") from e
    if not added:
        return f"{SETTINGS} already wires every kit hook"
    if not dry:
        backup = dest.with_name(f"settings.json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(dest, backup)
        dest.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return f"merged into {SETTINGS} (backup settings.json.bak-*): " + "; ".join(added)


def install_claude_md(repo: Path, force: bool, dry: bool) -> str:
    dest, src = repo / "CLAUDE.md", KIT / "CLAUDE.md"
    if not dest.exists():
        if not dry:
            shutil.copy2(src, dest)
        return "created CLAUDE.md"
    text = dest.read_text(encoding="utf-8")
    if text == src.read_text(encoding="utf-8") or (MARK_BEGIN in text and not force):
        return "CLAUDE.md already has the kit's skeleton"
    if force:
        section = f"{MARK_BEGIN}\n{src.read_text(encoding='utf-8').rstrip()}\n{MARK_END}\n"
        if MARK_BEGIN in text and MARK_END in text:
            a, b = text.index(MARK_BEGIN), text.index(MARK_END) + len(MARK_END) + 1
            new, what = text[:a] + section + text[b:], "replaced the marked kit section of"
        else:
            new, what = text.rstrip() + "\n\n" + section, "appended a marked kit section to"
        if not dry:
            dest.write_text(new, encoding="utf-8")
        return f"{what} CLAUDE.md (the rest is untouched)"
    if not dry:
        shutil.copy2(src, repo / "CLAUDE.loop.md")
    return "CLAUDE.md exists: wrote the skeleton to CLAUDE.loop.md; merge what you want by hand (or --force to append it)"


def install(repo: Path, force: bool = False, no_state: bool = False, dry_run: bool = False) -> tuple[list[str], list[str], list[str]]:
    """(written, kept, notes). With dry_run nothing is written; the lists say what would be."""
    written, kept, notes = [], [], []
    # Settings first: if it can't be merged, nothing else is installed.
    notes.append(install_settings(repo, dry_run))
    for src, rel in plan(no_state):
        if rel in (SETTINGS, "CLAUDE.md"):
            continue
        dest = repo / rel
        if dest.exists() and not force:
            kept.append(rel)
            continue
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        written.append(rel)
    notes.append(install_claude_md(repo, force, dry_run))
    config = repo / ".loop" / "config.json"
    if not config.exists():
        if not dry_run:
            sys.path.insert(0, str(HOOKS))
            import _loop  # noqa: E402 - the defaults live with the hooks that read them
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(json.dumps(_loop.DEFAULTS, indent=1) + "\n")
        written.append(".loop/config.json")
    else:
        kept.append(".loop/config.json")
    ignore = repo / ".gitignore"
    lines = ignore.read_text().splitlines() if ignore.exists() else []
    if ".loop/" not in lines:
        if not dry_run:
            ignore.write_text("\n".join([*lines, ".loop/"]) + "\n")
        written.append(".gitignore")
    return written, kept, notes


def run_tests() -> list[str]:
    """The hook tests, run in this repo's hooks/ (they test the source the kit installs; the target gets no tests)."""
    failed = []
    for t in sorted(HOOKS.glob("test_*.py")):
        r = subprocess.run([sys.executable, t.name], cwd=HOOKS, capture_output=True, text=True, timeout=300)
        print(f"  {'ok  ' if r.returncode == 0 else 'FAIL'}  {t.name}")
        if r.returncode:
            failed.append(t.name)
            print("        " + "\n        ".join((r.stdout + r.stderr).strip().splitlines()[-5:]))
    return failed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="print what would change; write nothing")
    ap.add_argument("--force", action="store_true", help="overwrite existing hooks, scripts and docs (CLAUDE.md gets a marked section)")
    ap.add_argument("--no-state", action="store_true", help="don't install docs/plans/LOOP_STATE.md")
    ap.add_argument("--test", action="store_true", help="run the hook tests (from this repo's hooks/) afterwards")
    a = ap.parse_args(argv)
    repo = a.repo.expanduser().resolve()
    if not (repo / ".git").exists():
        print(f"bootstrap_kit: {repo} is not a git repository (git init it first)", file=sys.stderr)
        return 2
    try:
        written, kept, notes = install(repo, a.force, a.no_state, a.dry_run)
    except Refuse as e:
        print(f"bootstrap_kit: STOPPED. {e}", file=sys.stderr)
        return 3
    tag = "DRY RUN, nothing written: would write" if a.dry_run else "wrote"
    print(f"bootstrap_kit: {tag} {len(written)} file(s), {len(kept)} left as they were")
    for n in notes:
        print(f"  {'(dry run) ' if a.dry_run else ''}{n}")
    for rel in written:
        print(f"  {'would write' if a.dry_run else 'wrote'}  {rel}")
    for rel in kept:
        print(f"  kept   {rel} (exists; --force replaces it)")
    if a.dry_run:
        return 0
    print("Next: fill the <placeholders> in CLAUDE.md (or CLAUDE.loop.md) and docs/process/, set LOOP_LIVE_CHECKOUT in "
          ".claude/settings.json (empty: no checkout is guarded), and schedule scripts/watchdog.py, "
          "scripts/worktree_gc.py --apply and scripts/waiter_reaper.py --apply every 15 minutes.")
    print("Config (.loop/config.json, hooks/README.md): off until you turn them on: gh_rules.block_pr_merge (blocks "
          "`gh pr merge`), coordinator.require_checks (Stop hook), finish_before_start.max_waiting_prs, "
          "prelanding.code_paths (the gate-change rule). On by default: admission_gate blocks a spawn under "
          "resources.min_free_disk_gb (15 GB free, lowered on a small disk) or over max_swap_used_gb; wip_limit blocks "
          "`gh pr create` at 7 open product PRs; git_rules blocks --no-verify and a helper's worktree outside "
          "git_rules.worktree_dirs. Change them there.")
    if a.test:
        print("hook tests (run from the kit source):")
        failed = run_tests()
        if failed:
            print(f"bootstrap_kit: {len(failed)} hook test(s) failed")
            return 1
        print("bootstrap_kit: every hook test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
