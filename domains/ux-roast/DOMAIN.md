# DOMAIN.md — the UX-roast domain

Additive. Everything here layers onto `LOOP.md`'s §1–7, §A, and §B — it never
restates them and never contradicts them. Read `LOOP.md` first; this file only
makes sense as a diff against it.

**Fetch this domain when:** the target project is a user-facing product (an app,
a site) where "improvement" means UX quality — confusion, missing polish, broken
flows, dishonest copy — rather than a research or benchmark claim to falsify. If
the project's central claims are about an algorithm, a dataset, or a model rather
than an experience a person navigates, this domain is the wrong fit; use core
`LOOP.md` alone.

---

## What changes vs. core

### §1 Pick exactly one item — surfaces, not files

The queue is organized by **product surface** (a user-facing flow: "drawer
search," "share-an-app," "voice input"), not by module or file. Picking an item
means picking a surface: the highest-priority open queue item, else the
**least-recently-roasted** surface in the coverage map, else a fresh
goal-driven critique of a surface nobody has framed yet.

Before picking, define the surface as a **Critical User Journey (CUJ)**:

- **Goal** — what the user wants, phrased as their desire, never a feature name.
- **Why critical** — what it proves about the product if it works, or breaks if
  it doesn't.
- **Demo flow** — the concrete, walk-on-device scenario a critic will be told to
  attempt: goal + mechanics only, never the expected behavior.
- **Success looks like** — the internal bar, not shared with the critic.

### §2 State what would prove it wrong — the falsifiable question is a critique

The round's question is answered by pointing a **critic** at the demo flow, not
by a code-level probe. Two critic roles, used for different jobs:

- **Blind critic (no context)** — discovers. Told the demo flow and nothing about
  the codebase or the expected outcome. Finds what a real user would hit.
- **Context-aware verifier** — establishes ground truth. Takes each blind-critic
  finding and checks it against the actual DB state, OS behavior, or code, and
  tags it: **real** / **critic-mistake** / **environment-artifact**. Only "real"
  findings enter the fix step. This triage is load-bearing — a blind critic
  optimized for finding problems will manufacture some; shipping a fix for a
  critic-mistake wastes the round and teaches the coverage map a false lesson.

### §4 Build it — disjoint fixes go in parallel worktrees

When a round's real findings land in disjoint files, fix them with parallel
maker agents, each in its own worktree, rather than serializing unrelated fixes
through one session. Findings that touch the same file still serialize — the
parallelism is for independence, not speed for its own sake.

### §5 Verify wider than you changed — maker ≠ checker, plus environment hygiene

Every fix gets an adversarial reviewer — a checker distinct from the agent that
built the fix — who signs off before the round ships. This is in addition to,
not instead of, the core gate.

**Reset the test environment to a realistic clean state before any first-run or
onboarding round.** Accumulated fixtures, test data, and prior-session cruft
manufacture false alarms that look like real defects — a stale-state artifact
and a real regression are indistinguishable to a critic seeing the surface for
the first time. Keep whatever long-lived credential or config is needed; clear
everything the product itself would consider a fresh user's history.

### §6 Write the state file last — coverage map by surface

The coverage map's rows are surfaces, not files or modules: `surface | last
round | verdict`. Verdict is terse — `PASS`, `FIXED`, `PASS + N fixed`, or a
one-line description of what's still open — because the full finding lives in
the round section above it, and the coverage row exists so a cold read finds the
neglected surface without opening every round.

### §D Unattended runs — the ship-policy tiers, made concrete

This domain is where LOOP.md's optional declared auto-merge tier earns its
keep, because a nightly UX-roast round produces exactly three shapes of finding,
each with an obvious ship policy:

1. **Mechanical + clearly-correct** (a crash guard, a fail-closed tighten, a
   stale-test fix, a docs correction) — maker+checker sign-off + full gate green
   → eligible for the declared auto-merge tier.
2. **Judgment-y** (changed behavior in a way a reviewer should see before it
   ships, or needed on-device confirmation the run couldn't do) — draft PR,
   no merge, no matter how confident the round is.
3. **Subjective, credentialed, or destructive** (brand/taste calls, anything
   needing a key or an account the agent doesn't have, anything that deletes
   user data) — NEEDS-MAX, never fixed, never auto-merged.

A round that can't confidently place a finding in one of these three treats it
as tier 2.

---

## What stays exactly as core defines it

Ending states, the audit round, the stop conditions, the round boundary, and the
state-file mechanics are unchanged. This domain adds a discovery/verification
method and a coverage-map shape; it does not add new ending states or new stop
conditions.
