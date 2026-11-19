#!/usr/bin/env python3
"""The kit's two hooks from the loop repo's hooks/ folder: the lane cap and the wait-loop guard.
The other hooks here carry their own test_<hook>.py. Run: python3 .claude/hooks/test_loop_hooks.py"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import admission_gate  # noqa: E402
import waiter_guard  # noqa: E402


class WaiterGuard(unittest.TestCase):
    def test(self):
        self.assertIsNotNone(waiter_guard.check('until ! pgrep -f "run_suite.py"; do sleep 10; done'))
        self.assertIsNone(waiter_guard.check("until ! pgrep -f '[r]un_suite.py'; do sleep 10; done"))
        self.assertIsNone(waiter_guard.check("pgrep -f run_suite.py"))


class AdmissionGate(unittest.TestCase):
    def setUp(self):
        self.ledger = os.path.join(tempfile.mkdtemp(), "lanes.json")
        admission_gate.LEDGER = admission_gate.Path(self.ledger)
        admission_gate.shutil.disk_usage = lambda _p: type("U", (), {"free": 100e9})()
        admission_gate.swap_used_gb = lambda: 1.0

    def spawn(self, line):
        return admission_gate.check({"prompt": "Do the thing.\n" + line, "subagent_type": "general-purpose"})

    def test_lane_line_and_hotspot(self):
        self.assertIsNotNone(self.spawn(""))
        self.assertIsNone(self.spawn("Lane: feature; Hotspot: api"))
        with open(self.ledger, "w") as fh:
            json.dump({"lanes": [{"kind": "feature", "hotspots": ["api"], "updated": time.time()}]}, fh)
        self.assertIsNotNone(self.spawn("Lane: feature; Hotspot: api"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
