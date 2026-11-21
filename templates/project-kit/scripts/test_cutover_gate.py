#!/usr/bin/env python3
"""scripts/cutover_gate.py: a cutover is refused while the release pipeline is paused, when a config cutover's build
lacks the shipped code it switches on, and without a whole-suite pass in 24 h on a commit containing its base.
On a throwaway git repo.

    python3 scripts/test_cutover_gate.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cutover_gate as cg  # noqa: E402

NOW = time.time()


def g(cwd: Path, *a: str) -> str:
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class Gate(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="cutover-gate-"))
        self.addCleanup(shutil.rmtree, self.repo, True)
        g(self.repo, "init", "-q", "-b", "main")
        g(self.repo, "config", "user.email", "t@example.invalid")
        g(self.repo, "config", "user.name", "t")
        self.published = self.commit("src/app.py", "1")
        self.commit("src/app.py", "2")          # a shipped change after the published build
        self.commit("tests/test_app.py", "1")   # not shipped
        self.main = g(self.repo, "rev-parse", "HEAD")
        g(self.repo, "update-ref", "refs/remotes/origin/main", self.main)
        g(self.repo, "checkout", "-q", "-b", "cut")
        self.commit("config/flags.json", '{"new": true}')
        (self.repo / ".loop").mkdir()
        self.config({})
        self.write("rel/latest.json", {"commit": self.main, "version": "2.0"})
        self.passes([{"at": NOW - 3600, "commit": self.main, "full": True, "failed": 0}])

    def commit(self, path: str, text: str) -> str:
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        g(self.repo, "add", "-A")
        g(self.repo, "commit", "-q", "-m", f"edit {path}")
        return g(self.repo, "rev-parse", "HEAD")

    def write(self, rel: str, doc: dict) -> None:
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(doc))

    def config(self, cut: dict, rel: dict | None = None) -> None:
        self.write(".loop/config.json", {
            "release": {"paused_file": "rel/paused.json", "published_file": "rel/latest.json", "shipped_paths": ["src/"],
                        "resume_command": "make resume", **(rel or {})},
            "cutover": {"passes_file": "rel/passes.jsonl", "known_red_file": "rel/red.json", "suite_command": "make suite",
                        **cut}})

    def passes(self, rows: list[dict]) -> None:
        (self.repo / "rel" / "passes.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))

    def why(self, body: str = "Cutover: the new screen\n", files=("config/flags.json",)) -> str:
        return cg.refusal(self.repo, list(files), body, "origin/main", now=NOW, say=lambda m: None)

    def test_not_a_cutover_passes_at_once(self):
        self.write("rel/paused.json", {"at": NOW - 99999})
        self.assertEqual(self.why(body="A change."), "")

    def test_ready(self):
        self.assertEqual(self.why(), "")

    def test_a_listed_path_makes_it_a_cutover(self):
        self.config({"when_paths": ["config/flags.json"]})
        self.passes([])
        self.assertIn("whole-suite", self.why(body="no line"))

    def test_a_paused_pipeline_refuses(self):
        self.write("rel/paused.json", {"at": NOW - 86400, "why": "crash loop"})
        why = self.why()
        self.assertIn("paused (crash loop", why)
        self.assertIn("make resume", why)

    def test_a_config_cutover_needs_the_shipped_code_in_the_published_build(self):
        self.write("rel/latest.json", {"commit": self.published, "version": "1.9"})
        why = self.why()
        self.assertIn("lacks 1 shipped change(s)", why, "the test-only commit doesn't count")
        self.assertIn("1.9", why)

    def test_a_cutover_that_changes_shipped_code_ships_next(self):
        self.write("rel/latest.json", {"commit": self.published})
        self.assertEqual(self.why(files=("config/flags.json", "src/app.py")), "")

    def test_an_unreadable_published_build_refuses(self):
        self.write("rel/latest.json", {"commit": "0" * 40})
        self.assertIn("can't be read", self.why())

    def test_the_suite_pass_must_be_recent_whole_and_contain_the_base(self):
        self.passes([{"at": NOW - 30 * 3600, "commit": self.main, "full": True, "failed": 0}])
        self.assertIn("no whole-suite run in 24 h", self.why())
        self.passes([{"at": NOW - 60, "commit": self.main, "full": False, "failed": 0}])
        self.assertIn("no whole-suite run", self.why())
        self.passes([{"at": NOW - 60, "commit": self.published, "full": True, "failed": 0}])
        self.assertIn("doesn't contain the base", self.why())

    def test_failures_pass_only_when_all_known_red(self):
        self.passes([{"at": NOW - 60, "commit": self.main, "full": True, "failed": 1, "failures": ["login"]}])
        self.assertIn("not known red: login", self.why())
        self.write("rel/red.json", {"scenarios": ["login"]})
        self.assertEqual(self.why(), "")
        self.passes([{"at": NOW - 60, "commit": self.main, "full": True, "failed": 2}])
        self.assertIn("unnamed", self.why())

    def test_no_passes_file_refuses(self):
        self.config({"passes_file": ""})
        why = self.why()
        self.assertIn("cutover.passes_file", why)
        self.assertIn("make suite", why)

    def test_release_unset_skips_checks_one_and_two(self):
        self.config({}, {"paused_file": "", "published_file": ""})
        self.write("rel/paused.json", {"at": NOW})
        self.assertEqual(self.why(), "")


if __name__ == "__main__":
    unittest.main()
