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


if __name__ == "__main__":
    unittest.main()
