#!/usr/bin/env python3
"""throwaway_worktrees.py: a cap on places, removal however a run ends, a sweep of the ones a kill left.
    python3 templates/project-kit/scripts/test_throwaway_worktrees.py"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import throwaway_worktrees as tw  # noqa: E402


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout


class Throwaways(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.d = Path(os.path.realpath(self._t.name))
        self.repo = self.d / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        for k, v in {"user.name": "t", "user.email": "t@example.invalid", "commit.gpgsign": "false"}.items():
            git(self.repo, "config", k, v)
        (self.repo / "a").write_text("a\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "init")
        os.environ.pop(tw.HELD_ENV, None)

    def tearDown(self):
        os.environ.pop(tw.HELD_ENV, None)
        self._t.cleanup()

    def make(self, name):
        p = self.d / name
        git(self.repo, "worktree", "add", "-q", "--detach", str(p), "HEAD")
        return p

    def test_places_are_capped_and_a_waiter_gets_one_when_it_frees(self):
        said = []
        with tw.slot(self.d / "locks", 1, say=said.append) as a:
            self.assertEqual(a, 0)
            os.environ.pop(tw.HELD_ENV)  # as another process: no parent place
            naps = []

            def nap(_s):
                naps.append(1)
                if len(naps) == 2:  # the holder ends while the waiter sleeps
                    raise KeyboardInterrupt
            with self.assertRaises(KeyboardInterrupt):
                with tw.slot(self.d / "locks", 1, say=said.append, sleep=nap):
                    pass
            self.assertEqual(len([s for s in said if "all 1 places" in s]), 1, "says it once")
            os.environ[tw.HELD_ENV] = "1"
        with tw.slot(self.d / "locks", 1) as b:
            self.assertEqual(b, 0, "the place was released")

    def test_a_parents_place_is_reused(self):
        os.environ[tw.HELD_ENV] = "1"
        with tw.slot(self.d / "locks", 1) as got:
            self.assertIsNone(got)

    def test_owned_removes_on_exit_and_on_error(self):
        p = self.make("prelanding-a")
        with tw.owned(p, self.repo, say=lambda _m: None):
            self.assertEqual(Path(str(p) + tw.OWNER_SUFFIX).read_text(), str(os.getpid()))
        self.assertFalse(p.exists())
        self.assertFalse(Path(str(p) + tw.OWNER_SUFFIX).exists())
        q = self.make("prelanding-b")
        with self.assertRaises(RuntimeError):
            with tw.owned(q, self.repo):
                raise RuntimeError
        self.assertFalse(q.exists())
        k = self.make("prelanding-c")
        with tw.owned(k, self.repo, keep=True, say=lambda _m: None):
            pass
        self.assertTrue(k.exists())

    def test_a_sigterm_runs_the_removal(self):
        p = self.make("prelanding-term")
        code = ("import os, signal, sys; sys.path.insert(0, %r); import throwaway_worktrees as tw; from pathlib import Path\n"
                "with tw.owned(Path(%r), Path(%r)):\n    os.kill(os.getpid(), signal.SIGTERM)\n" % (str(Path(tw.__file__).parent), str(p), str(self.repo)))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(r.returncode, 128 + signal.SIGTERM, r.stderr)
        self.assertFalse(p.exists())

    def test_sweep_takes_only_idle_ownerless_throwaways(self):
        old, mine, other = self.make("prelanding-old"), self.make("prelanding-mine"), self.make("feature-x")
        Path(str(mine) + tw.OWNER_SUFFIX).write_text(str(os.getpid()))
        later = time.time() + 3 * 3600
        self.assertEqual(tw.sweep(self.repo, [self.d], now=time.time(), say=lambda _m: None), [], "not idle yet")
        got = tw.sweep(self.repo, [self.d], now=later, apply=False, say=lambda _m: None)
        self.assertEqual([x.name for x in got], ["prelanding-old"], "a live owner and another name are kept")
        self.assertTrue(old.exists())
        tw.sweep(self.repo, [self.d], now=later, say=lambda _m: None)
        self.assertFalse(old.exists())
        self.assertTrue(mine.exists() and other.exists())

    def test_the_cap_comes_from_config(self):
        self.assertEqual(tw.slots_wanted(self.repo), 2)
        (self.repo / ".loop").mkdir()
        (self.repo / ".loop" / "config.json").write_text('{"prelanding": {"max_throwaways": 4}}')
        self.assertEqual(tw.slots_wanted(self.repo), 4)


if __name__ == "__main__":
    unittest.main()
