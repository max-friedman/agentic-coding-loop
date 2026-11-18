#!/usr/bin/env python3
"""The gate for this repository.

Runs identically on a laptop and in CI, which is the point — a gate that only
ever runs where it was written is an unverifiable claim, not a check. See
LOOP.md §0.5 and docs/PRINCIPLES.md §9.

    python3 scripts/check.py                    # structural checks
    python3 scripts/check.py --base origin/main # also enforce the version bump

Exit code 0 if every check passes, 1 otherwise. Stdlib only: a gate with
dependencies is a gate that fails for reasons unrelated to what it checks.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Changing any of these changes what downstream projects execute. Without a
# version bump, plugin installs never get the change (projects fetching main get
# it anyway, Round 4), so a change here without one is almost certainly a mistake.
BEHAVIOR_PATHS = ("LOOP.md", "skills/", "templates/")

MANIFEST = ".claude-plugin/marketplace.json"

# Resolved relative to the repo that ADOPTS the loop, not this one.
EXPECTED_DANGLING = {"docs/plans/LOOP_STATE.md", "docs/plans/ROAST_LOG.md"}

failures: list[str] = []
checks_run = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks_run
    checks_run += 1
    if ok:
        print(f"  ok    {name}")
    else:
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))
        failures.append(name)


def read(path: str) -> str:
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return fh.read()


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Minimal YAML frontmatter reader — flat `key: value` pairs only.

    Deliberately not PyYAML: see the stdlib-only note above. Skill frontmatter
    is flat by construction, so a real YAML parser buys nothing here.
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    out: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def check_manifest() -> dict:
    print("\nmanifest")
    try:
        manifest = json.loads(read(MANIFEST))
    except (OSError, json.JSONDecodeError) as exc:
        check("marketplace.json parses", False, str(exc))
        return {}
    check("marketplace.json parses", True)

    for field in ("name", "owner", "plugins"):
        check(f"marketplace has {field!r}", field in manifest)

    plugins = manifest.get("plugins") or []
    check("at least one plugin", bool(plugins), f"found {len(plugins)}")

    # Every declared plugin is validated, not just the first.
    #
    # This replaced `len(plugins) == 1`, which 0.10.0 broke by adding a second
    # plugin (`loop-ux-roast`) on purpose. That assertion was not merely stale:
    # it stood in for validation it never performed. Measured before replacing
    # it — with plugins[1]'s `name` deleted, its `source` set to a directory
    # that does not exist and its `version` set to `not-a-version`, the gate
    # reported the same two failures and every per-plugin check passed green.
    # A second plugin could ship completely malformed and nothing here noticed.
    for index, plugin in enumerate(plugins):
        label = plugin.get("name") or f"plugins[{index}]"

        for field in ("name", "source", "version"):
            check(f"{label}: has {field!r}", field in plugin)

        version = plugin.get("version", "")
        check(
            f"{label}: version is semver",
            bool(re.fullmatch(r"\d+\.\d+\.\d+", version)),
            f"got {version!r}",
        )

        source = plugin.get("source", "")
        check(
            f"{label}: source exists",
            isinstance(source, str) and os.path.isdir(os.path.join(ROOT, source)),
            f"got {source!r}",
        )
    return manifest


def check_skills() -> None:
    print("\nskills")
    skills_dir = os.path.join(ROOT, "skills")
    if not os.path.isdir(skills_dir):
        check("skills/ exists", False)
        return

    names = sorted(d for d in os.listdir(skills_dir) if not d.startswith("."))
    check("at least one skill", bool(names))

    # Every skill inlines LOOP.md rather than restating it, so the protocol has
    # exactly one copy. If this target moves, every skill silently ships empty.
    check("LOOP.md at plugin root", os.path.isfile(os.path.join(ROOT, "LOOP.md")))

    for name in names:
        rel = f"skills/{name}/SKILL.md"
        if not os.path.isfile(os.path.join(ROOT, rel)):
            check(f"{name}: SKILL.md present", False)
            continue
        text = read(rel)
        front = parse_frontmatter(text)
        check(f"{name}: frontmatter parses", front is not None)
        if front is None:
            continue
        check(f"{name}: has description", bool(front.get("description")))
        check(
            f"{name}: inlines LOOP.md",
            'cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"' in text,
            "skill bodies must not restate the protocol",
        )


def check_links() -> None:
    print("\nlinks")
    pattern = re.compile(r"\]\((?!https?:|#|mailto:)([^)]+)\)")
    broken: list[str] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules"}]
        for filename in filenames:
            if not filename.endswith((".md", ".txt")):
                continue
            path = os.path.join(dirpath, filename)
            rel_file = os.path.relpath(path, ROOT)
            with open(path, encoding="utf-8") as fh:
                body = fh.read()
            # Resolve against the file's REAL directory, not the directory it
            # was walked in. domains/ux-roast/LOOP.md is a symlink to the root
            # LOOP.md (the domain ships as its own plugin, so its skills can
            # read ${CLAUDE_PLUGIN_ROOT}/LOOP.md). Resolving that file's links
            # from domains/ux-roast/ reported two targets as broken that exist
            # at the root and are broken for no reader. A link is authored
            # relative to where its file actually lives.
            base = os.path.dirname(os.path.realpath(path))
            for match in pattern.finditer(body):
                target = match.group(1).split("#")[0].strip()
                if not target or target in EXPECTED_DANGLING:
                    continue
                resolved = os.path.normpath(os.path.join(base, target))
                if not os.path.exists(resolved):
                    broken.append(f"{rel_file} -> {target}")
    check("all relative links resolve", not broken, "; ".join(broken[:5]))


def check_inertness() -> None:
    print("\nboundaries")
    # proposals/ holds untrusted text submitted by agents in repositories nobody
    # here can see. If an instruction file loaded it, any consumer of the loop
    # could change the loop's behavior in every other consumer, unreviewed.
    offenders: list[str] = []
    for rel in ["LOOP.md"] + [
        f"skills/{d}/SKILL.md" for d in sorted(os.listdir(os.path.join(ROOT, "skills")))
        if os.path.isfile(os.path.join(ROOT, "skills", d, "SKILL.md"))
    ]:
        if re.search(r"(cat|read|source|include)[^\n]*proposals/", read(rel)):
            offenders.append(rel)
    check("no instruction file loads proposals/", not offenders, "; ".join(offenders))


def check_version_bump(base: str) -> None:
    print("\nrelease")

    # This compares COMMITTED state. A dirty tree would otherwise report "no
    # behavior paths changed" while the working copy plainly changed them —
    # a check that silently no-ops is worse than no check.
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.strip()
    if dirty:
        print("  warn  working tree is dirty; this check only sees committed changes")

    try:
        changed = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        check(f"can diff against {base}", False, str(exc))
        return

    touched = [f for f in changed if f.startswith(BEHAVIOR_PATHS)]
    if not touched:
        print(f"  skip  no behavior paths changed vs {base}")
        return

    try:
        before = json.loads(subprocess.run(
            ["git", "show", f"{base}:{MANIFEST}"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout)["plugins"][0]["version"]
    except Exception as exc:  # noqa: BLE001 — any failure here is a real failure
        check("can read base version", False, str(exc))
        return

    after = json.loads(read(MANIFEST))["plugins"][0]["version"]
    check(
        "version bumped for behavior change",
        before != after,
        f"{', '.join(touched[:3])} changed but version is still {after} — "
        "without a bump, plugin installs never receive it",
    )


def check_docs_derive() -> None:
    """Counts and lists in the docs are derived here, not trusted.

    Proposal 008's lesson: a gate must derive its own count. Two places drift
    when something is added: the skill tables a human reads (README, ADOPTING),
    and the state-file template every adopting project copies. A skill missing
    from the tables is invisible to anyone deciding whether to install; a section
    LOOP.md §6 requires but the template lacks is one no bootstrapped project
    will ever write.
    """
    print("\ndocs agree with the protocol")
    skills_dir = os.path.join(ROOT, "skills")
    names = sorted(
        d for d in os.listdir(skills_dir)
        if os.path.isfile(os.path.join(skills_dir, d, "SKILL.md"))
    )
    # The skill table lives in ADOPTING.md; the README stays short and links to it.
    text = read("docs/ADOPTING.md")
    missing = [n for n in names if f"| `{n}` |" not in text]
    check("docs/ADOPTING.md lists every skill", not missing, ", ".join(missing))
    check("README.md links the skill table", "docs/ADOPTING.md" in read("README.md"))

    # Every `## Section` row in LOOP.md's section 6 table must exist as a heading
    # in the template, so a bootstrapped state file starts with all of them.
    loop = read("LOOP.md")
    table = loop.split("\n## 6.", 1)[1].split("\n## 7.", 1)[0]
    required = re.findall(r"^\| `(## [^`]+)` \|", table, re.MULTILINE)
    template = read("templates/LOOP_STATE.template.md")
    absent = [h for h in required if not re.search(rf"^{re.escape(h)}\s*$", template, re.MULTILINE)]
    check("§6 table found", bool(required), "no `## ` rows parsed from LOOP.md §6")
    check("template has every §6 section", not absent, ", ".join(absent))


def check_state_version(manifest: dict) -> None:
    """This repo's own state file names each plugin's version in its Artifact line.

    It said 0.10.0 for four releases after 0.10.0. A version written by hand in two
    places drifts; this derives the comparison instead of trusting either copy.
    """
    print("\nstate file agrees with the manifest")
    state = read("docs/plans/LOOP_STATE.md")
    status = state.split("## Current status", 1)[-1].split("\n## ", 1)[0]
    for plugin in manifest.get("plugins") or []:
        name, version = plugin.get("name"), plugin.get("version")
        found = re.findall(rf"`{re.escape(str(name))}` (\d+\.\d+\.\d+)", status)
        check(f"state file names {name} {version}", found == [version],
              f"Current status says {found or 'nothing'}, marketplace.json says {version}")


# Phrases that promise every consumer is pinned to a release. Round 4 found the
# promise false: every non-plugin path this repo documents fetches from `main`.
UNSCOPED_PINNING = ("A merge alone changes nothing downstream", "Downstream projects are pinned",
                    "downstream projects never receive it", "why a merge alone changes nothing")
PINNING_DOCS = ("CONTRIBUTING.md", "CHANGELOG.md", "docs/ADOPTING.md", "README.md", "AGENTS.md",
                ".github/ISSUE_TEMPLATE/config.yml")


def check_pinning_claims() -> None:
    """A doc may not promise pinning while a documented path fetches from main.

    Derived, not trusted: the fetch paths are read from the templates and docs
    that tell a project how to consume the loop. If none of them fetched
    `main` any more, the promise could stand.
    """
    print("\npinning claims match the documented fetch paths")
    sources = ["docs/ADOPTING.md", "llms.txt"] + [
        f"templates/{n}" for n in sorted(os.listdir(os.path.join(ROOT, "templates")))
    ]
    fetch_main = [p for p in sources if re.search(r"raw\.githubusercontent\.com/[^\s)]*/main/LOOP\.md", read(p))]
    claims = [f"{d}: {phrase!r}" for d in PINNING_DOCS for phrase in UNSCOPED_PINNING if phrase in read(d)]
    check("some documented path is found", bool(fetch_main), "no path fetches LOOP.md from main")
    check("no doc promises pinning to every consumer",
          not (fetch_main and claims),
          f"{'; '.join(claims)} — but {', '.join(fetch_main)} fetch LOOP.md from main")


def check_hooks() -> None:
    """The example hooks are code people copy, so they get tested like code."""
    print("\nhooks")
    try:
        with open(os.path.join(ROOT, "hooks", "settings.example.json"), encoding="utf-8") as fh:
            json.load(fh)
        check("hooks/settings.example.json parses", True)
    except (OSError, ValueError) as exc:
        check("hooks/settings.example.json parses", False, str(exc))
    run = subprocess.run([sys.executable, os.path.join(ROOT, "hooks", "test_hooks.py")],
                         capture_output=True, text=True, timeout=60)
    tail = (run.stderr or run.stdout).strip().splitlines()[-1:] or ["no output"]
    check("hooks/test_hooks.py passes", run.returncode == 0, tail[0])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        help="git ref to compare against for the version-bump check (e.g. origin/main)",
    )
    args = parser.parse_args()

    manifest = check_manifest()
    check_skills()
    check_links()
    check_inertness()
    check_docs_derive()
    check_state_version(manifest)
    check_pinning_claims()
    check_hooks()
    if args.base:
        check_version_bump(args.base)

    version = (manifest.get("plugins") or [{}])[0].get("version", "?")
    print(f"\n{checks_run} checks, {len(failures)} failed (version {version})")
    if failures:
        print("\nfailed:")
        for name in failures:
            print(f"  - {name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
