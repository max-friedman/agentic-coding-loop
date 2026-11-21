"""Shared by the lane hooks (admission_gate.py, lane_ledger.py) and spawn_gate.py: the project's knobs in
`.loop/config.json`, the `Lane: <kind>; Hotspot: <areas>` line, and the lane ledger `.loop/lanes.json`.

Every knob has a default, so a project with no config file gets working gates. `hooks/README.md` documents each one.
Paths are relative to the project: $CLAUDE_PROJECT_DIR when Claude Code sets it, else the working directory.
"""
from __future__ import annotations

import contextlib
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULTS: dict = {
    "lanes": {
        "total": 5,                       # running lanes at most, every kind together
        "caps": {"feature": 4, "bug": 1, "process": 1},  # per kind; a kind not listed has cap 0 (blocked)
        "default_kind": "feature",        # the kind of a spawn whose prompt has no Lane: line
        "require_lane_line": False,       # True: a spawn with no Lane: line is blocked instead of defaulted
        "stale_hours": 6,                 # a ledger entry this old counts as ended (a crashed lane can't hold a slot)
        "read_only_types": ["Explore", "Plan", "claude-code-guide", "web-fetch"],  # never counted, never gated
    },
    "resources": {
        "min_free_disk_gb": 15,           # block a spawn under this much free disk
        "max_swap_used_gb": 6,            # block a spawn over this much swap in use
        "scale_to_machine": True,         # lower both on a smaller machine (see floors())
    },
    "spawn_gate": {
        "require_model": False,           # True: an Agent spawn must set `model`
        "require_rules": False,           # True: a spawn prompt must carry one of rules_markers
        "rules_markers": [["helper-rules.md"], ["playbook", "prelanding"]],  # alternatives; each: phrases all present
        "require_no_notify": False,       # True: a RemoteTrigger prompt must say it won't notify the owner
    },
    "gh_rules": {
        "block_pr_merge": False,          # True: block `gh pr merge` on this repo (land with scripts/land.sh); opt-in
        "warn_shared_body_file": True,    # warn on a PR body read from a shared scratch path
    },
    "git_rules": {
        "block_no_verify": True,          # block `git commit --no-verify`/`-n` and `git push --no-verify`
        "landers": ["land.sh", "prelanding.py"],  # landing scripts whose override flags only the coordinator may pass
        "coordinator_only_flags": ["--no-prelanding", "--skip-checks"],
        "gate_env": ["PRELANDING_CHECKS", "WIP_LIMIT"],  # env vars that change a gate: set on a command, they warn
        "worktree_dirs": [".claude/worktrees", "../{repo}-worktrees"],  # relative to the project; {repo}: its name
        "block_stray_worktree": True,     # a helper's `git worktree add` outside worktree_dirs and $TMPDIR: blocked
    },
    "wip_limit": {
        "max_open_prs": 7,                # `gh pr create` (not --draft) blocked at this many open product PRs; 0: off
        "product_paths": [],              # prefixes that count as product code; empty: every path not exempt
        "exempt_paths": ["docs/", "tests/", "test/"],  # a PR touching only these (and *.md) is exempt, not counted
        "exempt_branches": ["revert-"],   # branch prefixes that are exempt and not counted
    },
    "finish_before_start": {
        "max_waiting_prs": 0,             # >0: a feature spawn is refused while more open ready PRs wait; 0: off
    },
    "watchdog": {
        "min_free_disk_gb": 12,           # watchdog.py flags disk_low under this (it reads the file itself)
        "lanes_idle_minutes": 30,         # lanes_idle: no lane running this long while ready work exists
        "ready_file": "docs/ROADMAP.md",  # where ready work is listed (no file: lanes_idle is off)
        "ready_pattern": r"\|\s*Ready\s*\|",  # each line matching this is one ready item
        "rule_notes_dir": "",             # the coordinator's private notes (its memory dir); empty: rule_drift is off
        "rule_note_pattern": r"^\s*type:\s*feedback\b",  # a note whose first lines match this records a rule
        "rule_docs": ["docs/process", "CLAUDE.md"],  # where written rules live
        "rule_drift_hours": 24,           # rule notes changed this recently and after rule_docs' last commit drift
    },
    "release": {                          # the release pipeline: how a merged change reaches users (off while unset)
        "paused_file": "",                # JSON the pipeline writes while it is paused: {"at": epoch, "why": "..."}
        "published_file": "",             # JSON naming the build users run: {"commit", "published": epoch, "version"}
        "good_ref": "origin/main",        # what the next build is cut from
        "shipped_paths": [],              # paths whose changes reach users through the build; empty: every path
        "not_shipped_pattern": r"(^|/)tests?/|(^|/)test_[^/]*$",  # files that never ship (tests)
        "resume_command": "",             # the command that resumes the pipeline (quoted in flags and the digest)
        "stuck_hours": 24,                # watchdog.py: paused this long is release_stuck (to the human at once)
        "stale_days": 2,                  # watchdog.py: build_stale when a shipped change this old isn't in the build
    },
    "digest": {
        "assumptions_log": "docs/process/assumptions-log.md",  # rows whose last cell starts with `open` are counted
        "min_lanes": 2,                   # under this many running lanes, the digest says so
    },
    "worktree_gc": {
        "idle_hours": 6,                  # scripts/worktree_gc.py removes a finished, clean worktree idle this long
    },
    "waiter_reaper": {
        "max_age_hours": 6,               # scripts/waiter_reaper.py kills a Claude Code waiter shell older than this
        "protected": [],                  # substrings of commands it never kills (your queue or scheduled-suite scripts)
    },
    "prelanding": {
        "checks": [],                     # the commands scripts/prelanding.py runs (it fails when none is set)
        "gate_paths": ["scripts/prelanding.py", "scripts/land.sh", ".claude/hooks/", ".claude/settings.json",
                       ".githooks/", ".github/workflows/"],  # files that decide what runs or passes
        "code_paths": [],                 # product code; a PR changing a gate and these needs an independent review line
        "not_independent": ["coordinator", "author", "self", "me", "myself"],  # reviewer names that don't count
        "stale_revert": True,             # refuse a branch that undoes lines main gained since it forked
        "review_lines": [],               # [{"name": "Fidelity", "when_body": "^Cutover:", "when_paths": ["ui/"]}]: such a
                                          # PR needs `<name>: OK (<reviewer>, ...)` from someone independent (exit 13)
    },
    "cutover": {                          # scripts/cutover_gate.py (prelanding exit 14)
        "when_body": r"^\W*Cutover:",    # a PR body matching this is a cutover
        "when_paths": [],                 # so is a PR changing these (your feature-switch config)
        "passes_file": "",                # JSON lines of whole-suite runs: {"at", "commit", "full", "failed", "failures"}
        "pass_max_age_hours": 24,         # a cutover needs a passing run this recent on a commit containing its base
        "known_red_file": "",             # {"scenarios": [...]}: failures that don't count against a run
        "suite_command": "",              # how to run the whole suite (quoted in the refusal)
    },
    "review_land": {
        "worktree_dir": "../{repo}-worktrees",  # scripts/review_land.py's review-<PR> worktree goes here
        "after": "scripts/land.sh {pr}",  # run once prelanding passes ({pr}: the number); your queue's add command
    },
    "coordinator": {                      # coordinator_stop.py: what must keep running in the coordinator's session
        "require_checks": False,          # True: the coordinator's turn can't end without a watcher and a check-in; opt-in
        "monitor_pattern": "events|watch",  # a running background task whose description/command/name matches
        "checkin_pattern": "check-?in|checklist|heartbeat",  # a recurring session cron whose prompt matches
        # The quiet watch: a background Bash that exits only when something needs the coordinator (cheaper than a
        # Monitor, whose every event wakes the session), and a sparse check-in (each idle wake re-reads the context).
        "monitor_command": "Bash(run_in_background=true, description=\"events: the quiet watch\", command=\"<your wait "
                           "script, which exits when something needs the coordinator>\")",
        "checkin_command": "CronCreate(cron=\"17 */2 * * *\", recurring=true, prompt=\"Coordinator check-in: run the "
                           "checklist in docs/process/PLAYBOOK.md\")",
        "cooldown_minutes": 15,           # each condition blocks at most once per this many minutes
    },
}

