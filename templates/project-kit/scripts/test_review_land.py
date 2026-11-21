#!/usr/bin/env python3
"""scripts/review_land.py: a worktree on the PR's exact branch (new, an existing stale local branch, or the worktree
that has it), main merged in or a conflict stopped, the review line set through a per-PR body file, prelanding before
the landing. On throwaway git repos with a bare origin, a fake gh and fake prelanding / land runs.

    python3 scripts/test_review_land.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_land as rl  # noqa: E402

BODY = "Does a thing.\n\nCutover: the new screen\n\n## Release note\nNone\n"
LINE = "Fidelity: OK (fresh-reviewer, checked a, b)"


def g(cwd: Path, *a: str) -> str:
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def ident(cwd: Path) -> None:
    g(cwd, "config", "user.email", "t@example.invalid")
    g(cwd, "config", "user.name", "t")


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="review-land-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.origin = self.tmp / "origin.git"
        g(self.tmp, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.repo = self.tmp / "repo"
        g(self.tmp, "clone", "-q", str(self.origin), str(self.repo))
        ident(self.repo)
        self.commit(self.repo, "a.txt", "one\n")
        g(self.repo, "push", "-q", "origin", "HEAD:main")
        g(self.repo, "checkout", "-q", "-b", "feat/x")
        self.commit(self.repo, "b.txt", "pr\n")
        g(self.repo, "push", "-q", "origin", "feat/x")
        g(self.repo, "checkout", "-q", "main")
        g(self.repo, "branch", "-q", "-D", "feat/x")  # the PR's branch exists on origin only (a test adds a local one)
        self.worktrees = self.tmp / "wts"
        self.body = BODY
        self.edits: list = []
        self.cmds: list = []
        self.rc = {"prelanding.py": 0, "land.sh": 0}
        os.environ.pop("LOOP_LIVE_CHECKOUT", None)

    def commit(self, cwd: Path, path: str, text: str) -> str:
        (cwd / path).write_text(text)
        g(cwd, "add", "-A")
        g(cwd, "commit", "-q", "-m", f"edit {path}")
        return g(cwd, "rev-parse", "HEAD")

    def head(self) -> str:
        return subprocess.run(["git", "ls-remote", str(self.origin), "refs/heads/feat/x"],
                              capture_output=True, text=True).stdout.split()[0]

    def info(self, n):
        return {"number": n, "headRefName": "feat/x", "headRefOid": self.head(), "body": self.body, "state": "OPEN"}

    def fake_cmd(self, c, cwd):
        name = Path(c[1] if c[0] == sys.executable else c[0]).name
        self.cmds.append((name, c, cwd))
        return self.rc[name]

    def land(self, line=LINE, **kw):
        return rl.run(7, line, repo=self.repo, worktrees=self.worktrees, info=self.info,
                      edit=lambda n, p: self.edits.append((n, p, p.read_text())), cmd=self.fake_cmd,
                      tmp=self.tmp / "t", **kw)


class Worktree(Fixture):
    def test_new_worktree_on_the_exact_branch_then_prelanding_then_land(self):
        self.assertEqual(self.land(), 0)
        wt = self.worktrees / "review-7"
        self.assertEqual(g(wt, "rev-parse", "--abbrev-ref", "HEAD"), "feat/x")
        self.assertEqual([c[0] for c in self.cmds], ["prelanding.py", "land.sh"])
        self.assertEqual(self.cmds[1][1], ["scripts/land.sh", "7"])
        self.assertEqual(self.cmds[0][2], wt)
        n, path, text = self.edits[0]
        self.assertEqual(path, self.tmp / "t" / "7" / "body.md", "a per-PR body file")
        self.assertIn(LINE + "\n\n## Release note", text)

    def test_after_points_at_a_queue(self):
        self.rc["queue.py"] = 0
        self.assertEqual(self.land(after="queue.py add {pr}"), 0)
        self.assertEqual(self.cmds[1][1], ["queue.py", "add", "7"])

    def test_an_existing_stale_local_branch_is_fast_forwarded(self):
        g(self.repo, "branch", "feat/x", "main")  # the PR's name, an old commit (main's)
        other = self.tmp / "other"
        g(self.tmp, "clone", "-q", str(self.origin), str(other))
        ident(other)
        g(other, "checkout", "-q", "feat/x")
        self.commit(other, "c.txt", "more\n")
        g(other, "push", "-q", "origin", "feat/x")
        self.assertEqual(self.land(), 0)
        self.assertEqual(g(self.worktrees / "review-7", "rev-parse", "HEAD"), self.head())

    def test_a_local_branch_with_commits_the_pr_lacks_stops(self):
        g(self.repo, "fetch", "-q", "origin")
        g(self.repo, "branch", "feat/x", "origin/feat/x")
        g(self.repo, "checkout", "-q", "feat/x")
        self.commit(self.repo, "local.txt", "unpushed\n")
        g(self.repo, "checkout", "-q", "main")
        with self.assertRaises(rl.Stop) as e:
            self.land()
        self.assertEqual(e.exception.code, 4)
        self.assertIn("1 commit(s) the PR doesn't", str(e.exception))
        self.assertEqual(self.cmds, [], "nothing run")

    def test_the_worktree_that_has_the_branch_is_reused_and_must_be_clean(self):
        g(self.repo, "fetch", "-q", "origin")
        mine = self.tmp / "lane-wt"
        g(self.repo, "worktree", "add", "-q", "-b", "feat/x", str(mine), "origin/feat/x")
        (mine / "b.txt").write_text("dirty\n")
        with self.assertRaises(rl.Stop) as e:
            self.land()
        self.assertEqual(e.exception.code, 4)
        g(mine, "checkout", "-q", "--", "b.txt")
        self.assertEqual(self.land(), 0)
        self.assertEqual(self.cmds[0][2].resolve(), mine.resolve())
        self.assertFalse((self.worktrees / "review-7").exists())

    def test_never_the_live_checkout(self):
        g(self.repo, "fetch", "-q", "origin")
        g(self.repo, "checkout", "-q", "-b", "feat/x", "origin/feat/x")
        os.environ["LOOP_LIVE_CHECKOUT"] = str(self.repo)
        self.addCleanup(os.environ.pop, "LOOP_LIVE_CHECKOUT", None)
        with self.assertRaises(rl.Stop) as e:
            self.land()
        self.assertIn("live checkout", str(e.exception))

    def test_a_pr_that_moved_stops(self):
        info = self.info
        self.info = lambda n: dict(info(n), headRefOid="0" * 40)
        with self.assertRaises(rl.Stop) as e:
            self.land()
        self.assertIn("the PR moved", str(e.exception))


class MergeMain(Fixture):
    def test_behind_main_merges_and_pushes(self):
        self.commit(self.repo, "a.txt", "two\n")
        g(self.repo, "push", "-q", "origin", "HEAD:main")
        before = self.head()
        self.assertEqual(self.land(), 0)
        self.assertNotEqual(before, self.head(), "the merge was pushed")
        self.assertEqual((self.worktrees / "review-7" / "a.txt").read_text(), "two\n")

    def test_a_conflict_stops_and_aborts_the_merge(self):
        self.commit(self.repo, "b.txt", "main's\n")
        g(self.repo, "push", "-q", "origin", "HEAD:main")
        with self.assertRaises(rl.Stop) as e:
            self.land()
        self.assertEqual(e.exception.code, 3)
        self.assertIn("b.txt", str(e.exception))
        self.assertEqual(g(self.worktrees / "review-7", "status", "--porcelain"), "", "the merge was aborted")
        self.assertEqual(self.cmds, [])

    def test_prelanding_failure_doesnt_land(self):
        self.rc["prelanding.py"] = 13
        self.assertEqual(self.land(), 1)
        self.assertEqual([c[0] for c in self.cmds], ["prelanding.py"])

    def test_dry_run_changes_nothing(self):
        self.assertEqual(self.land(dry=True), 0)
        self.assertFalse((self.worktrees / "review-7").exists())
        self.assertEqual((self.edits, self.cmds), ([], []))


class Lines(unittest.TestCase):
    def test_parse_line(self):
        self.assertEqual(rl.parse_line("Fidelity: OK (r, x)"), ("Fidelity", "Fidelity: OK (r, x)"))
        for bad in ("  ", "OK (r)", "Fidelity:  "):
            with self.assertRaises(rl.Stop):
                rl.parse_line(bad)

    def test_set_line_replaces_inserts_and_keeps_one(self):
        two = "x\nFidelity: old one\nmid\n**Fidelity:** older\nend\n"
        self.assertEqual(rl.set_line(two, "Fidelity", "Fidelity: new"), "x\nFidelity: new\nmid\nend\n")
        self.assertEqual(rl.set_line("a\n\n## Release note\nNone\n", "Fidelity", "Fidelity: n"),
                         "a\n\nFidelity: n\n\n## Release note\nNone\n")
        self.assertEqual(rl.set_line("only text", "Fidelity", "Fidelity: n"), "only text\n\nFidelity: n\n")


if __name__ == "__main__":
    unittest.main()
