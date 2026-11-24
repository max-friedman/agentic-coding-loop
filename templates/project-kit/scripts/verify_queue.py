#!/usr/bin/env python3
"""Bugs close on evidence, not on merge (2026-11-23): a bug is closed only after its repro ran on a device or
plugin path. A PR that says "Fixes #N" makes GitHub close #N the moment the merge queue merges it (#2756, #2599 and
#2581 had to be reopened). So after a merge the queue calls hold_open(pr): each issue the PR closed is reopened with a
comment and the `verify` label. Whoever has the evidence comments it and closes the issue (and drops the label).

    python3 scripts/verify_queue.py            # open `verify` issues: the PR that fixed each and the first release with it
    python3 scripts/verify_queue.py --json
    python3 scripts/verify_queue.py hold 2778  # (re)apply the hold for a merged PR by hand

Exempt: issues labelled `no-verify`, and non-bug kinds (enhancement, feature-request, documentation, process, question).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

GH = os.getenv("LOOP_GH_BIN") or "gh"
LABEL = "verify"
EXEMPT = {"no-verify", "enhancement", "feature-request", "documentation", "process", "question"}
MARK = "Held open for verification: fixed by PR #"
_PR_IN_COMMENT = re.compile(re.escape(MARK) + r"(\d+)")


def should_hold(labels: list[str]) -> bool:
    """A closed issue the PR fixed stays open for evidence unless it is exempt or already held."""
    names = {x.lower() for x in labels}
    return not (names & EXEMPT) and LABEL not in names


def hold_comment(pr: int) -> str:
    return (f"{MARK}{pr} (merged). A merge is not evidence: run the repro on a device or plugin path, comment what "
            f"you saw, then close this issue and remove the `{LABEL}` label (`no-verify` exempts an issue).")


def pr_from_comments(bodies: list[str]) -> int | None:
    """The PR a hold comment names (the latest one), else None."""
    found = [int(m.group(1)) for b in bodies for m in _PR_IN_COMMENT.finditer(b or "")]
    return found[-1] if found else None


def first_release(tags_containing: list[str]) -> str | None:
    """The first release tag (vX.Y.N, oldest first) among the tags that contain the merge commit."""
    rel = [t for t in tags_containing if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    rel.sort(key=lambda t: tuple(int(p) for p in t[1:].split(".")))
    return rel[0] if rel else None


def _gh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([GH, *args], capture_output=True, text=True, timeout=60)


def _json(*args: str):
    r = _gh(*args)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[:200])
    return json.loads(r.stdout)


def hold_open(pr: int, say=print, wait_s: float = 8.0) -> list[int]:
    """Reopen + label every issue merged PR `pr` closed. Best effort: never raises, returns the issues held."""
    held: list[int] = []
    try:
        refs = _json("pr", "view", str(pr), "--json", "closingIssuesReferences")["closingIssuesReferences"]
        todo = [r["number"] for r in refs]
        if not todo:
            return held
        _gh("label", "create", LABEL, "--color", "fbca04", "--description",
            "fix merged; close only with device/plugin evidence", "--force")
        for n in todo:
            for attempt in range(3):  # GitHub closes the issue a moment after the merge
                issue = _json("issue", "view", str(n), "--json", "state,labels")
                labels = [x["name"] for x in issue["labels"]]
                if not should_hold(labels):
                    break
                if issue["state"] == "CLOSED":
                    _gh("issue", "reopen", str(n), "--comment", hold_comment(pr))
                    _gh("issue", "edit", str(n), "--add-label", LABEL)
                    held.append(n)
                    break
                if attempt < 2:
                    time.sleep(wait_s / 2)
                else:  # still open: label it and say so, GitHub's close (if it comes) is reopened by `hold`
                    _gh("issue", "edit", str(n), "--add-label", LABEL)
                    held.append(n)
        if held:
            say(f"verify: held open for evidence: {', '.join('#' + str(n) for n in held)}")
    except (RuntimeError, OSError, KeyError, ValueError, subprocess.TimeoutExpired) as e:
        say(f"verify: could not hold PR #{pr}'s issues open ({e})")
    return held


def queue() -> list[dict]:
    rows = []
    for i in _json("issue", "list", "--label", LABEL, "--state", "open", "--limit", "100",
                   "--json", "number,title,comments"):
        pr = pr_from_comments([c.get("body", "") for c in i.get("comments", [])])
        sha = release = None
        if pr:
            try:
                sha = (_json("pr", "view", str(pr), "--json", "mergeCommit")["mergeCommit"] or {}).get("oid")
                if sha:
                    out = subprocess.run(["git", "tag", "--contains", sha], capture_output=True, text=True).stdout
                    release = first_release(out.split())
            except (RuntimeError, OSError, KeyError, ValueError):
                pass
        rows.append({"issue": i["number"], "title": i["title"], "pr": pr, "release": release})
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", choices=["list", "hold"], default="list")
    ap.add_argument("pr", nargs="?", type=int)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "hold":
        if not a.pr:
            ap.error("hold needs a PR number")
        hold_open(a.pr)
        return 0
    subprocess.run(["git", "fetch", "-q", "--tags", "origin"], capture_output=True)
    rows = queue()
    if a.json:
        print(json.dumps(rows, indent=1))
    elif not rows:
        print("verify queue: empty")
    else:
        print(f"verify queue: {len(rows)} issue(s) fixed, awaiting evidence")
        for r in rows:
            print(f"  #{r['issue']} {r['title'][:70]} | PR {('#' + str(r['pr'])) if r['pr'] else '?'}"
                  f" | {r['release'] or 'not released yet'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
