---
name: loop-init
description: Set up the continuous-improvement loop in this repository — create docs/plans/LOOP_STATE.md and add the loop section to the project rules file. Use when the user asks to set up, adopt, or start the loop in a project that does not have it yet.
disable-model-invocation: true
---

Set this repository up to run the improvement loop.

## 1. Check what's already here

If `docs/plans/LOOP_STATE.md` already exists, **stop**. Report that the project is
already set up, summarize its current status, and offer `/loop-round` instead.
Never overwrite an existing state file — it is the project's only memory.

## 2. Learn the project before writing anything

The state file is worthless if it is generic. Read enough to fill it honestly:

- The README and any docs describing what the project is *for*.
- The test and lint commands (`package.json`, `pyproject.toml`, `Makefile`, CI
  config). You need the exact **gate command** that must be green before a commit.
- The existing test suite — specifically, which tests assert *properties* rather
  than behavior. Those are your candidate standing invariants.
- Any TODO/FIXME clusters, stale docs, or known-weakness sections. Those are
  candidate queue items.

## 3. Write `docs/plans/LOOP_STATE.md`

Use the template at
https://github.com/max-friedman/agentic-coding-loop/blob/main/templates/LOOP_STATE.template.md
and fill it in from what you found. Every section, even if short:

- **Current status** — round 0, the real gate command and its current state, what
  the artifact is, and the honest headline (often "unmeasured").
- **Coverage map** — one row per significant module, with how you'd know it's
  healthy. Write "unprobed" where that is the truth.
- **NEEDS-MAX** — anything already blocked on a human (a missing credential, an
  unapproved spend, an undecided product question).
- **Queue** — 3–6 candidate rounds, ordered, each phrased as a *question*.
- **Standing invariants** — the properties this project must not lose, and the
  test enforcing each. If a property has no test yet, list it and mark it
  unenforced; that is a strong first round.

## 4. Add the loop section to the project rules

Add to `CLAUDE.md` (or `AGENTS.md`), creating it if needed. The pointer goes at the
very top — it is the only thing a cold agent is guaranteed to read:

```markdown
**Working the improvement loop? Read [`docs/plans/LOOP_STATE.md`](docs/plans/LOOP_STATE.md)
first and write it last.** It holds the queue, the coverage map, the NEEDS-MAX list,
and the standing invariants. Context is lost between rounds; that file is not.
```

Then, if the file has no equivalent section, add a **Rules that protect the
project's meaning** section — the specific ways this project could stop doing its
job while every surface signal still looks healthy. Name the test enforcing each.
See
https://github.com/max-friedman/agentic-coding-loop/blob/main/templates/PROJECT_RULES.template.md

Write only rules you can justify from the code you just read. An invented rule is
worse than no rule: it gets cited later as if it were load-bearing.

## 5. Report

Show the user the queue you drafted and the invariants you found, and say plainly
which sections you had to guess at. Then offer `/loop-round` to run round 1.
