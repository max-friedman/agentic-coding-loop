#!/usr/bin/env python3
"""scripts/verify_queue.py: the hold decision and the parsing. No gh, no network.

    python3 scripts/test_verify_queue.py
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_queue as vq  # noqa: E402


class Decide(unittest.TestCase):
    def test_bug_is_held(self):
        self.assertTrue(vq.should_hold(["bug"]))
        self.assertTrue(vq.should_hold([]))

    def test_exempt_and_already_held(self):
        for lab in ("no-verify", "enhancement", "feature-request", "documentation", "process", "question"):
            self.assertFalse(vq.should_hold(["bug", lab]), lab)
        self.assertFalse(vq.should_hold(["bug", "verify"]))

    def test_pr_from_comments_takes_latest(self):
        a, b = vq.hold_comment(10), vq.hold_comment(22)
        self.assertEqual(vq.pr_from_comments(["hi", a, b]), 22)
        self.assertIsNone(vq.pr_from_comments(["nothing", ""]))

    def test_first_release(self):
        self.assertEqual(vq.first_release(["v1.0.2215", "v1.0.2214", "nightly", "v1.0.999"]), "v1.0.999")
        self.assertIsNone(vq.first_release(["x"]))


class Hold(unittest.TestCase):
    def run_hold(self, issue, refs=((7,))):
        calls = []

        def fake(*a):
            calls.append(a)
            return mock.Mock(returncode=0, stdout="", stderr="")

        def fake_json(*a):
            if a[0] == "pr":
                return {"closingIssuesReferences": [{"number": n} for n in refs]}
            return issue
        with mock.patch.object(vq, "_gh", fake), mock.patch.object(vq, "_json", fake_json), \
                mock.patch.object(vq.time, "sleep"):
            held = vq.hold_open(5, say=lambda m: None)
        return held, calls

    def test_closed_bug_reopened_and_labelled(self):
        held, calls = self.run_hold({"state": "CLOSED", "labels": [{"name": "bug"}]})
        self.assertEqual(held, [7])
        self.assertTrue(any(c[:2] == ("issue", "reopen") for c in calls))
        self.assertTrue(any("--add-label" in c and "verify" in c for c in calls))

    def test_exempt_untouched(self):
        held, calls = self.run_hold({"state": "CLOSED", "labels": [{"name": "no-verify"}]})
        self.assertEqual(held, [])
        self.assertFalse(any(c[:2] == ("issue", "reopen") for c in calls))

    def test_no_closing_issues(self):
        held, calls = self.run_hold({}, refs=())
        self.assertEqual((held, calls), ([], []))

    def test_gh_failure_never_raises(self):
        with mock.patch.object(vq, "_json", side_effect=RuntimeError("boom")):
            self.assertEqual(vq.hold_open(5, say=lambda m: None), [])


if __name__ == "__main__":
    unittest.main()
