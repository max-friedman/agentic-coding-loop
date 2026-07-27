---
name: loop-audit
description: Run an audit-only round — ship no features, measure whether the strongest claim this repository makes about itself still holds. Use when the loop has been green for several rounds, when the user suspects drift, or when they ask to audit or stress-test a claim.
disable-model-invocation: true
argument-hint: [optional claim to audit]
---

Run a round that ships **no features**. The deliverable is a measurement.

$ARGUMENTS

## Why this exists

Several rounds in a row where everything passes and everything ships usually means
the checks stopped being adversarial, not that the work is finished. Uninterrupted
green is a signal to audit.

## The audit

**1. Read `docs/plans/LOOP_STATE.md` and the project rules.** If the user named a
claim above, audit that. Otherwise pick the target yourself:

Find the **strongest claim the project makes about itself** — in the README, the
docs, or a section heading. Prefer, in order:
- a claim that is central to the project's value ("this design prevents X")
- a claim that has never been measured
- a claim whose supporting test would still pass if the claim became false

That last one is the sharpest test. A property with no adversarial probe behind it
is a property that can rot silently.

**2. State the claim precisely, and state what would falsify it.** Write both down
before measuring. Include the number that would count as failure.

**3. Build the probe.** Independent of the code under test — it should not import
the machinery whose output it is checking, and it must not be able to see the
answer. Where the project's own tests and the probe disagree, the probe is the one
you trust, because the tests were written by whoever wrote the claim.

**4. Run it. Report the number.** Especially if it is bad. A refuted claim is the
most valuable thing this skill can produce.

**5. Do not fix it in this round.** If the claim fails, the fix is a *separate*
round with its own before/after. Fixing inside the audit destroys the before
number and lets the fix be shaped by the same assumptions that produced the bug.
Record the finding and put the fix at the top of the queue.

## Write up

Append a round section to `docs/plans/LOOP_STATE.md`:

- the claim, quoted verbatim from wherever it appears
- the falsification threshold, set before measuring
- the probe, and what it deliberately cannot see
- the number
- the verdict: **holds**, **fails**, or **unmeasurable as stated**

If it fails, also correct the claim in the doc that makes it — immediately, in this
round. A claim known to be false must not survive the session that disproved it,
even when the fix is queued for later. Weaken the wording to what the evidence
supports rather than deleting the section outright.

If it holds, keep the probe. Wire it into the gate so the next regression is caught
automatically, and add the threshold to the standing invariants.

Then re-rank the queue and report to the user.
