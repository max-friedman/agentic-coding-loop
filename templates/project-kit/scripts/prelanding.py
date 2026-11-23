#!/usr/bin/env python3
"""Run the fast checks on this branch merged with origin/main, and record the pass for its head commit.

    python3 scripts/prelanding.py            # the current branch
    python3 scripts/prelanding.py --status   # has HEAD a recorded pass?
    python3 scripts/prelanding.py --body-only [--pr N] [--body FILE]   # only the PR body's lines: seconds, no checks
    python3 scripts/prelanding.py --batch 12 15 19 [--plan] [--json FILE]   # several PRs in one run

The checks run in a scratch worktree of HEAD with origin/main merged in, so what passes is what main would get.
PRELANDING_CHECKS lists them, separated by ";" (or the "prelanding": {"checks": [...]} list in .loop/config.json).
With no checks configured it fails: a check that ran nothing is no verdict. A pass is recorded in
.loop/prelanding/<sha> of the main checkout; scripts/land.sh refuses a pull request whose head has none.

Fail fast: every problem readable from the PR body and the file list (a gate change without its review line, a review
line that is there but names the author, an `Intentional revert:` line the stale-merge guard can't read) is reported,
all at once with the fix, before the scratch worktree or any check, so a typo costs seconds, not a whole run.
`--body-only` runs just these. A missing review line is not one of them: it is added after an independent review, so the
checks still run first and its refusal (exit 13) comes after them.

The scratch worktree is made (under .loop/throwaways/ of the main checkout) only once the run holds one of `prelanding.max_throwaways` (2)
places (scripts/throwaway_worktrees.py: queued runs no longer each hold a checkout while they wait), and it is removed
however the run ends, SIGTERM and SIGHUP included; a stale one a kill left is swept at the start.

Batch (`--batch PR...`): several PRs are merged, in order, onto origin/main in one scratch worktree and the same checks
run once; green records a pass for each head (the record notes the PRs it was checked with), red is bisected by halves,
so the innocent PRs still get passes and the culprit fails alone. The per-PR rules above keep their exit codes
(outcome `refused`) and run per PR first. A PR that changes a gate (`gate_paths`) or a path in `alone_paths`, or that
conflicts with an earlier PR in the batch, runs on its own. At most `batch_max` (6) PRs share a run. A failure the
checks mark with `env_marker` ("ENVIRONMENT, not your PR") blames nobody and is not bisected. `--plan` says which runs
it would make; `--json FILE` writes each PR's outcome. Exit 0 only if every PR passed.

Two guards run before the checks (knobs under "prelanding" in .loop/config.json):
- A gate change is reviewed on its own. A branch that changes a gate (`gate_paths`: files that decide what runs, what
  is skipped or what passes) together with product code (`code_paths`; empty: the rule is off) is refused (exit 11)
  unless the PR body has `Gate change: reviewed by <reviewer>`, naming someone independent: a fresh reviewer agent or
  the owner, never the author or the coordinator (`not_independent`). Otherwise the check and the code it checks are
  changed and reviewed together. Split the gate change into its own PR when you can.
- The stale-merge guard (`stale_revert`, scripts/stale_revert.py): a branch that undoes lines main gained since it
  forked is refused (exit 12) unless the body or a commit says `Intentional revert: <what and why>`.
After the checks (so a hand-back has their results too), one more:
- A required review line (`review_lines`). Each rule names a line, the PR bodies (`when_body`, a regex) and changed
  paths (`when_paths`) that need it: e.g. `{"name": "Fidelity", "when_body": "^Cutover:", "when_paths": ["ui/"]}`
  means a PR declaring a cutover, or changing ui/, needs `Fidelity: OK (<reviewer>, ...)` naming someone independent.
  Missing, or naming the author or the coordinator: refused (exit 13), no pass recorded. A cutover once passed with
  no review line at all. Anything that queues PRs by itself calls `missing_review_lines()` and skips a PR that lacks
  one: an auto-queue once queued a PR before its review came back.
The PR body comes from `gh pr view` for the current branch (PRELANDING_BODY overrides it; no PR: an empty body).

- A cutover that isn't ready (scripts/cutover_gate.py): the release pipeline paused, the build users run lacking
  the shipped changes a config cutover switches on, or no whole-suite pass in 24 h on its base (exit 14).
The knobs and the checks come from the main checkout's .loop/config.json (it is git-ignored, so the scratch worktree
has none).

Exit: 0 passed · 1 checks failed or conflicts · 2 setup failed · 11 gate change without an independent review ·
12 stale merge · 13 a required review line missing or wrong, or an unreadable `Intentional revert:` line · 14 a cutover
not ready
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path


def git(*args: str, cwd: str | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def main_checkout() -> Path:
    """The main checkout: its .loop/ (git-ignored, so not in the scratch worktree) holds the knobs and the records.
    The first entry of `git worktree list` (the main worktree); with a bare repository and worktrees only, that entry
    is the bare repo, so the current worktree's top level is used instead."""
    first = next((line[len("worktree "):] for line in git("worktree", "list", "--porcelain").splitlines()
                  if line.startswith("worktree ")), "")
    bare = "\nbare" in ("\n" + git("worktree", "list", "--porcelain").split("\n\n")[0])
    if first and not bare:
        return Path(first).resolve()
    return Path(git("rev-parse", "--show-toplevel")).resolve()


