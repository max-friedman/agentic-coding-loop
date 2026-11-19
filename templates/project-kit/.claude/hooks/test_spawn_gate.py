#!/usr/bin/env python3
"""spawn_gate.py: a spawn needs a model and the helper rules.  python3 .claude/hooks/test_spawn_gate.py"""

# The validation gate runs this file when one of these paths changes (scripts/validate.py reads GATE_COVERS).
# The project's Claude Code hooks (.claude/hooks/README.md): each hook's test, on any change there.
GATE_COVERS = (".claude/hooks/", ".claude/settings.json")

import json, os, subprocess as sp, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spawn_gate  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


def hook(tool, inp):
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "spawn_gate.py")],
               input=json.dumps({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": inp}),
               capture_output=True, text=True)
    return r, time.time() - t


RULES = ("Helper for the master. Read CLAUDE.md and docs/process/PLAYBOOK.md (its \"Master checklist\"). Rules: never "
         "edit the live checkout; run `python3 scripts/prelanding.py` before handing back. Task: build X.")
NO_NOTIFY = ("Do not send any notifications or push messages to the owner (no push notification, no chat, no "
             "email); report only in your final answer, which the master reads.")


def agent(prompt=RULES, model="opus", kind=None, tool="Agent"):
    inp = {"description": "build X", "prompt": prompt}
    if model:
        inp["model"] = model
    if kind:
        inp["subagent_type"] = kind
    return tool, inp


def trigger(action, prompt=None, model="claude-sonnet-5-5"):
    inp = {"action": action}
    if action in ("get", "run", "update"):
        inp["trigger_id"] = "trig_test"
    if prompt is not None:
        ccr = {"session_context": {"allowed_tools": ["Bash", "Read"]},
               "events": [{"data": {"message": {"content": prompt}}}]}
        if model:
            ccr["session_context"]["model"] = model
        inp["body"] = {"name": "lane", "job_config": {"ccr": ccr}}
    return "RemoteTrigger", inp


print("spawn_gate.py")
allowed = {
    "a compliant build helper": agent(),
    "the older tool name Task": agent(tool="Task"),
    "PLAYBOOK instead of Master checklist": agent("Follow docs/process/PLAYBOOK.md; run prelanding before hand-back."),
    "a pointer to helper-rules.md instead of the list": agent("Read docs/process/helper-rules.md and follow every rule in it. Lane: process; Hotspot: none. Task: X."),
    "a read-only review, no rules": agent("Blind review: do NOT read any other files. Rate this card.", model="sonnet"),
    "a read-only research prompt": agent("Read-only: find where the feed renders cards.", model="haiku"),
    "an Explore type, no rules": agent("Find the wip limit code.", model="haiku", kind="Explore"),
    "a Plan type, no rules": agent("Plan the refactor.", model="opus", kind="Plan"),
    "a fork (inherits model and context)": agent("carry on", model=None, kind="fork"),
    "a compliant cloud lane": trigger("create", RULES + " " + NO_NOTIFY),
    "RemoteTrigger list": ("RemoteTrigger", {"action": "list"}),
    "RemoteTrigger get": trigger("get"),
    "RemoteTrigger run of an existing trigger": trigger("run"),
    "RemoteTrigger update": trigger("update", "anything"),
    "another tool": ("Bash", {"command": "echo hi"}),
}
blocked = {
    "a missing model": (agent(model=None), ["model"]),
    "an empty model": (agent(model=" "), ["model"]),
    "a missing checklist mention": (agent("Build X. Run python3 scripts/prelanding.py before handing back."),
                                    ["Master checklist"]),
    "a missing prelanding line": (agent("Read the PLAYBOOK's Master checklist. Build X."), ["prelanding"]),
    "an Explore type still needs a model": (agent("Find it.", model=None, kind="Explore"), ["model"]),
    "a general-purpose type with no rules": (agent("Build X.", kind="general-purpose"), ["Master checklist", "prelanding"]),
    "a cloud trigger without the no-notify line": (trigger("create", RULES), ["no-notify"]),
    "a cloud trigger without a model": (trigger("create", RULES + " " + NO_NOTIFY, model=None), ["model"]),
    "a cloud trigger without the rules": (trigger("create", "Build X. " + NO_NOTIFY), ["prelanding"]),
    "a run that carries a prompt without the rules": (trigger("run", "Build Y."), ["prelanding", "no-notify"]),
}
for name, (tool, inp) in allowed.items():
    msg = spawn_gate.check(tool, inp)
    check(f"allows: {name}", msg is None, msg)
for name, ((tool, inp), wants) in blocked.items():
    msg = spawn_gate.check(tool, inp) or ""
    check(f"blocks: {name} (says {', '.join(wants)})", msg and all(w in msg for w in wants), msg)
msg = spawn_gate.check(*agent(model=None)) or ""
check("only what's missing is listed", "prelanding.py` before" not in msg, msg)

r, dt = hook(*agent(model=None))
check("missing model: exit 2, points to the PLAYBOOK's spawning section",
      r.returncode == 2 and "#spawning-a-helper" in r.stderr and "model" in r.stderr, (r.returncode, r.stderr))
r, _ = hook(*trigger("create", RULES))
check("cloud lane without no-notify: exit 2, says Cloud steering", r.returncode == 2 and "cloud-steering" in r.stderr, r.stderr)
r, _ = hook(*agent())
check("a compliant spawn: exit 0, no output", r.returncode == 0 and not r.stdout and not r.stderr, r.stderr)
r = sp.run([sys.executable, os.path.join(HERE, "spawn_gate.py")], input="{", capture_output=True, text=True)
check("broken input: fails open (exit 1)", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))
r, _ = hook("Agent", "not a dict")
check("odd tool_input: fails open (exit 1)", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))
settings = json.load(open(os.path.join(HERE, "..", "settings.json")))
matchers = [e["matcher"] for e in settings["hooks"]["PreToolUse"] if any("spawn_gate.py" in h["command"] for h in e["hooks"])]
check("settings.json runs it on Agent|Task|RemoteTrigger", matchers == ["Agent|Task|RemoteTrigger"], matchers)
t = time.time()
for _ in range(200):
    spawn_gate.check(*trigger("create", RULES * 20 + NO_NOTIFY))
per = (time.time() - t) / 200
check(f"fast: {per * 1000:.2f} ms a check (< 10 ms); {dt * 1000:.0f} ms with python startup (< 1 s)", per < 0.01 and dt < 1, dt)

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
