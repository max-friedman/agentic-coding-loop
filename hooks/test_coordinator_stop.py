#!/usr/bin/env python3
"""coordinator_stop.py (and coordinator_session.py): the coordinator's Stop hook.
python3 .claude/hooks/test_coordinator_stop.py"""

import json, os, subprocess as sp, sys, tempfile, time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _loop  # noqa: E402
import coordinator_session as ms  # noqa: E402
import coordinator_stop as m  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


tmp = Path(tempfile.mkdtemp(prefix="coordinator-stop-test-"))
FB = tmp / ".loop"
MARK, STATE = FB / "coordinator_session.json", FB / "coordinator_stop.json"
FB.mkdir(parents=True, exist_ok=True)
(FB / "config.json").write_text(json.dumps({"coordinator": {"require_checks": True}}))
DEFAULT_CFG = _loop.config(tmp / "no-config.json")
CFG = _loop._merge(DEFAULT_CFG, {"coordinator": {"require_checks": True}})
COOLDOWN_S = CFG["coordinator"]["cooldown_minutes"] * 60
SID = "11111111-2222-3333-4444-555555555555"
MONITOR = {"id": "t1", "type": "monitor", "status": "running", "description": "events: the coordinator's event stream"}
CRON = {"id": "c1", "schedule": "17 */2 * * *", "recurring": True, "prompt": "Coordinator check-in: touch the heartbeat"}


def inp(**kw):
    d = {"session_id": SID, "hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": "done",
         "background_tasks": [MONITOR], "session_crons": [CRON]}
    d.update(kw)
    return d


def fresh():
    for p in (MARK, STATE):
        if p.exists():
            p.unlink()
    ms.register(SID, MARK)


def decide(d, now=None, cfg=CFG):
    return m.decide(d, now or time.time(), MARK, STATE, cfg)


def hook(d, home=tmp, raw=None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(home))
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "coordinator_stop.py")], input=raw if raw is not None else json.dumps(d),
               capture_output=True, text=True, env=env)
    return r, time.time() - t


print("coordinator_stop.py")
fresh()
check("opt-in: off by default, nothing blocks", DEFAULT_CFG["coordinator"]["require_checks"] is False and decide(inp(background_tasks=[], session_crons=[]), cfg=DEFAULT_CFG) is None)
st = json.loads(STATE.read_text())
check("opt-in off: the turn end is still recorded (the watchdog reads it)", st.get("session_id") == SID
      and st.get("last", {}).get("at"), st)
check("all armed: the turn ends", decide(inp()) is None)
why = decide(inp(background_tasks=[]))
check("no watch: blocks, says how to restart it", why and "quiet watch" in why and "run_in_background" in why, why)
check("no watch: doesn't mention the cron", why and "CronCreate" not in why, why)
fresh()
why = decide(inp(session_crons=[]))
check("no check-in cron: blocks with the CronCreate call", why and "CronCreate(" in why and "recurring=true" in why, why)
fresh()
why = decide(inp(background_tasks=[], session_crons=[]))
check("both gone: one message names both", why and "quiet watch" in why and "CronCreate(" in why, why)

fresh()
done = dict(MONITOR, status="completed")
check("a finished events task doesn't count", decide(inp(background_tasks=[done])) is not None)
fresh()
shell = {"id": "t2", "type": "shell", "status": "running", "description": "events", "command": "bash /scratch/events_loop.sh"}
check("a running task whose command matches the pattern counts", decide(inp(background_tasks=[shell])) is None)
fresh()
other = {"id": "t3", "type": "monitor", "status": "running", "description": "CI checks for #12"}
check("another Monitor doesn't count", decide(inp(background_tasks=[other])) is not None)
fresh()
once = dict(CRON, recurring=False)
check("a one-shot check-in doesn't count", decide(inp(session_crons=[once])) is not None)
fresh()
lane = dict(CRON, prompt="build the release notes")
check("a recurring cron that isn't a check-in doesn't count", decide(inp(session_crons=[lane])) is not None)

