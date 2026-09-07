---
status: proposed
filed: 2026-09-02
area: state-file
issue: "#21"
released-in: ""
---

# 005 — The §A/§C audit cadence cannot fire itself, and was missed by nine rounds twice

## What happened

§C says an audit runs every fifth round. In practice it has run when someone
happened to remember.

- One audit ran **nine rounds late**. Its own write-up recorded why: the cadence is
  stated in the protocol but nothing in the round checklist fires it, so it is
  remembered only if someone thinks to. It compared this to an earlier lesson in
  the same project — a rule stated where it cannot be acted on gets skipped.
- The next audit then ran **nine rounds late**, for the identical reason. The
  finding the first one wrote down did not prevent its own recurrence, because it
  too was written somewhere nobody re-reads mid-round.

Same interval, same cause, two consecutive cycles. That is a protocol property,
not a lapse of attention.

## What it cost

The first slip could only argue the cost was theoretical. The second could price
it. The audit it eventually ran mutation-tested the project's highest-stakes
standing invariant — its taint/egress security gate — and found **two runtime
protections that no test in a 1900-test suite could see leave**, plus, via the
review pass it triggered, an ungated second egress surface.

All had been in that state for the entire nine rounds, while every round in
between read an invariant list asserting the gate was covered.

The audit is the mechanism that finds this class of defect: in that project §A has
run three times and returned FAILS twice. Delaying it nine rounds at a stretch is
delaying the only check that looks at whether the other checks mean anything.

## How often

Twice, consecutively, at the same nine-round interval. Rounds run: ~97 at filing.

## Root cause

The cadence lives in `LOOP.md`, which is read when someone goes looking for
protocol. The **state file** is what §1 makes every round read first, by
construction. The rule is stated in the document that is not on the critical path.

## Proposed change

Move the *trigger* — not the rule — onto the path the round already walks. Have
the state file carry a **next-audit-due** marker that §1's read surfaces and §9's
write updates. One line, in the file the protocol already guarantees gets read.

## Blast radius

One line in the state file template and one clause in the round's write step.
Projects that already run their audits on time see a line that is always already
satisfied. Nothing is blocked, nothing halts.

## Why this might be wrong

A project running unattended may not want an audit **forced** on an arbitrary fifth
round mid-feature; a hard block could be worse than the slip. The right shape is
therefore probably *surface it as due and require an explicit defer* rather than
*stop until run* — a due-marker plus a defer-with-reason, not a gate. If that is
right, the proposal as stated is close but should not land as a blocking check.

## Evidence added after filing

The submitting project added a one-line `Audit due: R102` marker to its own state
file as bookkeeping — deliberately not a protocol fork. The audit that followed ran
**because that line was read at step 1**, not because anyone remembered the
cadence, after the two prior audits had each been nine rounds late.

That audit mutation-tested the project's hardest rule (*never delete user data
without explicit confirmation*) and measured **2 of 8 enforcement points caught, 6
uncaught** — including that inverting a destructive confirmation dialog's cancel
path left the entire suite green. First positive evidence that the mechanism does
what it claims. The counter-argument above still stands.

---

<!-- Maintainer use below this line. -->

## Disposition

_None yet. Accepted for consideration on 2026-09-07 — triaged, not judged. No
change has been written, and nothing here affects the protocol until one is._