def record_dir() -> Path:
    return main_checkout() / ".loop" / "prelanding"


DEFAULTS = {"gate_paths": ["scripts/prelanding.py", "scripts/land.sh", ".claude/hooks/", ".claude/settings.json",
                           ".githooks/", ".github/workflows/"],
            "code_paths": [], "not_independent": ["coordinator", "author", "self", "me", "myself"],
            "stale_revert": True, "review_lines": [], "max_throwaways": 2, "batch_max": 6, "alone_paths": [],
            "env_marker": "ENVIRONMENT, not your PR"}  # as hooks/_loop.py's "prelanding"
GATE_CHANGE_LINE = re.compile(r"^\W*Gate change:\s*reviewed by\s+(.+?)\s*$", re.I | re.M)


def knobs(root: str) -> dict:
    try:
        cfg = json.loads(Path(root, ".loop", "config.json").read_text())
    except (OSError, ValueError):
        cfg = {}
    own = cfg.get("prelanding") if isinstance(cfg.get("prelanding"), dict) else {}
    return {**DEFAULTS, **own}


def checks(root: str) -> list[str]:
    env = os.environ.get("PRELANDING_CHECKS")
    if env:
        return [c.strip() for c in env.split(";") if c.strip()]
    return [c for c in knobs(root).get("checks") or [] if isinstance(c, str) and c.strip()]