fresh()
check("stop_hook_active: never blocks", decide(inp(background_tasks=[], stop_hook_active=True)) is None)
fresh()
now = time.time()
check("first time: blocks", decide(inp(background_tasks=[]), now) is not None)
check("again within the cooldown: lets the turn end", decide(inp(background_tasks=[]), now + 60) is None)
check("after the cooldown: blocks again", decide(inp(background_tasks=[]), now + COOLDOWN_S + 1) is not None)
why = decide(inp(background_tasks=[], session_crons=[]), now + COOLDOWN_S + 2)
check("the cooldown is per condition (the cron still blocks)", why and "CronCreate(" in why and "quiet watch" not in why, why)

fresh()
check("a subagent of the coordinator (agent_id): never blocked", decide(inp(background_tasks=[], agent_id="a1")) is None)
check("another session: never blocked", decide(inp(background_tasks=[], session_id="other")) is None)
MARK.unlink()
check("no marker: never blocked", decide(inp(background_tasks=[])) is None)
fresh()
d = inp()
del d["background_tasks"], d["session_crons"]
check("arrays missing (registry unreachable): no evidence, no block", decide(d) is None)

fresh()
own = _loop._merge(CFG, {"coordinator": {"monitor_command": "Monitor(command='bash my_events.sh')",
                                         "monitor_pattern": "my_events"}})
why = decide(inp(background_tasks=[]), cfg=own)
check("the config's monitor_command is quoted", why and "bash my_events.sh" in why, why)
fresh()
check("the config's monitor_pattern decides what counts", decide(inp(), cfg=own) is not None)
fresh()
mk = json.loads(MARK.read_text())
mk["note"] = "kept"
MARK.write_text(json.dumps(mk))
check("register keeps the marker's own fields", ms.register(SID, MARK).get("note") == "kept", MARK.read_text())

fresh()
decide(inp(session_crons=[]))
last = json.loads(STATE.read_text()).get("last", {})
check("the turn end's view is saved", last.get("monitor") is True and last.get("checkin") is False, last)

fresh()
r, dt = hook(inp(background_tasks=[]))
out = json.loads(r.stdout or "{}")
check("hook: exit 0, decision block on stdout", r.returncode == 0 and out.get("decision") == "block" and "quiet watch" in out.get("reason", ""),
      (r.returncode, r.stdout, r.stderr))
r, _ = hook(inp())
check("hook: armed, exit 0 and nothing printed", r.returncode == 0 and not r.stdout, (r.returncode, r.stdout))
r, _ = hook(None, raw="{")
check("broken input: fails open (exit 1), never blocks", r.returncode == 1 and "hook error" in r.stderr and not r.stdout, (r.returncode, r.stderr))
check(f"fast: {dt * 1000:.0f} ms with python startup (< 1 s)", dt < 1, dt)

env = dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp), CLAUDE_CODE_SESSION_ID="abc-123")
r = sp.run([sys.executable, os.path.join(HERE, "coordinator_session.py"), "register"], capture_output=True, text=True, env=env)
check("coordinator_session.py register: takes $CLAUDE_CODE_SESSION_ID", r.returncode == 0 and ms.marker(MARK).get("session_id") == "abc-123", (r.stdout, r.stderr))
env.pop("CLAUDE_CODE_SESSION_ID")
r = sp.run([sys.executable, os.path.join(HERE, "coordinator_session.py"), "register"], capture_output=True, text=True, env=env)
check("register without a session id: exit 1, says --session-id", r.returncode == 1 and "--session-id" in r.stderr, r.stderr)
r = sp.run([sys.executable, os.path.join(HERE, "coordinator_session.py"), "register", "--session-id", "xyz"], capture_output=True, text=True, env=env)
check("register --session-id", r.returncode == 0 and ms.marker(MARK).get("session_id") == "xyz", r.stderr)

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
