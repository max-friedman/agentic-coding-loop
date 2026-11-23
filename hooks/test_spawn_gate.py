#!/usr/bin/env python3
"""spawn_gate.py: every check is opt-in; turned on, a spawn needs a model and the helper rules.
python3 .claude/hooks/test_spawn_gate.py"""

import json, os, subprocess as sp, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _loop  # noqa: E402
import spawn_gate  # noqa: E402

# Cloud first: these tests describe a local session (the hook lets every spawn from a cloud session through).
os.environ.pop("CLAUDE_CODE_REMOTE", None)

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


ON = _loop.config()
ON["spawn_gate"].update(require_model=True, require_rules=True, require_no_notify=True)
CLOUD = _loop.config()
CLOUD["spawn_gate"].update(require_rules=True, require_local_need=True)
OFF = _loop.DEFAULTS
PROJECT = tempfile.mkdtemp(prefix="spawn-gate-test-")
os.makedirs(os.path.join(PROJECT, ".loop"))
with open(os.path.join(PROJECT, ".loop", "config.json"), "w") as fh:
    json.dump({"spawn_gate": ON["spawn_gate"]}, fh)


def hook(tool, inp, project=PROJECT):
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "spawn_gate.py")],
               input=json.dumps({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": inp}),
               capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": project})
    return r, time.time() - t


RULES = ("Helper for the coordinator. Read CLAUDE.md and docs/process/PLAYBOOK.md. Rules: never "
         "edit the live checkout; run `python3 scripts/prelanding.py` before handing back. Task: build X.")
NO_NOTIFY = ("Do not send any notifications or push messages to the owner (no push notification, no chat, no "
             "email); report only in your final answer, which the coordinator reads.")


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
for name, (tool, inp) in {"no model": agent(model=None), "no rules": agent("Build X."),
                          "a cloud lane with nothing": trigger("create", "Build X.", model=None)}.items():
    check(f"off by default: allows {name}", spawn_gate.check(tool, inp, OFF) is None)
allowed = {
    "a compliant build helper": agent(),
    "the older tool name Task": agent(tool="Task"),
    "the PLAYBOOK and prelanding": agent("Follow docs/process/PLAYBOOK.md; run prelanding before hand-back."),
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
    "a missing playbook mention": (agent("Build X. Run python3 scripts/prelanding.py before handing back."),
                                   ["helper-rules.md", "playbook"]),
    "a missing prelanding line": (agent("Read the PLAYBOOK. Build X."), ["prelanding"]),
    "an Explore type still needs a model": (agent("Find it.", model=None, kind="Explore"), ["model"]),
    "a general-purpose type with no rules": (agent("Build X.", kind="general-purpose"), ["helper-rules.md", "prelanding"]),
    "a cloud trigger without the no-notify line": (trigger("create", RULES), ["no notifications"]),
    "a cloud trigger without a model": (trigger("create", RULES + " " + NO_NOTIFY, model=None), ["model"]),
    "a cloud trigger without the rules": (trigger("create", "Build X. " + NO_NOTIFY), ["prelanding"]),
    "a run that carries a prompt without the rules": (trigger("run", "Build Y."), ["prelanding", "no notifications"]),
}
for name, (tool, inp) in allowed.items():
    msg = spawn_gate.check(tool, inp, ON)
    check(f"allows: {name}", msg is None, msg)
for name, ((tool, inp), wants) in blocked.items():
    msg = spawn_gate.check(tool, inp, ON) or ""
    check(f"blocks: {name} (says {', '.join(wants)})", msg and all(w in msg for w in wants), msg)
msg = spawn_gate.check(*agent(model=None), ON) or ""
check("only what's missing is listed", "helper rules" not in msg, msg)

# Cloud first: a local writing helper declares `Needs: local`, or goes to a cloud lane (opt-in).
LOCAL = RULES
WITH = RULES + "\nNeeds: local (device run)."
check("cloud first is off by default", spawn_gate.check(*agent(LOCAL), ON) is None)
msg = spawn_gate.check(*agent(LOCAL), CLOUD) or ""
check("blocks: a local helper without `Needs: local`, with the cloud hint",
      "Needs: local" in msg and "cloud lane" in msg and "require_local_need" in msg, msg)
msg = spawn_gate.check(*agent("Build X."), CLOUD) or ""
check("a spawn missing the rules also lists the Needs line", "helper rules" in msg and "Needs: local" in msg, msg)
for name, prompt in {"Needs: cloud": LOCAL + "\nNeeds: cloud", "Needs: locally": LOCAL + "\nNeeds: locally",
                     "a passing mention": LOCAL + " Don't add Needs: local to this one.",
                     "mid-line": LOCAL + " Lane: process; Needs: local (device)"}.items():
    check(f"blocks: {name} isn't Needs: local", "cloud first" in (spawn_gate.check(*agent(prompt), CLOUD) or ""), name)
for name, inp in {"the line": agent(WITH), "markup": agent(LOCAL + "\n- **Needs:** `Local` (device)"),
                  "a read-only prompt": agent("Read-only: find X.", model="haiku"),
                  "an Explore type": agent("Find X.", model="haiku", kind="Explore"),
                  "a fork": agent("carry on", model=None, kind="fork"),
                  "a cloud lane (RemoteTrigger)": trigger("create", LOCAL + " " + NO_NOTIFY),
                  "isolation remote": ("Agent", {**agent(LOCAL)[1], "isolation": "remote"})}.items():
    check(f"cloud first allows {name}", spawn_gate.check(*inp, CLOUD) is None, spawn_gate.check(*inp, CLOUD))
os.environ["CLAUDE_CODE_REMOTE"] = "true"
check("cloud first doesn't gate a spawn from a cloud session", spawn_gate.check(*agent(LOCAL), CLOUD) is None)
os.environ.pop("CLAUDE_CODE_REMOTE")
check("uses_build: Needs: local counts unless it says no build",
      _loop.uses_build("x\nNeeds: local (build)") and _loop.uses_build("needs: local") and not _loop.uses_build("Build X.")
      and not _loop.uses_build("Needs: local (live service, no build)") and not _loop.uses_build("Needs: cloud")
      and _loop.uses_build("Needs: local (device)\nlater: no build talk on another line"))

r, dt = hook(*agent(model=None))
check("missing model (config on): exit 2, names the knob",
      r.returncode == 2 and "require_model" in r.stderr and ".loop/config.json" in r.stderr, (r.returncode, r.stderr))
r, _ = hook(*agent(model=None), project=tempfile.mkdtemp())
check("missing model, no config file: exit 0", r.returncode == 0, r.stderr)
r, _ = hook(*trigger("create", RULES))
check("cloud lane without no-notify (config on): exit 2", r.returncode == 2 and "require_no_notify" in r.stderr, r.stderr)
r, _ = hook(*agent())
check("a compliant spawn: exit 0, no output", r.returncode == 0 and not r.stdout and not r.stderr, r.stderr)
r = sp.run([sys.executable, os.path.join(HERE, "spawn_gate.py")], input="{", capture_output=True, text=True)
check("broken input: fails open (exit 1)", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))
r, _ = hook("Agent", "not a dict")
check("odd tool_input: fails open (exit 1)", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))
SETTINGS = os.path.join(HERE, "..", "settings.json")
if os.path.exists(SETTINGS):  # installed in a project (bootstrap_kit.py), not in the loop repo's hooks/
    settings = json.load(open(SETTINGS))
    matchers = [e["matcher"] for e in settings["hooks"]["PreToolUse"] if any("spawn_gate.py" in h["command"] for h in e["hooks"])]
    check("settings.json runs it on Agent|Task|RemoteTrigger", matchers == ["Agent|Task|RemoteTrigger"], matchers)
t = time.time()
for _ in range(200):
    spawn_gate.check(*trigger("create", RULES * 20 + NO_NOTIFY), ON)
per = (time.time() - t) / 200
check(f"fast: {per * 1000:.2f} ms a check (< 10 ms); {dt * 1000:.0f} ms with python startup (< 1 s)", per < 0.01 and dt < 1, dt)

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
