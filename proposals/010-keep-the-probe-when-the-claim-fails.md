---
status: proposed
filed: 2026-09-07
area: protocol
issue: "#30"
released-in: ""
---

# 010 — §A step 6 keeps the probe only when the claim HOLDS, but the failing case is the one that needs it

## What happened

§A step 6:

> If it fails: correct the claim in the doc that makes it, immediately, weakening the
> wording to what the evidence supports. Queue the fix at the top.
> If it holds: **wire the probe into the gate** and add the threshold to the standing
> invariants.

The probe is preserved exactly when it has the least left to do. A claim that
**holds** has a probe that will pass indefinitely. A claim that **fails** has a probe
that is the *definition of done* for the round that later fixes it — and that is the
branch where the protocol says nothing about the probe, so it is discarded with the
audit.

## What it cost

An audit measured a central claim, found it false, produced a headline number over a
corpus, and correctly changed no behaviour (step 5). Per step 6 the claim was
reworded and a fix queued at the top. The probe was **deleted** and the corpus was
**not committed** — it was user data and the project had a standing precedent against
committing it. Every one of those decisions was defensible alone.

Consequences, in order:

1. The next round shipped a **partial** remedy. It fixed the narrow question the
   queue item named and had no way to tell it had missed most of the symptom, because
   the number that defined the symptom was no longer runnable.
2. The queue item carried the original, now-wrong number for roughly 27 rounds.
3. The round that eventually closed it could re-measure only the three examples the
   audit happened to write down in prose. Those were enough to prove the defect was
   still live and to drive a fix, but that round could not produce a real
   before/after, and shipped saying so: its headline improvement is an **inference
   from the mechanism**, not a measurement.

Point 3 is the actual loss. §A's whole value is that it produces a number instead of
an opinion, and the number evaporated between the round that found it and the round
that fixed it.

## The asymmetry worth naming

The `holds` branch produces an artifact guarding a property that is *already true*.
The `fails` branch produces an artifact measuring a defect the project has *just
committed to fixing* — the one with a consumer already waiting. The protocol
preserves the first and drops the second.

## A worked example from the next audit

The submitter deliberately did the opposite on the following audit, to test whether
it was worth the words.

That audit found a claim false: a renderer's fallback for unknown node types could be
deleted entirely, so unrecognised content rendered as nothing at all, with the
project's full ~2000-test gate still green. Per step 5 nothing was fixed; per step 6
the claim was corrected and the fix queued. **Against step 6, the mutation harness
shipped runnable.**

The next round added the missing assertions and re-ran that harness. Both mutations
went UNCAUGHT → CAUGHT, with the specific test names that now go red. That round's
pull request contains a real before/after table instead of an argument that the fix
ought to work, and it cost one small script written during the audit, while the
mechanism was still in hand.

## How often

Once with a measured cost, plus one deliberate counter-example showing the cheaper
path works. Rounds run: 100+ in the submitting project.

## Proposed change

The reviewer writes the change; these are shapes, not copy.

- Symmetrise step 6: **on `fails`, commit the probe alongside the queued fix.** Not
  wired into the gate — it is red by construction — but runnable, so the fixing round
  inherits its own before/after.
- Where the corpus genuinely cannot be committed (user data, credentials, licence),
  say so explicitly and require the queue item to record **how to reconstruct it** and
  **what the number was**, so the fixing round knows up front what it cannot reproduce
  rather than discovering it late.
- Weakest version, still an improvement: require the fixing round to state whether it
  re-ran the original measurement, and if not, to mark its result as inference. The
  round above did that voluntarily; nothing asked it to.

## Blast radius

A committed-but-red probe is a new artifact class the protocol does not currently
have, and projects will need to know it is not a broken test. For a project whose
audits mostly hold, this branch rarely fires and costs nothing. For one whose audits
fail often — the projects §A is most valuable to — it adds one small committed script
per failed audit.

## Why this might be wrong

A red-by-construction probe sitting in a repository is a standing invitation to
misread the suite's state, and the weakest variant above (require the fixing round to
say whether it re-measured) captures most of the value for none of that risk. A
maintainer could reasonably take only that.

There is also a scoping question the submitter does not settle: a probe worth
committing is one worth maintaining, and nothing in the proposal says when a
committed-but-red probe should be deleted if its queue item is dropped.

## Overlap checked by the submitter

Not #22 (proposal 006) — that concerns step **3**'s import-independence requirement, a
different clause. The two compound, though: mutation-style probes are especially worth
keeping, since they edit the machinery and are hardest to reconstruct from memory.
Not #21 (proposal 005, cadence). Not #26 (proposal 008), though they share a root —
a number outliving the means of reproducing it. #19 (proposal 004) is adjacent and
the submitter added the instance there rather than re-arguing it here.

---

<!-- Maintainer use below this line. -->

## Disposition

_None yet. Accepted for consideration on 2026-09-07 — triaged, not judged. No
change has been written, and nothing here affects the protocol until one is._
