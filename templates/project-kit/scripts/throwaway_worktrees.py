#!/usr/bin/env python3
"""
Throwaway worktrees that never outlive their run, and never pile up while they wait.

A checking script (prelanding.py) makes a full scratch checkout of the branch it checks. In the project this came from,
six queued runs each held a ~1 GB checkout (more once built) while they waited for the one build slot, a killed run
left its checkout behind, and the disk fell to 8-12 GB free. Three rules:

1. At most `prelanding.max_throwaways` (default 2) throwaway worktrees at once. `slot()` takes one of that many places
   (flock files under the main checkout's `.loop/throwaway-slots/`) BEFORE the worktree is made, and waits for one.
   A nested run that its parent already gave a place (env THROWAWAY_SLOT_HELD=1) reuses the parent's, so two parents
   can never deadlock each other.
2. `owned()` writes the owner's pid beside the worktree (`<worktree>.owner`), turns SIGTERM and SIGHUP into SystemExit
   (so the `finally` that removes it runs), and registers an atexit removal as a backstop.
3. A SIGKILL still leaves one: `sweep()` (run at the start of every checking run) removes a `prelanding-*` throwaway
   under the main checkout's `.loop/throwaways/` (the only place it looks) that has been idle `STALE_H` (2 h) with its
   owner gone.

    python3 scripts/throwaway_worktrees.py           # the stale throwaways sweep() would remove
    python3 scripts/throwaway_worktrees.py --apply   # remove them
"""
from __future__ import annotations

import argparse
import atexit
import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HELD_ENV = "THROWAWAY_SLOT_HELD"
STALE_H = 2.0
PREFIXES = ("prelanding-",)
OWNER_SUFFIX = ".owner"
LOCKS = "throwaway-slots"
DIR = "throwaways"  # under the main checkout's .loop/: the only place sweep() looks


def alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def slots_wanted(root: Path | None = None) -> int:
    try:
        cfg = json.loads(Path(root or ".", ".loop", "config.json").read_text())
        n = int((cfg.get("prelanding") or {}).get("max_throwaways") or 2)
    except (OSError, ValueError, TypeError, AttributeError):
        n = 2
    return max(1, n)


@contextlib.contextmanager
def slot(lock_dir: Path, slots: int = 2, purpose: str = "", poll: float = 5.0, say=print, sleep=time.sleep):
    """Hold one of `slots` places for the block (yields its index, or None when a parent holds one). Waits as long as it
    takes; says so once. Children inherit HELD_ENV."""
    if os.getenv(HELD_ENV) == "1":
        yield None
        return
    import fcntl
    lock_dir.mkdir(parents=True, exist_ok=True)
    told, held = False, None
    while held is None:
        for i in range(slots):
            fh = open(lock_dir / f"{i}.lock", "w")
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                fh.close()
                continue
            held = (i, fh)
            break
        if held is None:
            if not told:
                say(f"throwaway: all {slots} places are taken; waiting for one{f' ({purpose})' if purpose else ''}")
                told = True
            sleep(poll)
    os.environ[HELD_ENV] = "1"
    try:
        yield held[0]
    finally:
        os.environ.pop(HELD_ENV, None)
        held[1].close()  # closing releases the flock


def remove(path: Path, repo: Path) -> None:
    subprocess.run(["git", "worktree", "remove", "--force", str(path)], cwd=repo, capture_output=True)
    shutil.rmtree(path, ignore_errors=True)
    Path(str(path) + OWNER_SUFFIX).unlink(missing_ok=True)


@contextlib.contextmanager
def owned(path: Path, repo: Path, keep: bool = False, say=print):
    """The worktree at `path` belongs to this process: its pid is written beside it, and it is removed when the block
    ends, on SIGTERM or SIGHUP too (unless keep)."""
    Path(str(path) + OWNER_SUFFIX).write_text(str(os.getpid()))
    old = {s: signal.signal(s, lambda _n, _f: sys.exit(128 + _n)) for s in (signal.SIGTERM, signal.SIGHUP)}
    if not keep:
        atexit.register(remove, path, repo)
    try:
        yield
    finally:
        for s, h in old.items():
            signal.signal(s, h)
        if keep:
            say(f"throwaway: kept {path}")
        else:
            remove(path, repo)
            atexit.unregister(remove)


def stale(path: Path, now: float, pid_of=None) -> str:
    """Why this throwaway can be swept, or "": idle STALE_H hours and its owner is gone (the .owner file's pid)."""
    if not path.name.startswith(PREFIXES) or not path.is_dir():
        return ""
    idle = now - max([path.stat().st_mtime] + [p.stat().st_mtime for p in path.glob("*")][:50])
    if idle < STALE_H * 3600:
        return ""
    try:
        pid = int(Path(str(path) + OWNER_SUFFIX).read_text().strip())
    except (OSError, ValueError):
        pid = None
    return "" if alive(pid) else f"idle {idle / 3600:.1f} h, owner gone"


def sweep(repo: Path, dirs: list[Path], now: float | None = None, apply: bool = True, say=print) -> list[Path]:
    """Remove the stale throwaways in `dirs`; -> the ones found."""
    now = time.time() if now is None else now
    found = []
    for d in dirs:
        for path in sorted(d.glob("*")) if d.is_dir() else []:
            if why := stale(path, now):
                found.append(path)
                say(f"throwaway: {'removing' if apply else 'would remove'} {path} ({why})")
                if apply:
                    remove(path, repo)
    return found


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dir", action="append", help="where throwaways live (default: .loop/throwaways/ here)")
    ns = ap.parse_args(argv)
    repo = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or ".")
    dirs = [Path(d) for d in ns.dir or [repo / ".loop" / DIR]]
    if not sweep(repo, dirs, apply=ns.apply):
        print("throwaway: nothing stale")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
