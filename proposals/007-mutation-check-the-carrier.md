---
status: proposed
filed: 2026-09-02
area: protocol
issue: "#23"
released-in: ""
---

# 007 — Mutation-check the carrier, not just the ends

## What happened

A round fixes something by computing a value correctly at one end and consuming it
correctly at the other. Both ends get tests. Both ends pass mutation. **The carrier
between them — a plain argument at a call site inside a UI framework — is invisible
to the suite, and setting it to a constant restores the original defect with
everything green.**

Four consecutive rounds, each caught by an adversarial reviewer or an ad-hoc
mutation and never by the gate:

- A testing seam made a security branch reachable; the seam's *default binding*
  then became the new invisible spot. Caught by review.
- A taint value computed correctly, honoured correctly, and dropped in two carrier
  lines between them. Setting both to a constant restored the exact defect the
  round existed to fix, with all ~1944 tests green.
- The same shape one layer down. Five carrier links mutated; **three restored the
  full defect green.** Two were closed by naming them; one survived because nothing
  rendered the screen.
- A round that stopped finding instances and measured the population instead,
  against the project's hardest standing rule (never destroy user data without
  explicit confirmation). Eight mutations, each making one destructive path silent:
  **2 caught, 6 uncaught** — including inverting a confirmation dialog's cancel
  path on two separate dialogs, which left the full suite green.

The two that were caught are the only two that are pure functions. Every uncaught
one is a call site.

## What it cost

Four rounds *believed they had shipped coverage*. Each wrote a test named after its
fix; in one case the test named after the fix was a determinism check that would
have passed with the fix reverted.

Worse, the natural repair makes it look solved: extract the wiring into a helper
and test the helper. One round did exactly that and the invisible line simply
**moved** — from an inline null-coalescing expression at the call site to a named
helper call at the same call site, still three framework hops from any test.

The population measurement is what makes this evidence rather than anecdote: the
prediction was registered before measuring and came back exact — 2 of 8, and the
same six.

## How often

Four consecutive rounds, then measured across a population of eight enforcement
points. Rounds run: ~102.

## Independently replicated

A contributor from an unrelated codebase reported the same shape, reached from a
different direction: both ends tested with real tests, nothing covering the
connective tissue, a constant in the carrier restoring the defect with everything
green. Two components measured in one session — 16 breaks applied to one (5 caught,
11 missed), 4 applied to the other (none caught). Both suites had been green and
trusted for weeks.

Two caveats belong on that replication. Its breaks were chosen by the agent that
scored them, with nothing pre-registered, and an agent scored on defects found has
an incentive to pick breaks it expects to survive — so the ratio measures the search
as much as the grid. The reporter says as much themselves: it "produces prose rather
than a reproducible mutation score… a defect finder, not a metric."

## Proposed change

Three separable parts, in the order a round meets them.

**1. The obligation.** Add to the fix step, wherever *ship tests with the feature*
lives:

> When a fix introduces a value that travels from where it is computed to where it
> is used, **the mutation check is on the carrier, not only on the ends.** Set each
> intermediate hand-off to a constant and confirm the suite goes red. A test that
> re-derives the composition tests its own copy, not the wiring. Where a carrier
> crosses a UI-framework boundary that no test can drive, say so **in the code**,
> next to the line, rather than leaving the round's summary to imply coverage.

The generalisable one-liner: **a value that crosses a UI-framework boundary is
untested until a mutation says otherwise.**

**2. The remedy**, because the obvious repair does not work:

> Where a carrier crosses a UI-framework boundary, **drive the real component** —
> make it visible to tests if that is what it takes. Extracting the hand-off into a
> named helper does **not** discharge this: it relocates the untested line rather
> than testing it.

Both carriers closed this way needed one keyword in production code — the component
stopped being private. One immediately caught a live defect the mutation set had
missed entirely: a second destructive entry point with no confirmation at all.

**3. The finder**, optional and explicitly not a metric:

> A **breaker pass**: an agent separate from the builder, given one objective —
> prove this part does not work — scored on defects found rather than on the part
> passing, operating on a copy so the live tree is never mutated. Its output is a
> list of candidate carriers, not a score. Grading stays where §A puts it: a
> pre-registered prediction, and a real mutation-testing tool where one exists.

The mechanism claim: a builder self-checking its own work proposes breaks its own
tests already catch, because it reasons from the tests it wrote. An agent told only
*prove this is broken* goes for the carrier, because that is where the cheap wins
are. That is the insight §E already encodes for the user-facing surface, generalised
to correctness.

## Blast radius

Part 1 costs a project whose UI is thin close to pure overhead. A narrower scoping
is available and may be the right one: require it only when the carried value is a
*security or data-safety* signal, which is what all four instances were.

Part 3 costs more than it first appears. "One extra agent pass" is **per part** —
a project with many parts pays N passes — and unlike a mutation tool it leaves no
accumulating artifact. Prose findings also do not survive the round unless something
converts them into queue items and standing invariants, which the proposal does not
specify. §6 exists so a cold agent need not re-derive; a finder whose output
evaporates fails that test.

## Why this might be wrong

Mutation-checking every carrier is not free, and the submitter would rather see the
security/data-safety scoping argued than have the rule land unbounded and get
ignored.

Part 3 is the weakest of the three and should be declinable on its own. If it lands
at all, it may belong in §E's shape — opt-in, refills a queue — rather than in the
fix step, since that is where this repository already keeps a blind adversarial
pass.

## Related

Complements #22 (proposal 006), which asks §A to be re-cast around pre-registration
and notes mutation testing's blind spot: it only finds protections that *can be
removed*. This is the other half — mutation testing must also be pointed at the
right lines, and *the function that computes it* is the wrong lines. Part 3 depends
on 006's separation of finding from grading to be safe to adopt.

Underneath both sits #26 (proposal 008): whether a suite's reported numbers are
derived from its run at all. Every mutation score quoted here assumes they are.

---

<!-- Maintainer use below this line. -->

## Disposition

_None yet. Accepted for consideration on 2026-09-07 — triaged, not judged. No
change has been written, and nothing here affects the protocol until one is._