LANE_LINE = re.compile(r"Lane:\s*(\w+)\s*(?:;\s*Hotspot:\s*([\w,\- ]+))?", re.I)


def project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def config_path() -> Path:
    return Path(os.environ.get("LOOP_CONFIG") or project_dir() / ".loop" / "config.json")


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def config(path: Path | str | None = None) -> dict:
    """DEFAULTS with the project's `.loop/config.json` laid over them. A file that doesn't parse raises: each caller
    decides whether that blocks (the admission gate fails closed) or not."""
    p = Path(path) if path else config_path()
    if not p.exists():
        return copy.deepcopy(DEFAULTS)
    return _merge(DEFAULTS, json.loads(p.read_text(encoding="utf-8")))


# ------------------------------------------------------------------ the machine

def total_disk_gb() -> float:
    return shutil.disk_usage(Path.home()).total / 1e9


def ram_gb() -> float | None:
    try:
        if sys.platform == "darwin":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5).stdout
            return int(out.strip()) / 1e9
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9
    except Exception:  # noqa: BLE001 - unreadable: don't scale
        return None


def floors(cfg: dict, disk_total_gb: float | None = None, ram: float | None = None) -> tuple[float, float]:
    """(minimum free disk GB, maximum swap used GB). A value set in the config is used as given. A default, with
    scale_to_machine, is lowered on a smaller machine: the disk floor to at most 10% of the disk, the swap ceiling to
    at most 3/8 of RAM. On the 16 GB, 228 GB laptop the defaults came from neither changes, nor on a bigger one."""
    r, d = cfg["resources"], DEFAULTS["resources"]
    disk, swap = float(r["min_free_disk_gb"]), float(r["max_swap_used_gb"])
    if r.get("scale_to_machine"):
        if r["min_free_disk_gb"] == d["min_free_disk_gb"]:
            total = disk_total_gb if disk_total_gb is not None else total_disk_gb()
            disk = min(disk, round(0.10 * total, 1))
        mem = ram if ram is not None else ram_gb()
        if mem and r["max_swap_used_gb"] == d["max_swap_used_gb"]:
            swap = min(swap, round(0.375 * mem, 1))
    return disk, swap


