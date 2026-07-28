---
name: loop-roast
description: Run a roast round — meet the product as a first-time user with no goodwill, write an unkind verdict, and turn the complaints that survive a falsifiability test into queue items. Use when the improvement loop's queue is empty and the project should keep going, or when asked to critique a project as a user rather than as its maintainer.
when_to_use: The queue in docs/plans/LOOP_STATE.md is empty and the loop is configured to continue, or a user-facing critique is wanted. Trigger phrases include "roast this", "what would a user hate about this", "the queue is empty, keep going", "review this as a product manager". Ships no features by design. For auditing a technical claim instead, use loop-audit.
argument-hint: [optional entry point or user journey to roast]
---

# Roast round

Run **§E** of the protocol below. Ship no features. The deliverable is a critique
and the queue items that survive it.

The journey to run, if given: $ARGUMENTS — otherwise pick the entry point a new
user would actually reach first.

## Before starting

Read `## Loop configuration` in `docs/plans/LOOP_STATE.md`. If `roast-on-empty` is
off and no human asked for this directly, the empty-queue stop condition applies —
say so and stop rather than roasting anyway.

Read `docs/plans/ROAST_LOG.md` if it exists. You are deduplicating against it, not
starting fresh.

## The one rule that makes this honest

**Every complaint must cite something a user could hit** — a command you actually
ran and its actual output, a page they land on, a step they must perform. A
complaint you could only make by reading the round history, the coverage map, or
an internal design doc is struck before it reaches the table.

You are roasting the product, not the code. Run the thing.

## Citing something is not the same as diagnosing it correctly

Before the verdict, check each surviving complaint against ground truth (state,
logs, a second run) and tag it real, critic-mistake, or environment-artifact.
Only *real* complaints shape the verdict or reach the queue — a critic can
genuinely see a real screen and still guess wrong about why it looks wrong, or be
looking at a test-harness artifact a real user could never hit. Ground truth may
only correct or drop a complaint that turns out to be unreal; it may never explain
away a complaint a real user would still experience.

## Finding nothing is a result

A roast that produces no complaint not already in the log means the loop is
exhausted and should stop — report that, do not manufacture a complaint to justify
the round. A queue refilled with plausible-sounding tasks is worse than an empty
one, because the empty queue was telling you something true.

## Never write the configuration

`## Loop configuration` is human-set. A round that enables its own `indefinite`
setting has removed the only limit on it.

## Report at the end

The verdict, how many complaints survived to the queue, how many were noted but not
queued, and the **new this roast** count. If that count is zero, say the loop is
exhausted and stop.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`
