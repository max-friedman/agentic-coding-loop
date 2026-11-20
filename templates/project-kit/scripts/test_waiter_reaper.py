#!/usr/bin/env python3
"""waiter_reaper.py on a fake process list: which Claude Code waiter shells it kills, and what it never touches.

    python3 templates/project-kit/scripts/test_waiter_reaper.py
"""
from __future__ import annotations

import json
import signal
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import waiter_reaper as wr  # noqa: E402

H = 3600
SNAP = "/bin/zsh -c source ~/.claude/shell-snapshots/snapshot-zsh-1-abc.sh 2>/dev/null || true && eval "


def shell(pid, body, age_h=7.0, ppid=1):
    return {"pid": pid, "ppid": ppid, "age_s": int(age_h * H), "command": SNAP + repr(body)}


def child(pid, ppid, cmd="sleep 10"):
    return {"pid": pid, "ppid": ppid, "age_s": 5, "command": cmd}


WAIT = 'until ! pgrep -f "run_suite.py --mode slow"; do sleep 10; done'


class Plan(unittest.TestCase):
    def setUp(self):
        self._protected = wr.PROTECTED
        wr.PROTECTED = ("queue_worker", "nightly")

    def tearDown(self):
        wr.PROTECTED = self._protected

    def pids(self, procs):
        return [p["pid"] for p in wr.plan(procs)]

    def test_old_waiter_is_killed(self):
        self.assertEqual(self.pids([shell(100, WAIT), child(101, 100)]), [100])

    def test_young_waiter_is_kept(self):
        self.assertEqual(self.pids([shell(100, WAIT, age_h=5.9)]), [])

    def test_file_waiter_is_killed(self):
        self.assertEqual(self.pids([shell(100, "until [ -s /tmp/x.output ]; do sleep 5; done; cat /tmp/x.output")]), [100])

    def test_not_a_loop_is_kept(self):
        self.assertEqual(self.pids([shell(100, "python3 tests/run_suite.py --mode fast", age_h=20)]), [])

    def test_not_from_a_claude_snapshot_is_kept(self):
        p = {"pid": 100, "ppid": 1, "age_s": 20 * H, "command": "/bin/zsh -c " + repr(WAIT)}
        self.assertEqual(self.pids([p]), [])

    def test_protected_are_kept(self):
        for body in ("while pgrep -f queue_worker.py; do sleep 30; done",
                     "while pgrep -f nightly; do sleep 30; done"):
            self.assertEqual(self.pids([shell(100, body, age_h=48)]), [], body)

    def test_a_loop_running_real_work_is_kept(self):
        procs = [shell(100, "while true; do python3 scripts/x.py; sleep 60; done", age_h=30),
                 child(101, 100, "python3 scripts/x.py")]
        self.assertEqual(self.pids(procs), [])

    def test_long_running_processes_that_are_not_shells_are_kept(self):
        procs = [{"pid": 5, "ppid": 1, "age_s": 99 * H, "command": "python3 scripts/queue_worker.py"},
                 {"pid": 7, "ppid": 1, "age_s": 99 * H, "command": "sleep 100000"}]
        self.assertEqual(self.pids(procs), [])

    def test_etime(self):
        self.assertEqual(wr.etime_s("05:03"), 303)
        self.assertEqual(wr.etime_s("23:45:36"), 23 * H + 45 * 60 + 36)
        self.assertEqual(wr.etime_s("8-01:00:00"), 8 * 86400 + H)


class Reap(unittest.TestCase):
    def test_kills_by_pid_and_logs_each(self):
        killed = []
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "reaper.jsonl"
            lines = wr.reap(now=1000, procs=lambda: [shell(100, WAIT), shell(200, WAIT, age_h=1)],
                            kill=lambda pid, sig: killed.append((pid, sig)), log=log)
            recs = [json.loads(x) for x in log.read_text().splitlines()]
        self.assertEqual(killed, [(100, signal.SIGTERM)])
        self.assertEqual(len(lines), 1)
        self.assertEqual([(r["pid"], r["result"]) for r in recs], [(100, "killed")])

    def test_gone_process_is_skipped(self):
        def kill(pid, sig):
            raise ProcessLookupError
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(wr.reap(procs=lambda: [shell(100, WAIT)], kill=kill, log=Path(d) / "l"), [])


if __name__ == "__main__":
    unittest.main()
