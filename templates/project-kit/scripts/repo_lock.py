#!/usr/bin/env python3
"""
Named locks shared by everyone who changes main or publishes from it on this machine: the
landing script (scripts/land.sh), and the deploy and release scripts if you add them. One lock per resource:

    merge    check that main hasn't moved since the checks, then merge (held for seconds)
             and pull the live checkout
    release  build and publish a release

    python3 scripts/repo_lock.py release -- scripts/release.sh --notes "…"   # run holding it
    python3 scripts/repo_lock.py merge --status                                # who holds it

An flock on ~/.loop/<name>.lock, released when the holder exits (even on a
crash). Children of a holder see REPO_LOCK_<NAME>=1 and don't take it again.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

NAMES = ("merge", "release")


def path(name: str) -> Path:
    return Path(os.getenv("LOOP_HOME") or Path.home() / ".loop") / f"{name}.lock"


def env_key(name: str) -> str:
    return f"REPO_LOCK_{name.upper()}"


def holder(name: str) -> dict:
    try:
        return json.loads(path(name).read_text() or "{}")
    except Exception:
        return {}


@contextlib.contextmanager
def repo_lock(name: str, purpose: str, timeout: float | None = None):
    """Hold lock `name` for the block (no-op inside a holder's child)."""
    if os.getenv(env_key(name)) == "1":
        yield
        return
    p = path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    f = open(p, "a+")
    start, told = time.time(), False
    while True:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if timeout is not None and time.time() - start > timeout:
                f.close()
                raise TimeoutError(f"{name} lock busy: {holder(name)}")
            if not told:
                print(f"waiting for the {name} lock (held by {holder(name)})…", file=sys.stderr, flush=True)
                told = True
            time.sleep(2)
    f.seek(0)
    f.truncate()
    f.write(json.dumps({"pid": os.getpid(), "purpose": purpose, "cwd": os.getcwd(), "since": int(time.time())}))
    f.flush()
    os.environ[env_key(name)] = "1"
    try:
        yield
    finally:
        os.environ.pop(env_key(name), None)
        f.seek(0)
        f.truncate()
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", choices=NAMES)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--timeout", type=float)
    argv = sys.argv[1:]
    cut = argv.index("--") if "--" in argv else len(argv)
    a, cmd = ap.parse_args(argv[:cut]), argv[cut + 1:]
    if a.status:
        print(json.dumps(holder(a.name)) if holder(a.name) else "free")
        return 0
    if not cmd:
        ap.error("nothing to run: repo_lock.py NAME -- <cmd>")
    try:
        with repo_lock(a.name, " ".join(cmd)[:200], a.timeout):
            return subprocess.call(cmd)
    except TimeoutError as e:
        print(e, file=sys.stderr)
        return 75


if __name__ == "__main__":
    sys.exit(main())