def pr_body() -> str:
    if "PRELANDING_BODY" in os.environ:
        return os.environ["PRELANDING_BODY"]
    r = subprocess.run(["gh", "pr", "view", "--json", "body", "-q", ".body"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def gate_change_refusal(files: list[str], body: str, cfg: dict) -> str:
    """Why a gate change that comes with product code can't land, or ""."""
    gates = [f for f in files if f.startswith(tuple(cfg["gate_paths"])) or re.match(r"^scripts/[^/]*_gate\.py$", f)]
    code = [f for f in files if cfg["code_paths"] and f.startswith(tuple(cfg["code_paths"]))]
    if not gates or not code:
        return ""
    m = GATE_CHANGE_LINE.search(body or "")
    who = m.group(1).strip() if m else ""
    bad = {w.lower() for w in cfg["not_independent"]}
    if who and not ({w.strip(".,;()").lower() for w in who.split()} & bad):
        return ""
    said = f" (it names `{who}`, which isn't independent)" if who else ""
    return (f"this branch changes a gate ({', '.join(gates[:3])}{'…' if len(gates) > 3 else ''}) together with code "
            f"({', '.join(code[:3])}{'…' if len(code) > 3 else ''}){said}. A gate change is reviewed on its own: split "
            "it into its own PR (best), or have a fresh reviewer agent or the owner read the gate diff and add "
            "`Gate change: reviewed by <reviewer>` to the PR body (never the author or the coordinator).")


def cut_configured(root: str) -> bool:
    """The project set a `cutover` or `release` section in .loop/config.json."""
    try:
        cfg = json.loads(Path(root, ".loop", "config.json").read_text())
    except (OSError, ValueError):
        return False
    return any(isinstance(cfg.get(k), dict) and cfg[k] for k in ("cutover", "release"))


def review_line(name: str) -> re.Pattern:
    return re.compile(r"^[ \t>*_-]*" + re.escape(name) + r":\**[ \t]*OK\b[ \t]*\(([^,)]+)", re.I | re.M)


def missing_review_lines(files: list[str], body: str, cfg: dict, present_only: bool = False) -> list[str]:
    """Why the PR can't land yet, one entry per required review line it lacks (empty: none missing). present_only: only
    a line that is there but names the author or the coordinator (a missing one is added after the review)."""
    bad = {w.lower() for w in cfg["not_independent"]}
    out = []
    for rule in cfg.get("review_lines") or []:
        name = str(rule.get("name") or "").strip()
        if not name:
            continue
        by_body = bool(rule.get("when_body")) and re.search(rule["when_body"], body or "", re.I | re.M)
        by_path = [f for f in files if rule.get("when_paths") and f.startswith(tuple(rule["when_paths"]))]
        if not by_body and not by_path:
            continue
        why = "its body matches " + repr(rule["when_body"]) if by_body else f"it changes {', '.join(by_path[:3])}"
        m = review_line(name).search(body or "")
        who = m.group(1).strip() if m else ""
        if who and not ({w.strip(".,;()").lower() for w in who.split()} & bad):
            continue
        if present_only and not who:
            continue
        said = f" (it names `{who}`, which isn't independent)" if who else ""
        out.append(f"this PR needs `{name}: OK (<reviewer>, ...)` because {why}{said}. Have a fresh reviewer agent or "
                   "the owner review it and put their line in the body (never the author or the coordinator); "
                   "scripts/review_land.py does that and reruns this")
    return out


# --- Fail fast on the PR body's lines -------------------------------------------------------------------------------
BODY_LINE = 13
REVERT_MARKED = re.compile(r"^[ \t]*(?:[-*+>]|\d+\.|\*\*|__)[ \t*_>-]*intentional revert[*_]*[ \t]*:.*$", re.I | re.M)


def _stale_revert():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import stale_revert
        return stale_revert
    except ImportError:
        return None


def revert_line_problem(body: str, label: str = "this PR") -> str:
    """Why an `Intentional revert:` line wouldn't switch off the stale-merge guard, or "": it reads only a plain line, so
    a bulleted, quoted or bold one was refused after the whole run. Prose that mentions a revert is not checked."""
    mod = _stale_revert()
    marked = [ln.strip() for ln in REVERT_MARKED.findall(body or "")]
    if not mod or not marked or mod.ON_PURPOSE.search(body or ""):
        return ""
    return (f"{label}'s `Intentional revert:` line ({marked[0][:80]!r}) has a bullet, quote or bold, which the stale-merge "
            "guard doesn't read: write it as a plain line starting `Intentional revert: <what and why>`.")


def body_problems(files: list[str], body: str, cfg: dict, label: str = "this branch") -> list[tuple[int, str]]:
    """Every PR-body problem readable without a worktree or a check, in order: [(exit code, the exact fix)]."""
    out: list[tuple[int, str]] = []
    if why := gate_change_refusal(files, body, cfg):
        out.append((11, why))
    out += [(BODY_LINE, why) for why in missing_review_lines(files, body, cfg, present_only=True)]
    if why := revert_line_problem(body, label):
        out.append((BODY_LINE, why))
    return out


def changed_files(here: Path, base: str, rev: str = "HEAD") -> list[str]:
    r = subprocess.run(["git", "diff", "--name-only", f"{base}...{rev}"], cwd=here, capture_output=True, text=True)
    return r.stdout.split() if r.returncode == 0 else []


def gh_json(*args: str) -> dict:
    r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise RuntimeError(f"gh {' '.join(args[:3])}: {(r.stderr or r.stdout).strip()[-200:]}")
    return json.loads(r.stdout or "{}")


def body_only_main(a) -> int:
    """--body-only: the PR body's lines against this head (or --pr N's): seconds, nothing built."""
    here = Path(git("rev-parse", "--show-toplevel"))
    subprocess.run(["git", "fetch", "-q", "origin"], check=False)
    cfg = knobs(str(main_checkout()))
    if a.pr:
        try:
            m = member(here, a.pr, a.base)
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as e:
            print(f"prelanding: {e}")
            return 2
        files, body, label = m["files"], m["body"], f"PR #{a.pr}"
    else:
        files, body, label = changed_files(here, a.base), pr_body(), "this branch"
    if a.body:
        body = Path(a.body).read_text()
    if not body.strip():
        print("prelanding: no PR body to check (open the PR first, or pass --body <file>)")
        return 2
    found = body_problems(files, body, cfg, label)
    for code, why in found:
        print(f"prelanding: (exit {code}) {why}")
    if found:
        print(f"prelanding: {len(found)} PR body problem(s) above; fix them before the checks "
              "(`gh pr edit <PR> --body-file <body.md>`), then run prelanding")
        return found[0][0]
    print("prelanding: PR body lines OK")
    return 0


# --- Throwaway worktrees ---------------------------------------------------------------------------------------------

def throwaway_module():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import throwaway_worktrees
    return throwaway_worktrees


def worktree_name(*parts: str) -> str:
    return "prelanding-" + re.sub(r"[^A-Za-z0-9._-]+", "-", "-".join(p for p in parts if p)).strip("-")[:60]


# --- Batch prelanding ------------------------------------------------------------------------------------------------
# One run per PR means PRs reach the landing queue one at a time and a merge train rarely forms. `--batch` merges the
# PRs onto main in one worktree and runs the checks once. Green: a pass for each head. Red: bisected by halves (each
# half its own run) so the innocent PRs still get passes and the culprit fails with its own checks.

def member(here: Path, pr: int, base: str) -> dict:
    """A PR's head, branch, body, state and files (gh, then `git fetch origin pull/<pr>/head`)."""
    info = gh_json("pr", "view", str(pr), "--json", "headRefName,headRefOid,body,state,baseRefName")
    head = str(info.get("headRefOid") or "")
    subprocess.run(["git", "fetch", "-q", "origin", f"pull/{pr}/head"], cwd=here, capture_output=True)
    if subprocess.run(["git", "cat-file", "-e", f"{head}^{{commit}}"], cwd=here, capture_output=True).returncode:
        raise RuntimeError(f"#{pr}'s head {head[:9]} couldn't be fetched")
    return {"pr": pr, "head": head, "branch": str(info.get("headRefName") or ""), "body": str(info.get("body") or ""),
            "state": str(info.get("state") or ""), "base_ref": str(info.get("baseRefName") or ""),
            "files": changed_files(here, base, head)}


def batch_alone(files: list[str], cfg: dict) -> str:
    """Why a PR runs on its own, or "": it changes a gate (the batch would be checked by its new rules) or an
    `alone_paths` path (a protocol, a migration: whatever you land by itself)."""
    gate = [f for f in files if f.startswith(tuple(cfg["gate_paths"])) or re.match(r"^scripts/[^/]*_gate\.py$", f)]
    if gate:
        return f"it changes a gate ({gate[0]})"
    hot = [f for f in files if cfg["alone_paths"] and f.startswith(tuple(cfg["alone_paths"]))]
    return f"it touches a path that lands alone ({hot[0]})" if hot else ""


def batch_groups(members: list[dict], cap: int) -> list[list[dict]]:
    """The runs a batch makes, in order: the compatible members together (at most `cap` a run), then each `alone` one."""
    together = [m for m in members if not m.get("alone")]
    runs = [together[i:i + cap] for i in range(0, len(together), max(1, cap))]
    return [r for r in runs if r] + [[m] for m in members if m.get("alone")]


def settle(group: list[dict], check, say=print, of: list[dict] | None = None) -> dict[int, dict]:
    """Run `group` (check(group) -> {"ok", "why", "env", "tree", "conflict": pr or None}) and bisect a red one by halves
    until each PR has its own verdict: {pr: {"outcome": "passed"|"failed"|"conflict", "why", "run": the group's PRs,
    "tree"}}. A member that conflicts with an earlier one is taken out and run on its own. A red run that is the
    environment blames no one: every member fails with that reason, no bisect."""
    of = of or group
    out: dict[int, dict] = {}
    res = check(group)
    while res.get("conflict") and len(group) > 1:
        bad = res["conflict"]
        say(f"prelanding: #{bad} conflicts with main or an earlier PR in the batch: it runs on its own")
        out.update(settle([m for m in group if m["pr"] == bad], check, say))
        group = [m for m in group if m["pr"] != bad]
        res = check(group)
    prs = [m["pr"] for m in group]
    if res.get("conflict"):
        out[prs[0]] = {"outcome": "conflict", "why": res.get("why") or "conflicts with main", "run": prs}
        return out
    if res.get("ok"):
        for m in group:
            out[m["pr"]] = {"outcome": "passed", "why": "", "run": prs, "tree": res.get("tree")}
        return out
    if res.get("env") or len(group) == 1:
        for m in group:
            out[m["pr"]] = {"outcome": "failed", "why": res.get("why") or "checks failed", "run": prs,
                            **({"culprit_of": [x["pr"] for x in of]} if len(of) > 1 and len(group) == 1
                               and not res.get("env") else {})}
        return out
    half = (len(group) + 1) // 2
    say(f"prelanding: batch {', '.join('#%d' % p for p in prs)} failed ({res.get('why') or 'checks failed'}): bisecting, "
        f"{', '.join('#%d' % m['pr'] for m in group[:half])} first")
    for part in (group[:half], group[half:]):
        out.update(settle(part, check, say, of))
    return out


def run_checks(cmds: list[str], cwd: str, marker: str) -> tuple[list[str], bool]:
    """Run the checks, echoing their output: (the failed commands, whether any printed `marker`: an environment failure)."""
    failed, env = [], False
    for cmd in cmds:
        print(f"== {cmd}", flush=True)
        r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, errors="replace")
        print(r.stdout + r.stderr, end="", flush=True)
        if r.returncode:
            failed.append(cmd)
            env = env or bool(marker and marker in r.stdout + r.stderr)
    return failed, env


def check_group(here: Path, group: list[dict], base: str, cmds: list[str], cfg: dict, keep: bool = False) -> dict:
    """One run: a worktree of `base`, each PR's head merged in order (a conflict stops it: {"conflict": pr}), the checks once."""
    tw = throwaway_module()
    root = main_checkout()
    sha = git("rev-parse", base)
    wt = root / ".loop" / tw.DIR / (worktree_name("batch", "-".join(str(m["pr"]) for m in group))
                                    + f"-{os.getpid()}-{secrets.token_hex(3)}")
    wt.parent.mkdir(parents=True, exist_ok=True)
    tw.sweep(here, [wt.parent])
    with tw.slot(root / ".loop" / tw.LOCKS, tw.slots_wanted(root), f"batch {wt.name}"):
        r = subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), sha], cwd=here, capture_output=True, text=True)
        if r.returncode:
            shutil.rmtree(wt, ignore_errors=True)
            return {"ok": False, "why": f"couldn't make a worktree: {r.stderr.strip()}", "env": True}
        with tw.owned(wt, here, keep=keep):
            for m in group:
                mg = subprocess.run(["git", "-c", "user.name=prelanding", "-c", "user.email=prelanding@localhost", "merge",
                                     "-q", "--no-edit", "-m", f"batch prelanding: #{m['pr']}", m["head"]],
                                    cwd=wt, capture_output=True, text=True)
                if mg.returncode:
                    files = subprocess.run(["git", "diff", "--name-only", "--diff-filter=U"], cwd=wt, capture_output=True,
                                           text=True).stdout.split()
                    subprocess.run(["git", "merge", "--abort"], cwd=wt, capture_output=True)
                    return {"ok": False, "conflict": m["pr"],
                            "why": f"conflicts with {base}{' or an earlier PR in the batch' if len(group) > 1 else ''} in: "
                                   f"{', '.join(files) or mg.stderr.strip()}"}
            print(f"prelanding: {', '.join('#%d (%s)' % (m['pr'], m['head'][:9]) for m in group)} + {base}", flush=True)
            failed, env = run_checks(cmds, str(wt), cfg["env_marker"])
            tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=wt, capture_output=True, text=True).stdout.strip()
            if failed:
                return {"ok": False, "env": env, "tree": tree,
                        "why": (cfg["env_marker"] + ": " if env else "checks failed: ") + "; ".join(failed)}
            return {"ok": True, "tree": tree}


