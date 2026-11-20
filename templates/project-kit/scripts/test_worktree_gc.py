#!/usr/bin/env python3
"""worktree_gc.py on a throwaway repo: which worktrees it removes, and what it never touches.
    python3 templates/project-kit/scripts/test_worktree_gc.py"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worktree_gc as gc  # noqa: E402

H = 3600


class Plan(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.d = Path(os.path.realpath(self._t.name))
        self.origin, self.root = self.d / "origin.git", self.d / "repo"
        subprocess.run(["git", "init", "-q", "--bare", str(self.origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.root)], check=True, capture_output=True)
        for k, v in {"user.name": "t", "user.email": "t@example.invalid", "commit.gpgsign": "false"}.items():
            self.g(self.root, "config", k, v)
        (self.root / "a.txt").write_text("a\n")
        self.g(self.root, "add", "-A")
        self.g(self.root, "commit", "-qm", "init")
        self.g(self.root, "push", "-q", "origin", "HEAD:main")
        self.g(self.root, "fetch", "-q")
        self.old = time.time() + 7 * H  # "now" for the plan: everything made here looks 7 h idle

    def tearDown(self):
        self._t.cleanup()

    def g(self, cwd, *a):
        return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout

    def add(self, name, commit=False, where=None):
        path = (where or self.d / "repo-worktrees") / name
        self.g(self.root, "worktree", "add", "-q", "-b", name, str(path), "origin/main")
        if commit:
            (path / f"{name}.txt").write_text(name + "\n")
            self.g(path, "add", "-A")
            self.g(path, "commit", "-qm", name)
        return path

    def planned(self, prs=lambda _r: {}, now=None):
        return {os.path.basename(w["path"]): w["why"] for w in gc.plan(str(self.root), now or self.old, prs=prs)}

    def test_finished_worktrees_go_wherever_they_live(self):
        self.add("never-started")
        self.add("stray", where=self.d / "elsewhere")
        got = self.planned()
        self.assertIn("never-started", got)
        self.assertIn("outside the managed dirs", got["stray"])
        self.assertNotIn("outside", got["never-started"])

    def test_unmerged_work_is_kept_unless_its_pr_is_closed(self):
        p = self.add("feat", commit=True)
        self.assertEqual(self.planned(), {})
        head = self.g(p, "rev-parse", "HEAD").strip()
        self.assertIn("its PR is merged", self.planned(prs=lambda _r: {head: "MERGED"})["feat"])
        self.assertEqual(self.planned(prs=lambda _r: {"0" * 40: "MERGED"}), {}, "a PR at another head doesn't count")

    def test_kept(self):
        dirty = self.add("dirty")
        (dirty / "new.txt").write_text("x\n")
        keep = self.add("keep")
        (keep / ".gc-keep").write_text("")
        self.add("clean")
        self.add("held")
        Path(self.root, ".loop").mkdir()
        Path(self.root, ".loop", "lanes.json").write_text(json.dumps({"lanes": [{"branch": "held"}]}))
        self.assertEqual(self.planned(now=self.old), {"clean": self.planned(now=self.old)["clean"]})
        self.assertEqual(self.planned(now=time.time()), {}, "nothing is idle yet")

    def test_the_main_checkout_is_never_listed(self):
        self.assertEqual(self.planned(), {})

    def test_apply_removes_and_logs(self):
        p = self.add("done")
        os.utime(p, None)
        old = time.time() - 7 * H
        gd = self.g(p, "rev-parse", "--absolute-git-dir").strip()
        for name in ("HEAD", "index", "logs/HEAD"):
            if os.path.exists(os.path.join(gd, name)):
                os.utime(os.path.join(gd, name), (old, old))
        env = {**os.environ, "LOOP_GH_BIN": "false"}
        r = subprocess.run([sys.executable, gc.__file__, "--apply", "--repo", str(self.root)], capture_output=True,
                           text=True, env=env)
        self.assertIn("removed", r.stdout, r.stderr)
        self.assertFalse(p.exists())
        self.assertIn('"branch": "done"', Path(self.root, ".loop", "worktree_gc.jsonl").read_text())


if __name__ == "__main__":
    unittest.main()
