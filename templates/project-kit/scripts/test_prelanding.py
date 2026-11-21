#!/usr/bin/env python3
"""prelanding.py's gate-change rule: a gate changed with product code needs an independent review line.
    python3 templates/project-kit/scripts/test_prelanding.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prelanding  # noqa: E402

CFG = {**prelanding.DEFAULTS, "code_paths": ["src/"]}
FILES = [".claude/hooks/git_rules.py", "src/app.py"]


class GateChange(unittest.TestCase):
    def test_gate_and_code_without_a_line_is_refused(self):
        why = prelanding.gate_change_refusal(FILES, "", CFG)
        self.assertIn("changes a gate (.claude/hooks/git_rules.py)", why)
        self.assertIn("Gate change: reviewed by", why)

    def test_an_independent_reviewer_passes(self):
        self.assertEqual(prelanding.gate_change_refusal(FILES, "Body.\nGate change: reviewed by a fresh reviewer agent\n", CFG), "")
        self.assertEqual(prelanding.gate_change_refusal(FILES, "- Gate change: reviewed by the owner", CFG), "")

    def test_the_author_or_coordinator_does_not_count(self):
        for who in ("me", "the author", "Coordinator", "self (checked twice)"):
            why = prelanding.gate_change_refusal(FILES, f"Gate change: reviewed by {who}", CFG)
            self.assertIn("isn't independent", why, who)

    def test_gate_alone_or_code_alone_is_fine(self):
        self.assertEqual(prelanding.gate_change_refusal(FILES[:1], "", CFG), "")
        self.assertEqual(prelanding.gate_change_refusal(FILES[1:], "", CFG), "")
        self.assertNotEqual(prelanding.gate_change_refusal(["scripts/deploy_gate.py", "src/x.py"], "", CFG), "")

    def test_off_without_code_paths(self):
        self.assertEqual(prelanding.gate_change_refusal(FILES, "", prelanding.DEFAULTS), "")


RULES = {**prelanding.DEFAULTS, "review_lines": [{"name": "Fidelity", "when_body": "^Cutover:", "when_paths": ["ui/"]}]}


class ReviewLines(unittest.TestCase):
    def test_a_cutover_body_without_the_line_is_refused(self):
        why = prelanding.missing_review_lines(["config/flags.json"], "Cutover: the new screen\n", RULES)
        self.assertEqual(len(why), 1)
        self.assertIn("Fidelity: OK", why[0])

    def test_a_listed_path_needs_it_too(self):
        self.assertIn("ui/home.py", prelanding.missing_review_lines(["ui/home.py"], "", RULES)[0])

    def test_an_independent_ok_passes_and_the_author_does_not(self):
        body = "Cutover: x\nFidelity: OK (fresh-reviewer, sheet 1a2b)\n"
        self.assertEqual(prelanding.missing_review_lines([], body, RULES), [])
        self.assertIn("isn't independent", prelanding.missing_review_lines([], "Cutover: x\nFidelity: OK (author)", RULES)[0])
        self.assertTrue(prelanding.missing_review_lines([], "Cutover: x\nFidelity: pending", RULES))

    def test_nothing_required_otherwise(self):
        self.assertEqual(prelanding.missing_review_lines(["src/a.py"], "A change.", RULES), [])
        self.assertEqual(prelanding.missing_review_lines(["ui/a.py"], "Cutover: x", prelanding.DEFAULTS), [])


if __name__ == "__main__":
    unittest.main()