def member_refusal(here: Path, m: dict, base: str, cfg: dict, root: str) -> tuple[int, str]:
    """(exit code, why) when a PR can't get a pass from a batch, the same rules and codes as a run on its branch."""
    pr, head, files, body, label = m["pr"], m["head"], m["files"], m["body"], f"PR #{m['pr']}"
    if m.get("state") and m["state"] != "OPEN":
        return 2, f"#{pr} isn't an open PR ({m['state']})"
    if found := body_problems(files, body, cfg, label):
        return found[0]
    if why := (missing_review_lines(files, body, cfg) or [""])[0]:
        return 13, why
    mod = _stale_revert()
    if cfg.get("stale_revert", True) and mod and (why := mod.refusal(here, head, files, body, base, label)):
        return 12, why
    try:
        import cutover_gate  # noqa: E402
    except ImportError:
        cutover_gate = None
    if cutover_gate and (why := cutover_gate.refusal(here, files, body, base, head=head, root=Path(root))):
        return 14, why
    return 0, ""


def record(head: str, together: list[dict] | None = None, tree: str = "") -> None:
    rec = record_dir() / head
    rec.parent.mkdir(parents=True, exist_ok=True)
    extra = "".join(f"batch: {' '.join('#%d' % m['pr'] for m in together)}\n" if together and len(together) > 1 else "")
    rec.write_text(time.strftime("%Y-%m-%dT%H:%M:%S") + "\n" + extra + (f"tree: {tree}\n" if tree else ""))


