#!/usr/bin/env python3
"""stale_revert.py: a PR that undoes lines main gained since it forked is refused.
    python3 templates/project-kit/scripts/test_stale_revert.py"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stale_revert  # noqa: E402

DOC = "".join(f"existing line number {i} of the rules\n" for i in range(10))
OLD = DOC.replace("number 3", "number three")
ADDED = "".join(f"rule added by the merged PR {i} stays\n" for i in range(4))


class StaleRevertTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.d = Path(self._t.name)
        self.g("init", "-q")
        self.g("checkout", "-q", "-b", "main")
        self.g("config", "user.email", "t@example.invalid")
        self.g("config", "commit.gpgsign", "false")
        self.g("config", "user.name", "t")
        self.put("rules.md", DOC)
        self.commit("base")
        self.g("branch", "feature")
        self.put("rules.md", DOC + ADDED)  # the PR merged to main after the fork
        self.commit("merged PR")
        self.g("update-ref", "refs/remotes/origin/main", "main")
        self.g("checkout", "-q", "feature")

    def tearDown(self):
        self._t.cleanup()

    def g(self, *a):
        return subprocess.run(["git", *a], cwd=self.d, capture_output=True, text=True, check=True).stdout

    def put(self, name, text):
        (self.d / name).write_text(text)

    def commit(self, msg):
        self.g("add", "-A")
        self.g("commit", "-q", "-m", msg)

    def check(self, body=""):
        head = self.g("rev-parse", "HEAD").strip()
        files = self.g("diff", "--name-only", "origin/main...HEAD").split()
        return stale_revert.refusal(self.d, head, files, body, main="origin/main")

    def test_stale_overwrite_is_refused_and_names_the_culprit(self):
        self.put("rules.md", DOC.replace("number 3", "number three"))  # edited from the old copy
        self.commit("my edit")
        why = self.check()
        self.assertIn("rules.md: 4 lines main added are gone", why)
        self.assertIn("merged PR", why)

    def test_bad_merge_resolution_is_refused(self):
        self.put("rules.md", DOC + "my own new rule goes here\n")
        self.commit("my edit")
        self.g("merge", "-q", "-s", "ours", "main", "-m", "Merge main")  # keeps ours: drops main's lines
        self.assertIn("undoes lines", self.check())

    def test_proper_merge_keeps_both_sides(self):
        self.put("rules.md", DOC.replace("number 3", "number three"))
        self.commit("my edit")
        self.g("merge", "-q", "main", "-m", "Merge main")
        self.assertEqual(self.check(), "")

    def test_untouched_files_and_small_losses_are_fine(self):
        self.put("other.md", "something unrelated to anything\n")
        self.commit("other file")
        self.assertEqual(self.check(), "")
        self.put("rules.md", OLD)  # loses 4 lines: now flagged
        self.commit("old copy")
        self.assertNotEqual(self.check(), "")
        self.put("rules.md", OLD + ADDED.replace("stays", "stays!", 2))  # two lines edited: under the limit
        self.commit("reword two")
        self.assertEqual(self.check(), "")

    def test_on_purpose_line_in_body_or_commit(self):
        self.put("rules.md", OLD)
        self.commit("drop them")
        self.assertNotEqual(self.check(), "")
        self.assertEqual(self.check("Intentional revert: the merged rule was wrong, see the issue"), "")
        self.assertNotEqual(self.check("we revert nothing on purpose here"), "")
        self.put("rules.md", DOC + "x\n")
        self.commit("Back out\n\nIntentional revert: the rules are retired")
        self.assertEqual(self.check(), "")

    def test_blank_and_trivial_lines_do_not_count(self):
        self.assertFalse(stale_revert.significant("}"))
        self.assertFalse(stale_revert.significant("    "))
        self.assertFalse(stale_revert.significant("# ----------------"))
        self.assertTrue(stale_revert.significant("    return the value of x"))

    def test_git_trouble_fails_open(self):
        self.assertEqual(stale_revert.refusal(self.d, "deadbeef", ["rules.md"], "", main="origin/nope"), "")


if __name__ == "__main__":
    unittest.main()
