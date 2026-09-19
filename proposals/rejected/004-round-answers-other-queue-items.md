---
status: rejected
filed: 2026-07-30
area: protocol
issue: "#19"
released-in: ""
---

# 004 — A round answers queue items other than its own, and nothing sweeps them

## What happened

§6 tells a round to update the state file: append its round section, update its
coverage row, re-rank the queue. Every one of those is scoped to *the round's own
item*. Nothing asks whether the round's finding also answered a **different**
queue item.

It routinely does, because a round that disproves a suspicion about a subsystem
tends to disprove neighbouring suspicions about the same subsystem in passing.
Those neighbours keep sitting in the queue looking open.

Three instances in one eight-round sequence on one project:

1. A queued batch of four related suspicions. When a round finally picked it up,
   three of the four were already settled — two disproven by an earlier round
   investigating something else, which recorded its finding only in its own
   coverage row, and the third fixed outright by a merged change. The batch had
   been carried as open for roughly eight rounds.
2. A queue item whose premise a later round found to be false: the behaviour it
   described as missing was deliberate, and documented in the very code it
   referred to. Nothing had rechecked the premise since it was filed.
3. A standing invariant recorded as having no known enforcing test. It had one —
   three, in fact, across different paths. The enforcement existed but had never
   been catalogued, so the entry honestly and wrongly said it was unenforced.

## What it cost

A full round spent auditing a queue batch that should have been swept
incrementally. That round produced no change to the product, only corrections to
the state file.

Beyond that, every prior round read a queue with stale items near the top and had
to re-derive whether they were still live before picking. The deeper cost is that
the queue's ordering stops being trustworthy: the state file's whole value is that
a cold agent can act on it without re-deriving, and a queue with silently-answered
items forces exactly the re-derivation the loop exists to prevent.

## How often

A few times — three instances in an eight-round sequence, with the eight-round
dwell time on the batch suggesting it had been accumulating well before that.
Rounds run: 8 in this sequence; the submitting project has run 120+ under an
informal predecessor.

## Proposed change

One line in §6, extending an update the round already performs. Current:

> Then update, in place:
> | `## Queue — next rounds` | ordered next increments, each phrased as a question |

Proposed:

> | `## Queue — next rounds` | ordered next increments, each phrased as a question.
> **Before re-ranking, check whether this round's finding answers any OTHER queue
> item — a round that disproves a suspicion usually disproves its neighbours.
> Close them with the evidence, or say why they survive.** |

This adds no step. It extends an update in progress, at the moment the finding is
freshest.

## Blast radius

Near nothing for a project with a short queue — with two or three items the check
is a glance. It costs most on a long queue, which is also where it pays most. It
cannot cause a wrong action: the outcome is either closing an item with recorded
evidence, or leaving it alone.

The mild risk is over-eager closing — a round persuading itself a neighbouring
item is answered when it is only *related*. The wording requires evidence or an
explicit reason the item survives, which is the standard §6 already applies to the
round's own claims.

## Why this might be wrong

The strongest argument against, which the submitter raises themselves: this may be
a symptom of **queue items being written badly**, not of §6 missing a step. Two of
the three instances were vague — a batch of four loosely-related suspicions in one
bullet, and an item asserting a behaviour was missing without citing where it
looked. A sharply-written queue item states its own falsifier, and a round
answering it would then be obvious rather than needing a sweep.

Under that reading the fix belongs in how items are *written* (§7 / §E's conversion
step), not in a sweep at §6, and adding the sweep would paper over the real defect
while adding recurring cost to every project forever. The submitter leans toward
proposing it anyway on the grounds that the sweep is cheap and self-limiting while
a discipline about item-writing is the kind of prose rule that gets ignored.

---

<!-- Maintainer use below this line. -->

## Disposition

**Rejected 2026-09-16 — criterion 3 (Necessity), the mechanism test.**

The proposed change was advisory prose appended to §6's queue row: check whether
this round's finding answers any other queue item. The mechanism test rejects "a
rule that could be a test, a stop condition, or a step reordering, but is proposed
as advisory prose," and a mechanism was available — the filing named it itself, in
its own counter-argument and again in its follow-up comment: an item that records
*how to re-measure* is self-checking, and does not need a sweep to notice it has
gone stale.

Its own fourth instance is the sharpest argument against the sweep specifically.
That round *knew* it had partly settled the item and recorded the fact in a code
comment with its own round number. A §6 step asking "did my finding settle another
item?" would have been answered "yes, and I recorded it" — and the queue would
still not have learned.

Criterion 1 (Evidence) passed outright: four instances, a ~27-round dwell on the
top-priority item, and a full round spent producing only state-file corrections.
This was not rejected for thin evidence.

**What would change the answer:** the structural form instead of the sweep — items
carrying the measurement or falsifier that would settle them, enforced where items
are *written* (§6's queue row, §E step 5) rather than where they are read. See also
[proposal 012](012-lists-that-record-a-decision-go-stale.md), whose evidence belongs in
the same resubmission.

Full verdict, with the criterion-by-criterion record: [#19 comment](https://github.com/max-friedman/agentic-coding-loop/issues/19#issuecomment-5697433318).