def run_batch(here: Path, prs: list[int], base: str, cfg: dict, cmds: list[str], root: str, keep: bool = False,
              member_fn=None, refusal_fn=None, check_fn=None, record_fn=record, plan_only: bool = False) -> dict:
    """--batch: {pr: {"outcome": "passed"|"failed"|"refused"|"conflict"|"covered", "code", "why", "run"}}. The *_fn
    arguments are the outside world (tests pass fakes)."""
    member_fn = member_fn or (lambda pr: member(here, pr, base))
    refusal_fn = refusal_fn or (lambda m: member_refusal(here, m, base, cfg, root))
    check_fn = check_fn or (lambda group: check_group(here, group, base, cmds, cfg, keep))
    cap = max(1, int(cfg["batch_max"]))
    out: dict[int, dict] = {}
    members: list[dict] = []
    for pr in dict.fromkeys(prs):
        try:
            m = member_fn(pr)
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as e:
            out[pr] = {"outcome": "refused", "code": 2, "why": str(e)}
            continue
        if (record_dir() / m["head"]).exists():
            out[pr] = {"outcome": "covered", "code": 0, "why": f"{m['head'][:9]} already has a recorded pass"}
            continue
        code, why = refusal_fn(m)
        if code:
            out[pr] = {"outcome": "refused", "code": code, "why": why}
            continue
        if alone := batch_alone(m["files"], cfg):
            m["alone"] = alone
            print(f"prelanding: #{pr} runs on its own: {alone}")
        members.append(m)
    by_pr = {m["pr"]: m for m in members}
    runs = batch_groups(members, cap)
    for i, group in enumerate(runs, 1):
        print(f"prelanding: run {i} of {len(runs)}{' (planned)' if plan_only else ''}: "
              + ", ".join(f"#{m['pr']}" for m in group))
    if plan_only:
        return out
    for group in runs:
        for pr, res in settle(group, check_fn).items():
            out[pr] = {**res, "code": {"passed": 0, "failed": 1, "conflict": 1}[res["outcome"]]}
            if res["outcome"] == "passed":
                together = [by_pr[p] for p in res.get("run") or [pr] if p in by_pr]
                record_fn(by_pr[pr]["head"], together, res.get("tree") or "")
    return out


