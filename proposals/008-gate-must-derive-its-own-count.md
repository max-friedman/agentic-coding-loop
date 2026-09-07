---
status: proposed
filed: 2026-09-07
area: protocol
issue: "#26"
released-in: ""
---

# 008 — The protocol consumes a reported number without asking whether it was measured

## Provenance

Unlike 004–007, this was **not observed in a project running the loop**. It was
reported by an outside contributor as a side finding while independently
replicating proposal 007's carrier result, in a codebase nobody here can inspect.
The number below is a report, not a measurement, and it should be weighed
accordingly against proposals that priced their own cost.

It is filed separately from 007 because its blast radius is wider than the thread
it arrived on, and because its *shape* is checkable by any project in minutes —
which is the whole proposal.

## What happened

A test suite printed `37/37` while **55 checks had actually executed**. The summary
line was computed independently of the run rather than derived from the executed
set. Every gate above that suite had been reading a number that was simply wrong.

## Why this is a loop concern

The protocol consumes reported numbers at three steps, and none asks where the
number came from:

- **§5.1** — run the gate; both green, no exceptions.
- **§A step 4** — run the probe, report the number, especially if bad.
- **§6** — the number enters the state file, and every later round reads it
  *without re-deriving it*. That is the state file's purpose.

So a suite that miscounts does not produce one wrong round. It produces a wrong
number laundered into the memory the loop runs on, and every subsequent round
treats it as settled.

The protocol already holds the adjacent lesson. Proposal 001 argued *a gate that
has never failed is not yet known to be a gate*, and landed as a §0 precondition
plus a hard-rules row — both about **where** the gate runs. This is the sharper
sibling, about **whether the gate can count**:

> A gate whose summary is computed independently of its run is not a gate at all —
> no matter where it runs, and no matter how often it has gone red.

It is also recursive: a mutation score is a ratio of caught to applied, and both
halves are read off the same summary line. Where that line is decorative, every
mutation number in proposal 007 is decorative too.

## What it cost

Unquantified. Nothing is known to have been lost in any project that can be
inspected. This asks for a check on the strength of a plausible mechanism plus one
second-hand instance.

## How often

Once, second-hand. Latent for an unknown span before that.

## Proposed change

Extend the §0 precondition that already exists for the gate, since it is the same
sentence's concern. Current:

> 5. Confirm the gate runs somewhere other than this machine. A gate only ever run
>    where it was written is an unverifiable claim, not a check.

Proposed:

> 5. Confirm the gate runs somewhere other than this machine, **and that it can
>    count: once, check that the number of checks it reports matches the number
>    that actually ran, and that breaking one check moves the number.** A gate only
>    ever run where it was written is an unverifiable claim, not a check; a summary
>    line computed independently of the run is not a check at all.

Optionally sharpen the existing hard-rules row rather than adding one:

> **A gate that has never failed is not yet known to be a gate — and one whose
> count is not derived from its run is not a gate even when it fails.**

Sharpening is preferred over adding: the table is read in full every round.

## Blast radius

Near zero on a mainstream runner that reports honestly — a one-time check, never
repeated. It costs most where suites are assembled by hand or aggregated across
harnesses, which is where the defect lives.

The real cost is the wording, not the work: §0 is read in full every round,
forever, and this adds a clause to a precondition that only needs satisfying once.
That is a recurring read cost for a one-time action.

## Why this might be wrong

1. **The placement is probably wrong even if the check is right.** A one-time check
   does not belong in a per-round precondition. Two better homes: §B Bootstrap,
   where the gate command is first identified and the check is free; or §A, whose
   step 1 already says to prefer *a claim whose supporting test would still pass if
   the claim became false* — a miscounting suite is the purest instance of that
   sentence there is, and §A may already cover this without a new line.
2. **One second-hand instance, from an unverifiable source.** The mechanism is
   plausible and real in general, but this would not have been filed from a
   project's own evidence on this basis.
3. **It may be generic tooling hygiene rather than a loop concern** — the same
   objection proposal 001 had to answer.

## Measured against this repository, after filing

This repository's own gate was checked, at the then-current `main` and at the tip
of the branch about to land:

- the run counter increments **inside** the function that prints each result;
- the failure list is appended in that same function;
- the summary line reads only those two, and the exit code follows the failure
  list rather than the printed total.

The count is derived from the run. **This repository does not have the reported
defect**, and its gate cannot go green on a miscount. That is one negative
datapoint against the proposal's urgency.

The check did surface a narrowing. Two properties are conflated above, and only the
weaker holds here:

1. *the reported count is derived from the run* — satisfied;
2. *the reported count is comparable to an expected total* — **not** satisfied.

The release check returns after printing `skip` without ever registering a check,
which is correct behaviour, but it means a section that vanished entirely would be
indistinguishable from one that legitimately skipped. This gate has honestly
reported 32 and 37 checks across versions with no declared total anywhere. Property
1 is what this proposal asks for; property 2 is a stronger and more expensive ask
that one second-hand instance does not justify — recorded so the distinction
survives, not proposed.

---

<!-- Maintainer use below this line. -->

## Disposition

_None yet. Accepted for consideration on 2026-09-07 — triaged, not judged. No
change has been written, and nothing here affects the protocol until one is._
