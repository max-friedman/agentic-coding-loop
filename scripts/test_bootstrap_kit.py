#!/usr/bin/env python3
"""bootstrap_kit.py: the install is safe on a real repository.  python3 scripts/test_bootstrap_kit.py"""
import json
import os
import subprocess as sp
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bootstrap_kit as bk  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ok    " if ok else "  FAIL  ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


def repo(tmp, name):
    d = Path(tmp) / name
    d.mkdir()
    sp.run(["git", "init", "-q", str(d)], check=True)
    return d


def run(*args):
    return sp.run([sys.executable, str(HERE / "bootstrap_kit.py"), *map(str, args)], capture_output=True, text=True)


def snapshot(d):
    return {str(p.relative_to(d)): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file() and ".git" not in p.parts}


MINE = {"type": "command", "command": "bash my_own_check.sh", "timeout": 9}
EXISTING = {
    "permissions": {"allow": ["Bash(ls:*)"]},
    "env": {"LANE_LEDGER": "custom/lanes.json", "KEEP": "1"},
    "hooks": {
        "PreToolUse": [{"matcher": "Bash", "hooks": [MINE]}, {"matcher": "Read", "hooks": [MINE]}],
        "Notification": [{"hooks": [MINE]}],
    },
}

with tempfile.TemporaryDirectory() as tmp:
    print("a fresh repository")
    fresh = repo(tmp, "fresh")
    r = run(fresh, "--dry-run")
    check("dry-run exits 0 and says it wrote nothing", r.returncode == 0 and "DRY RUN" in r.stdout, r.stderr)
    check("dry-run writes nothing", snapshot(fresh) == {}, list(snapshot(fresh))[:3])
    check("dry-run lists what would be written", "would write  .claude/hooks/gh_rules.py" in r.stdout, r.stdout[:300])
    r = run(fresh)
    check("install exits 0", r.returncode == 0, r.stderr)
    tests = [n for n in snapshot(fresh) if Path(n).name.startswith("test_")]
    check("no test_*.py is copied into the target", not tests, tests)
    check("hooks and settings are installed", (fresh / ".claude/hooks/gh_rules.py").exists() and (fresh / ".claude/settings.json").exists())
    cfg = json.loads((fresh / ".loop/config.json").read_text())
    check("the opinionated hooks are off in the written config",
          cfg["gh_rules"]["block_pr_merge"] is False and cfg["coordinator"]["require_checks"] is False, cfg.get("gh_rules"))
    before = snapshot(fresh)
    r = run(fresh)
    check("a second run changes nothing", r.returncode == 0 and snapshot(fresh) == before)

    print("an existing .claude/settings.json")
    old = repo(tmp, "old")
    (old / ".claude").mkdir()
    sf = old / ".claude/settings.json"
    sf.write_text(json.dumps(EXISTING, indent=4))
    original = sf.read_bytes()
    r = run(old, "--dry-run")
    check("dry-run names the merge and leaves the file alone", "merged into .claude/settings.json" in r.stdout and sf.read_bytes() == original, r.stdout)
    r = run(old)
    check("install exits 0", r.returncode == 0, r.stderr)
    got = json.loads(sf.read_text())
    check("unrelated settings survive", got["permissions"] == EXISTING["permissions"] and got["env"]["KEEP"] == "1")
    check("an existing env value is not overridden", got["env"]["LANE_LEDGER"] == "custom/lanes.json", got["env"])
    check("a missing env key is added", "LOOP_LIVE_CHECKOUT" in got["env"])
    pre = got["hooks"]["PreToolUse"]
    bash = next(e for e in pre if e["matcher"] == "Bash")
    check("the project's own hook keeps its place, first", bash["hooks"][0] == MINE, bash["hooks"][:2])
    check("the kit's Bash hooks were added to that matcher", any("git_rules.py" in h["command"] for h in bash["hooks"]))
    check("the project's other matchers survive", next(e for e in pre if e["matcher"] == "Read")["hooks"] == [MINE])
    check("a matcher the project lacked is added", any(e["matcher"] == "Agent|Task|RemoteTrigger" for e in pre))
    check("an unrelated event survives", got["hooks"]["Notification"] == EXISTING["hooks"]["Notification"])
    check("Stop and SessionStart are added", "Stop" in got["hooks"] and "SessionStart" in got["hooks"])
    backups = list((old / ".claude").glob("settings.json.bak-*"))
    check("a backup of the original is kept", len(backups) == 1 and backups[0].read_bytes() == original, backups)
    merged_once = sf.read_bytes()
    run(old)
    cmds = [h["command"] for h in next(e for e in json.loads(sf.read_text())["hooks"]["PreToolUse"] if e["matcher"] == "Bash")["hooks"]]
    check("running again adds no duplicate hook", sf.read_bytes() == merged_once and len(cmds) == len(set(cmds)), cmds)

    print("a settings file that can't be merged")
    for label, text in (("not JSON", "{not json"), ("hooks is a list", '{"hooks": []}'), ("an event is not a list", '{"hooks": {"Stop": 3}}')):
        bad = repo(tmp, "bad-" + label.replace(" ", "-"))
        (bad / ".claude").mkdir()
        (bad / ".claude/settings.json").write_text(text)
        r = run(bad)
        check(f"{label}: stops loudly (exit 3, STOPPED on stderr)", r.returncode == 3 and "STOPPED" in r.stderr and "NOT" in r.stderr, (r.returncode, r.stderr))
        check(f"{label}: the file is untouched and nothing else installed",
              (bad / ".claude/settings.json").read_text() == text and set(snapshot(bad)) == {".claude/settings.json"}, list(snapshot(bad))[:4])

    print("CLAUDE.md")
    cm = repo(tmp, "claudemd")
    (cm / "CLAUDE.md").write_text("# Mine\nkeep this\n")
    r = run(cm)
    check("an existing CLAUDE.md is not touched; the skeleton goes to CLAUDE.loop.md",
          (cm / "CLAUDE.md").read_text() == "# Mine\nkeep this\n" and (cm / "CLAUDE.loop.md").exists(), r.stdout)
    r = run(cm, "--force")
    text = (cm / "CLAUDE.md").read_text()
    check("--force appends a marked section and keeps the original", text.startswith("# Mine\nkeep this\n") and bk.MARK_BEGIN in text and bk.MARK_END in text, text[:200])
    run(cm, "--force")
    check("--force again replaces the section instead of stacking", (cm / "CLAUDE.md").read_text().count(bk.MARK_BEGIN) == 1)

    print("the tests run from the kit source")
    r = run(fresh, "--test")
    check("--test passes without any test file in the target", r.returncode == 0 and "test_gh_rules.py" in r.stdout and not any(
        Path(n).name.startswith("test_") for n in snapshot(fresh)), (r.returncode, r.stdout[-300:], r.stderr))

print("\n" + ("all passed" if not fails else f"{len(fails)} failed: {fails}"))
sys.exit(1 if fails else 0)