def batch_main(a) -> int:
    here = Path(git("rev-parse", "--show-toplevel"))
    root = str(main_checkout())
    cfg = knobs(root)
    subprocess.run(["git", "fetch", "-q", "origin"], check=False)
    cmds = checks(root)
    if not cmds and not a.plan:
        print('prelanding: no checks configured, so nothing would be verified. Set PRELANDING_CHECKS or '
              '"prelanding": {"checks": [...]} in .loop/config.json')
        return 1
    out = run_batch(here, a.batch, a.base, cfg, cmds, root, a.keep, plan_only=a.plan)
    for pr, r in out.items():
        print(f"prelanding: #{pr} {r['outcome']}" + (f" (exit {r['code']})" if r.get("code") else "")
              + (f", checked with {', '.join('#%d' % p for p in r['run'] if p != pr)}" if len(r.get("run") or []) > 1 else "")
              + (f": {r['why']}" if r.get("why") else ""))
    if a.json:
        Path(a.json).write_text(json.dumps({str(k): v for k, v in out.items()}, indent=1))
    return 0 if a.plan or all(r["outcome"] in ("passed", "covered") for r in out.values()) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--status", action="store_true", help="has HEAD a recorded pass?")
    ap.add_argument("--keep", action="store_true", help="keep the throwaway worktree")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--body-only", action="store_true", help="check only the PR body's lines: no worktree, no checks")
    ap.add_argument("--pr", type=int, help="with --body-only: that PR's head and body")
    ap.add_argument("--body", help="read the PR body from this file instead of `gh pr view`")
    ap.add_argument("--batch", nargs="+", type=int, metavar="PR", help="check these PRs merged together in one run")
    ap.add_argument("--json", help="with --batch: write each PR's outcome here")
    ap.add_argument("--plan", action="store_true", help="with --batch: say which runs it would make, run nothing")
    a = ap.parse_args()
    if a.batch:
        return batch_main(a)
    if a.body_only:
        return body_only_main(a)
    head = git("rev-parse", "HEAD")
    rec = record_dir() / head
    if a.status:
        print(f"prelanding: {head[:9]} {'passed' if rec.exists() else 'has no recorded pass'}")
        return 0 if rec.exists() else 1
    subprocess.run(["git", "fetch", "-q", "origin"], check=False)
    here = Path(git("rev-parse", "--show-toplevel"))
    root = str(main_checkout())
    cfg = knobs(root)  # .loop/ is git-ignored: read it from the main checkout, not the scratch worktree
    changed = changed_files(here, a.base)
    body = Path(a.body).read_text() if a.body else pr_body()
    found = body_problems(changed, body, cfg)
    if found:
        for _code, why in found:
            print(f"prelanding: {why}")
        print("prelanding: stopped before the checks: fix the PR body line(s) above and run this again "
              "(`prelanding.py --body-only` checks just these, in seconds)")
        return found[0][0]
    tw = throwaway_module()
    wt = Path(root) / ".loop" / tw.DIR / f"prelanding-{head[:9]}-{os.getpid()}-{secrets.token_hex(3)}"
    wt.parent.mkdir(parents=True, exist_ok=True)
    tw.sweep(here, [wt.parent])
    with tw.slot(Path(root) / ".loop" / tw.LOCKS, tw.slots_wanted(Path(root)), f"prelanding {head[:9]}"):
        git("worktree", "add", "-q", "--detach", str(wt), head)
        with tw.owned(wt, here, keep=a.keep):
            merge = subprocess.run(["git", "merge", "-q", "--no-edit", a.base], cwd=wt, capture_output=True, text=True)
            if merge.returncode:
                print(f"prelanding: the branch conflicts with {a.base}; merge main in and rerun")
                return 1
            if cfg.get("stale_revert", True):
                mod = _stale_revert()
                why = mod.refusal(Path(wt), head, changed, body) if mod else ""
                if why:
                    print(f"prelanding: {why}")
                    return 12
            cmds = checks(root)
            if not cmds:
                print('prelanding: no checks configured, so nothing would be verified. Set PRELANDING_CHECKS or '
                      '"prelanding": {"checks": ["<your test command>"]} in .loop/config.json')
                return 1
            failed = []
            for cmd in cmds:
                print(f"== {cmd}", flush=True)
                if subprocess.run(cmd, shell=True, cwd=wt).returncode:
                    failed.append(cmd)
            if failed:
                print("prelanding: FAILED: " + "; ".join(failed))
                return 1
            missing = missing_review_lines(changed, body, cfg)
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            try:
                import cutover_gate
            except ImportError:
                cutover_gate = None
            if cutover_gate:
                # The branch itself, not the merged tree: a cutover's base is where the branch meets main.
                cut = cutover_gate.refusal(Path.cwd(), changed, body, "origin/main", head=head, root=Path(root),
                                           say=lambda m: print(f"prelanding: {m}"))
            else:
                print("prelanding: warning: scripts/cutover_gate.py is missing, so cutovers aren't checked")
                cut = ("the cutover knobs are configured but scripts/cutover_gate.py is missing: reinstall it "
                       "(bootstrap_kit.py --force) rather than land a cutover unchecked") if cut_configured(root) else ""
            if missing or cut:
                print("prelanding: the checks passed; no pass recorded until:")
                for why in missing:
                    print(f"prelanding: {why}")
                if cut:
                    print(f"prelanding: {cut}")
                return 13 if missing else 14
    record(head)
    print(f"prelanding: passed, recorded for {head[:9]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
