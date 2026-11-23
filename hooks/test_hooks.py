#!/usr/bin/env python3
"""The lane hooks (admission_gate.py, lane_ledger.py, the shared _loop.py config) and waiter_guard.py.
The other hooks carry their own test_<hook>.py. Run: python3 hooks/test_hooks.py (or .claude/hooks/ once installed)"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _loop  # noqa: E402
import admission_gate  # noqa: E402
import lane_ledger  # noqa: E402,F401 - imported so a syntax error fails here too
import waiter_guard  # noqa: E402


class WaiterGuard(unittest.TestCase):
    def test(self):
        self.assertIsNotNone(waiter_guard.check('until ! pgrep -f "run_suite.py"; do sleep 10; done'))
        self.assertIsNotNone(waiter_guard.check("while pgrep -fl 'land.sh 12'; do sleep 5; done"))
        self.assertIsNone(waiter_guard.check("until ! pgrep -f '[r]un_suite.py'; do sleep 10; done"))
        self.assertIsNone(waiter_guard.check("pgrep -f run_suite.py"))


class Project(unittest.TestCase):
    """A throwaway project dir: CLAUDE_PROJECT_DIR points at it, so the config and the ledger are its own."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="loop-hooks-")
        os.makedirs(os.path.join(self.dir, ".loop"))
        self._env = {k: os.environ.get(k) for k in ("CLAUDE_PROJECT_DIR", "LANE_LEDGER", "LOOP_CONFIG")}
        os.environ["CLAUDE_PROJECT_DIR"] = self.dir
        os.environ.pop("LANE_LEDGER", None)
        os.environ.pop("LOOP_CONFIG", None)
        self._probes = (_loop.swap_used_gb, _loop.total_disk_gb, _loop.ram_gb, admission_gate.shutil.disk_usage)
        self.free, self.swap = 100e9, 1.0
        admission_gate.shutil.disk_usage = lambda _p: type("U", (), {"free": self.free, "total": 228e9})()
        _loop.swap_used_gb = lambda: self.swap
        _loop.total_disk_gb = lambda: 228.0
        _loop.ram_gb = lambda: 16.0

    def tearDown(self):
        _loop.swap_used_gb, _loop.total_disk_gb, _loop.ram_gb, admission_gate.shutil.disk_usage = self._probes
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def config(self, **sections):
        with open(os.path.join(self.dir, ".loop", "config.json"), "w") as fh:
            json.dump(sections, fh)

    def spawn(self, line, kind="general-purpose"):
        return {"prompt": "Do the thing.\n" + line, "subagent_type": kind, "description": "a lane"}

    def run_hook(self, script, payload):
        # The subprocess probes the real disk and swap; floors of 0 and 10^6 GB keep them out of the lane tests.
        return subprocess.run([sys.executable, os.path.join(HERE, script)], input=json.dumps(payload),
                              capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": self.dir})

    def no_floors(self, **lanes):
        self.config(lanes=lanes, resources={"min_free_disk_gb": 0, "max_swap_used_gb": 1e6, "scale_to_machine": False})


class AdmissionGate(Project):
    def test_no_lane_line_defaults_and_warns(self):
        self.assertIsNone(admission_gate.check(self.spawn("")))
        self.assertIn("feature lane", admission_gate.warn(self.spawn("")))
        self.no_floors()
        r = self.run_hook("admission_gate.py", {"tool_name": "Agent", "tool_input": self.spawn("")})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("systemMessage", r.stdout)

    def test_require_lane_line_blocks(self):
        self.config(lanes={"require_lane_line": True})
        self.assertIn("Lane:", admission_gate.check(self.spawn("")))
        self.assertIsNone(admission_gate.check(self.spawn("Lane: feature; Hotspot: api")))

    def test_read_only_and_none(self):
        self.assertIsNone(admission_gate.check(self.spawn("", kind="Explore")))
        self.assertIsNone(admission_gate.warn(self.spawn("Lane: none; Hotspot: none")))

    def test_caps_and_hotspots(self):
        lanes = [{"kind": "feature", "hotspots": ["api"], "updated": time.time()}]
        with open(os.path.join(self.dir, ".loop", "lanes.json"), "w") as fh:
            json.dump({"lanes": lanes}, fh)
        self.assertIn("hotspot api", admission_gate.check(self.spawn("Lane: feature; Hotspot: api")))
        self.assertIsNone(admission_gate.check(self.spawn("Lane: feature; Hotspot: ui")))
        self.assertIn("cap 0", admission_gate.check(self.spawn("Lane: research; Hotspot: ui")))
        with open(os.path.join(self.dir, ".loop", "lanes.json"), "w") as fh:
            json.dump({"lanes": lanes * 5}, fh)
        self.assertIn("cap 5", admission_gate.check(self.spawn("Lane: bug; Hotspot: ui")))

    def test_build_slot_budget(self):
        lanes = [{"kind": "feature", "hotspots": [], "updated": time.time(), "build": b} for b in (True, True, False)]
        with open(os.path.join(self.dir, ".loop", "lanes.json"), "w") as fh:
            json.dump({"lanes": lanes}, fh)
        heavy, light = "Lane: feature; Hotspot: ui\nNeeds: local (device)", "Lane: feature; Hotspot: ui\nNeeds: local (docs, no build)"
        self.assertIsNone(admission_gate.check(self.spawn(heavy)), "off by default")
        self.config(lanes={"max_build_helpers": 2})
        self.assertIn("build-slot budget", admission_gate.check(self.spawn(heavy)))
        self.assertIsNone(admission_gate.check(self.spawn(light)), "no build: not counted")
        self.assertIsNone(admission_gate.check(self.spawn("Lane: feature; Hotspot: ui")), "no Needs line: not counted")
        self.config(lanes={"max_build_helpers": 3})
        self.assertIsNone(admission_gate.check(self.spawn(heavy)))

    def test_owner_override_raises_one_kinds_cap(self):
        lanes = [{"kind": "bug", "hotspots": [f"h{i}"], "updated": time.time()} for i in range(2)]
        with open(os.path.join(self.dir, ".loop", "lanes.json"), "w") as fh:
            json.dump({"lanes": lanes}, fh)
        path = os.path.join(self.dir, ".loop", "lane_override.json")
        spawn = self.spawn("Lane: bug; Hotspot: z")
        self.assertIn("cap 1", admission_gate.check(spawn))
        for doc, ok in [({"kind": "bug", "max": 3, "until": time.time() + 600, "why": "launch week"}, True),
                        ({"kind": "bug", "max": 3, "until": time.time() - 1, "why": "x"}, False),   # expired
                        ({"kind": "feature", "max": 3, "until": time.time() + 600}, False),         # another kind
                        ({"kind": "bug", "max": 2, "until": time.time() + 600}, False),            # still full
                        ({"kind": "bug", "max": 99, "until": time.time() + 600}, False)]:          # capped at the ceiling: 4 > 2 lanes
            with open(path, "w") as fh:
                json.dump(doc, fh)
            msg = admission_gate.check(spawn)
            if doc["max"] == 99:
                self.assertIsNone(msg)
            else:
                self.assertEqual(msg is None, ok, (doc, msg))
        with open(path, "w") as fh:
            fh.write("{")
        self.assertIn("cap 1", admission_gate.check(spawn), "unreadable: the normal cap")

    def test_resource_floors_default_and_config(self):
        self.free = 14e9
        self.assertIn("free disk, floor 15", admission_gate.check(self.spawn("Lane: feature; Hotspot: ui")))
        self.config(resources={"min_free_disk_gb": 10})
        self.assertIsNone(admission_gate.check(self.spawn("Lane: feature; Hotspot: ui")))
        self.free, self.swap = 100e9, 7.5
        self.assertIn("swap", admission_gate.check(self.spawn("Lane: feature; Hotspot: ui")))
        self.config(resources={"max_swap_used_gb": 8})
        self.assertIsNone(admission_gate.check(self.spawn("Lane: feature; Hotspot: ui")))

    def test_floors_scale_to_the_machine(self):
        cfg = _loop.config()
        self.assertEqual(_loop.floors(cfg, 228, 16), (15, 6))     # the machine the defaults came from: unchanged
        self.assertEqual(_loop.floors(cfg, 2000, 128), (15, 6))   # a bigger one keeps them
        self.assertEqual(_loop.floors(cfg, 120, 8), (12, 3))      # a smaller one gets lower values
        cfg["resources"]["scale_to_machine"] = False
        self.assertEqual(_loop.floors(cfg, 120, 8), (15, 6))

    def test_finish_before_start(self):
        saved = admission_gate.open_ready_prs
        try:
            admission_gate.open_ready_prs = lambda: [100, 101, 102, 103, 104, 105]
            self.assertIsNone(admission_gate.check(self.spawn("Lane: feature; Hotspot: ui")), "off by default")
            self.config(finish_before_start={"max_waiting_prs": 5})
            msg = admission_gate.check(self.spawn("Lane: feature; Hotspot: ui"))
            self.assertIn("6 pull requests wait to land", msg)
            self.assertIn("#100", msg)
            self.assertIsNone(admission_gate.check(self.spawn("Lane: bug; Hotspot: ui")))
            self.assertIsNone(admission_gate.check(self.spawn("Lane: process; Hotspot: docs")))
            admission_gate.open_ready_prs = lambda: [100, 101, 102, 103, 104]
            self.assertIsNone(admission_gate.check(self.spawn("Lane: feature; Hotspot: ui")))
            admission_gate.open_ready_prs = lambda: None
            self.assertIsNone(admission_gate.check(self.spawn("Lane: feature; Hotspot: ui")), "unreadable: no block")
        finally:
            admission_gate.open_ready_prs = saved

    def test_bad_config_fails_closed(self):
        with open(os.path.join(self.dir, ".loop", "config.json"), "w") as fh:
            fh.write("{not json")
        r = self.run_hook("admission_gate.py", {"tool_name": "Agent", "tool_input": self.spawn("Lane: bug; Hotspot: x")})
        self.assertEqual(r.returncode, 2)
        self.assertIn("blocked for safety", r.stderr)


class LaneLedger(Project):
    def setUp(self):
        super().setUp()
        self.no_floors()

    def post(self, line, agent_id=None, session="s1", status="async_launched"):
        resp = {"status": status, **({"agentId": agent_id} if agent_id else {})}
        return self.run_hook("lane_ledger.py", {"hook_event_name": "PostToolUse", "tool_name": "Agent",
                                                "session_id": session, "tool_input": self.spawn(line),
                                                "tool_response": resp})

    def stop(self, agent_id, session="s1", agent_type="general-purpose"):
        return self.run_hook("lane_ledger.py", {"hook_event_name": "SubagentStop", "session_id": session,
                                                "agent_id": agent_id, "agent_type": agent_type})

    def gate(self, line):
        return self.run_hook("admission_gate.py", {"tool_name": "Agent", "tool_input": self.spawn(line)})

    def lanes(self):
        return _loop.read_ledger()

    def test_the_cap_trips_end_to_end(self):
        """Spawns recorded by the PostToolUse hook fill the cap; the gate then blocks; a SubagentStop frees a slot."""
        self.no_floors(total=3, caps={"feature": 3})
        for i in range(3):
            self.assertEqual(self.gate(f"Lane: feature; Hotspot: area{i}").returncode, 0)
            self.assertEqual(self.post(f"Lane: feature; Hotspot: area{i}", agent_id=f"a{i}").returncode, 0)
        self.assertEqual(len(self.lanes()), 3)
        r = self.gate("Lane: feature; Hotspot: area9")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("3 lanes running, cap 3", r.stderr)
        self.assertEqual(self.stop("a1").returncode, 0)
        self.assertEqual([e["agent_id"] for e in self.lanes()], ["a0", "a2"])
        self.assertEqual(self.gate("Lane: feature; Hotspot: area9").returncode, 0)

    def test_the_default_caps_trip(self):
        """With no config at all: four feature lanes fill the feature cap, a fifth is refused."""
        for i in range(4):
            self.post(f"Lane: feature; Hotspot: f{i}", agent_id=f"f{i}")
        cfg = _loop.config(os.path.join(self.dir, "none.json"))
        self.assertIn("4 feature lanes running, cap 4", admission_gate.check(self.spawn("Lane: feature; Hotspot: q"), cfg))
        self.assertIsNone(admission_gate.check(self.spawn("Lane: bug; Hotspot: q"), cfg))

    def test_hotspot_held_until_stop(self):
        self.post("Lane: feature; Hotspot: checkout", agent_id="a1")
        self.assertEqual(self.gate("Lane: bug; Hotspot: checkout").returncode, 2)
        self.stop("a1")
        self.assertEqual(self.gate("Lane: bug; Hotspot: checkout").returncode, 0)

    def test_no_lane_line_records_the_default_kind(self):
        self.post("", agent_id="a1")
        self.assertEqual([(e["kind"], e["hotspots"]) for e in self.lanes()], [("feature", [])])

    def test_not_recorded(self):
        self.post("Lane: none; Hotspot: none", agent_id="a1")
        self.run_hook("lane_ledger.py", {"hook_event_name": "PostToolUse", "tool_name": "Agent", "session_id": "s1",
                                         "tool_input": self.spawn("", kind="Explore"), "tool_response": {}})
        self.post("Lane: feature; Hotspot: x", agent_id="a2", status="completed")  # a foreground lane, already over
        self.assertEqual(self.lanes(), [])

    def test_stop_before_post_is_remembered(self):
        """A foreground subagent's SubagentStop fires before the spawn's PostToolUse."""
        self.stop("a7")
        self.post("Lane: feature; Hotspot: x", agent_id="a7", status="")
        self.assertEqual(self.lanes(), [])

    def test_no_id_falls_back_to_the_oldest_of_the_session(self):
        self.post("Lane: feature; Hotspot: x")
        self.post("Lane: feature; Hotspot: y")
        self.post("Lane: feature; Hotspot: z", session="other")
        self.stop("unknown-id")
        self.assertEqual(sorted(e["hotspots"][0] for e in self.lanes()), ["y", "z"])
        self.stop("unknown-id", agent_type="Explore")  # a read-only stop never removes a lane
        self.assertEqual(len(self.lanes()), 2)

    def test_ttl_ends_a_lane_that_never_stopped(self):
        self.no_floors(total=1, caps={"feature": 1}, stale_hours=1)
        self.post("Lane: feature; Hotspot: x", agent_id="a1")
        self.assertEqual(self.gate("Lane: feature; Hotspot: y").returncode, 2)
        doc = _loop.read_doc()
        doc["lanes"][0]["updated"] = time.time() - 2 * 3600
        with open(_loop.ledger_path(), "w") as fh:
            json.dump(doc, fh)
        self.assertEqual(self.gate("Lane: feature; Hotspot: y").returncode, 0)
        self.post("Lane: feature; Hotspot: y", agent_id="a2")
        self.assertEqual([e["agent_id"] for e in self.lanes()], ["a2"])  # the stale entry is dropped on the next write

    def test_cli_and_errors(self):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": self.dir}
        self.post("Lane: feature; Hotspot: x", agent_id="a1")
        out = subprocess.run([sys.executable, os.path.join(HERE, "lane_ledger.py"), "list"], capture_output=True,
                             text=True, env=env).stdout
        self.assertIn("1 running (cap 5)", out)
        subprocess.run([sys.executable, os.path.join(HERE, "lane_ledger.py"), "end", "a1"], env=env, check=True)
        self.assertEqual(self.lanes(), [])
        r = subprocess.run([sys.executable, os.path.join(HERE, "lane_ledger.py")], input="{", capture_output=True,
                           text=True, env=env)
        self.assertEqual(r.returncode, 1)  # fails open: a non-blocking error


class Settings(unittest.TestCase):
    def test_installed_settings_wire_the_ledger(self):
        path = os.path.join(HERE, "..", "settings.json")
        if not os.path.exists(path):
            self.skipTest("not installed in a project (bootstrap_kit.py)")
        hooks = json.load(open(path))["hooks"]
        post = [e for e in hooks.get("PostToolUse", []) if any("lane_ledger.py" in h["command"] for h in e["hooks"])]
        stop = [e for e in hooks.get("SubagentStop", []) if any("lane_ledger.py" in h["command"] for h in e["hooks"])]
        self.assertEqual([e.get("matcher") for e in post], ["Agent|Task"])
        self.assertEqual(len(stop), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
