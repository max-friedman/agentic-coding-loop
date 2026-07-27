---
status: released
filed: 2026-07-27
area: protocol
issue: "#2"
released-in: "0.4.0"
---

# 001 — "The gate is green" is unverifiable when the gate runs on one machine

## What happened

§5.1 required the gate to be green with no exceptions, and never asked where it
ran. A project reported a green suite across five consecutive rounds. A later round
added CI and it failed on its first run: dev tooling was declared as an
optional-dependencies extra rather than a dependency group, so the runner installed
neither the test runner nor the linter. The suite had never once executed in a
clean checkout.

Every green-gate claim in five round writeups was true, and true only on the one
machine where the extra had been installed by hand.

## What it cost

Five rounds of unverifiable claims, recorded in the state file as verified. The
packaging defect was latent for the project's life and would have surfaced first
for an outside contributor rather than the author.

The deeper cost is that §5's strong guarantee silently degraded to "green once,
locally" with nothing in the protocol positioned to notice.

## Disposition — MERGE, narrowed

Accepted at the narrowest scope. Shipped:

- **§0 precondition 5**, framed around the verifiability of the §5 claim rather
  than around CI as infrastructure. The escape hatch is "record why", not "add
  CI", so it cannot become a blocker for a project where CI genuinely cannot run.
- **A hard-rules row**: *a gate that has never failed is not yet known to be a
  gate.* The submitter reported this framing did more work than the precondition
  itself — it made a red first run legible as the system working rather than a
  setback. It is also the more portable half, since it survives in projects with no
  CI at all.

Dropped from the proposal: the claim that CI is free on public repositories. A
vendor pricing detail inside a provider-agnostic protocol is a line that rots.

### Why the strongest objection did not sink it

The submitter's own first objection was the best one: the loop is deliberately
tight, and "set up CI" is advice any competent engineer already holds. That
argument wins against a proposal to *add CI*.

It loses here because §5 already promises "both green, no exceptions" — a guarantee
the protocol makes and never checks. A claim verifiable only on the machine that
produced it is precisely the failure this loop exists to catch: true, unfalsifiable,
and degrading silently. This closes a hole in an existing step rather than importing
general engineering practice.

### Unresolved

This issue cited five rounds; #3 cited four for the same history. Reconcile when the
round count is next written down.
