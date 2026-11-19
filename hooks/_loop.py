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
    },
    "watchdog": {
        "min_free_disk_gb": 12,           # watchdog.py flags disk_low under this (it reads the file itself)
    },
    "coordinator": {                      # coordinator_stop.py: what must keep running in the coordinator's session
        "require_checks": False,          # True: the coordinator's turn can't end without a watcher and a check-in; opt-in
        "monitor_pattern": "events|watch",  # a running background task whose description/command/name matches
        "checkin_pattern": "check-?in|checklist|heartbeat",  # a recurring session cron whose prompt matches
        "monitor_command": "Monitor(description=\"events: the coordinator's event stream\", command=\"<your event "
                           "stream command>\")",
        "checkin_command": "CronCreate(cron=\"7,37 * * * *\", recurring=true, prompt=\"Coordinator check-in: run the "
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
