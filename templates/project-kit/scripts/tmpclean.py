"""
Test helper: remove every temp directory this process makes with tempfile.mkdtemp when it exits.

2026-10-05: $TMPDIR held ~28 GB in ~50,000 leftover dirs: the suites made them with mkdtemp and never removed them
(each full run left hundreds). `tmpclean.install()` at the top of a test file keeps the tests unchanged and cleans up
after them. A killed run (SIGKILL, timeout) still leaves its dirs behind: scripts/worktree_gc.py sweeps those.
"""
from __future__ import annotations

import atexit
import shutil
import tempfile

_made: list[str] = []
_orig = tempfile.mkdtemp
_installed = False


def _mkdtemp(*a, **kw):
    d = _orig(*a, **kw)
    _made.append(d)
    return d


def cleanup() -> None:
    while _made:
        shutil.rmtree(_made.pop(), ignore_errors=True)


def install() -> None:
    global _installed
    if not _installed:
        _installed = True
        tempfile.mkdtemp = _mkdtemp
        atexit.register(cleanup)