def swap_used_gb() -> float | None:
    try:
        if sys.platform == "darwin":  # "total = 9216.00M  used = 7884.25M  free = ..."
            out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True, timeout=5).stdout
            m = re.search(r"used = ([\d.]+)M", out)
            return float(m.group(1)) / 1024 if m else None
        info = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
        kb = lambda k: float(info[k].split()[0])  # noqa: E731
        return (kb("SwapTotal") - kb("SwapFree")) / 1024 / 1024
    except Exception:  # noqa: BLE001 - unreadable probe: don't block on it
        return None


# ------------------------------------------------------------------ the Lane: line

def lane_of(tool_input: dict, cfg: dict) -> tuple[str | None, set[str], bool]:
    """(kind, hotspots, the line was there) of a spawn. kind None: not a lane (a read-only type, or `Lane: none`)."""
    if str(tool_input.get("subagent_type") or "") in cfg["lanes"]["read_only_types"]:
        return None, set(), True
    m = LANE_LINE.search(str(tool_input.get("prompt") or ""))
    if not m:
        return cfg["lanes"]["default_kind"], set(), False
    kind = m.group(1).lower()
    if kind == "none":
        return None, set(), True
    hotspots = {h.strip().lower() for h in (m.group(2) or "").split(",") if h.strip() and h.strip().lower() != "none"}
    return kind, hotspots, True


# ------------------------------------------------------------------ the ledger

def ledger_path() -> Path:
    p = Path(os.environ.get("LANE_LEDGER") or ".loop/lanes.json")
    return p if p.is_absolute() else project_dir() / p


def read_doc(path: Path | None = None) -> dict:
    """The ledger file: {"lanes": [...], "stopped": [agent ids whose stop came before their spawn was recorded]}."""
    p = path or ledger_path()
    doc = json.loads(p.read_text(encoding="utf-8") or "{}") if p.exists() else {}
    return {"lanes": list(doc.get("lanes", [])), "stopped": list(doc.get("stopped", []))}


def read_ledger(path: Path | None = None) -> list[dict]:
    return read_doc(path)["lanes"]


def running(cfg: dict, now: float | None = None, path: Path | None = None) -> list[dict]:
    """The ledger's lanes, minus the stale ones."""
    now = time.time() if now is None else now
    ttl = float(cfg["lanes"]["stale_hours"]) * 3600
    return [e for e in read_ledger(path) if now - float(e.get("updated", 0)) < ttl]


@contextlib.contextmanager
def locked_ledger(path: Path | None = None):
    """Read, change and write the ledger under an exclusive lock, so two hooks firing at once don't lose an entry.
    Yields the ledger document ({"lanes", "stopped"}); the caller changes it in place."""
    p = path or ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p.with_name(p.name + ".lock"), "w") as lock:
        try:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        except ImportError:  # no fcntl (Windows): best effort
            pass
        doc = read_doc(p)
        yield doc
        fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=p.name, suffix=".tmp")
        with os.fdopen(fd, "w") as fh:
            json.dump(doc, fh, indent=1)
            fh.write("\n")
        os.replace(tmp, p)
