#!/usr/bin/env python3
"""Each hook blocks what it should and allows what it should. Run: python3 hooks/test_hooks.py"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import admission_gate  # noqa: E402
import git_rules  # noqa: E402
import kill_rules  # noqa: E402
import live_checkout  # noqa: E402
import waiter_guard  # noqa: E402


class GitRules(unittest.TestCase):
    def test_stash(self):
        for cmd in ("git stash", "git stash -u", "git stash pop", "git stash push -m x", "cd a && git stash drop"):
            self.assertIsNotNone(git_rules.check(cmd), cmd)
        for cmd in ("git stash list", "git stash show -p", "git status"):
            self.assertIsNone(git_rules.check(cmd), cmd)

    def test_merge_chain(self):
        self.assertIsNotNone(git_rules.check("git merge origin/main && git add -A && git commit -m m"))
        self.assertIsNotNone(git_rules.check("git -C wt merge main; git commit -am m"))
        self.assertIsNone(git_rules.check("git merge origin/main"))
        self.assertIsNone(git_rules.check("git commit -m x && git merge main"))
        self.assertIsNone(git_rules.check("git merge --abort && git commit -m x"))


class KillRules(unittest.TestCase):
    def test(self):
        for cmd in ("pkill -f land.py", "killall node", "sleep 1; /usr/bin/pkill x", "sudo pkill x"):
            self.assertIsNotNone(kill_rules.check(cmd), cmd)
        for cmd in ("kill 4242", "pgrep -f '[l]and.py'", "echo pkill"):
            self.assertIsNone(kill_rules.check(cmd), cmd)


class WaiterGuard(unittest.TestCase):
    def test(self):
        self.assertIsNotNone(waiter_guard.check('until ! pgrep -f "run_suite.py"; do sleep 10; done'))
        self.assertIsNotNone(waiter_guard.check("while pgrep -fl 'land.py 12'; do sleep 5; done"))
        self.assertIsNone(waiter_guard.check("until ! pgrep -f '[r]un_suite.py'; do sleep 10; done"))
        self.assertIsNone(waiter_guard.check("pgrep -f run_suite.py"))


class AdmissionGate(unittest.TestCase):
    def setUp(self):
        self.ledger = os.path.join(tempfile.mkdtemp(), "lanes.json")
        admission_gate.LEDGER = admission_gate.Path(self.ledger)
        self.free = 100e9
        admission_gate.shutil.disk_usage = lambda _p: type("U", (), {"free": self.free})()
        self.swap = 1.0
        admission_gate.swap_used_gb = lambda: self.swap

    def spawn(self, line, kind="general-purpose"):
        return admission_gate.check({"prompt": "Do the thing.\n" + line, "subagent_type": kind})

    def test_lane_line_and_read_only(self):
        self.assertIsNotNone(self.spawn(""))
        self.assertIsNone(self.spawn("", kind="Explore"))
        self.assertIsNone(self.spawn("Lane: feature; Hotspot: api"))

    def test_caps_and_hotspots(self):
        import json, time
        lanes = [{"kind": "feature", "hotspots": ["api"], "updated": time.time()}]
        with open(self.ledger, "w") as fh:
            json.dump({"lanes": lanes}, fh)
        self.assertIsNotNone(self.spawn("Lane: feature; Hotspot: api"))
        self.assertIsNone(self.spawn("Lane: feature; Hotspot: ui"))
        with open(self.ledger, "w") as fh:
            json.dump({"lanes": lanes * 5}, fh)
        self.assertIsNotNone(self.spawn("Lane: bug; Hotspot: ui"))

    def test_resource_floors(self):
        self.free = 5e9
        self.assertIn("free disk", self.spawn("Lane: feature; Hotspot: ui"))
        self.free, self.swap = 100e9, 7.5
        self.assertIn("swap", self.spawn("Lane: feature; Hotspot: ui"))


class LiveCheckout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.live = os.path.join(self.tmp, "live")
        self.wt = os.path.join(self.tmp, "worktree")
        os.makedirs(self.live)
        os.makedirs(self.wt)

    def test_edit(self):
        self.assertIsNotNone(live_checkout.check_edit({"file_path": os.path.join(self.live, "a.py")}, self.live))
        self.assertIsNone(live_checkout.check_edit({"file_path": os.path.join(self.wt, "a.py")}, self.live))

    def test_git(self):
        self.assertIsNotNone(live_checkout.check_bash("git commit -m x", self.live, self.live))
        self.assertIsNotNone(live_checkout.check_bash(f"cd {self.live} && git pull", self.wt, self.live))
        self.assertIsNotNone(live_checkout.check_bash(f"git -C {self.live} reset --hard", self.wt, self.live))
        self.assertIsNone(live_checkout.check_bash("git status && git log", self.live, self.live))
        self.assertIsNone(live_checkout.check_bash("git worktree add ../wt2", self.live, self.live))
        self.assertIsNone(live_checkout.check_bash("git commit -m x", self.wt, self.live))


if __name__ == "__main__":
    unittest.main(verbosity=1)
