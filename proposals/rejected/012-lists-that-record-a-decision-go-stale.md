---
status: rejected
filed: 2026-09-08
area: state-file
issue: "#34"
released-in: ""
---

# 012 — A list that records a decision has no mechanism to notice the decision changed

## What happened

A queue is a list of decisions made at a moment, read later as a standing fact.
Nothing in the protocol re-checks such a list, and the loop has guidance for the
queue only — not for the other lists a state file carries.

Three instances in ten rounds, across three different artifacts:

1. **The queue.** The top item quoted a measured number and named a fix. A round
   two later shipped that fix and recorded the new number *in a code comment,
   crediting itself by round number*. The item read as untouched for ~27 rounds.
2. **A "verify this later" tag.** An audit honestly recorded a claim it had not
   independently checked, tagged *verify before acting on it* — and sat for ~23
   rounds, because no step ever reads such a marker.
3. **A product backlog.** A round picked an item to implement, measured first, and
   found it already shipped — by a module whose own doc comment cites the backlog
   number it closes. Sweeping the line: **4 of 5 entries were already built.**

## What it cost

A round nearly rebuilt working, tested, self-documenting code. A round had two
wrong moves available before writing a line — redo shipped work, or close an item
still half-live — and only an unrequested measurement separated them. A finding was
reported from memory rather than contact, ~23 rounds late.

None produced a bad merge. All consumed a round's opening, and one nearly consumed
the whole round.

## How often

Three instances in ten rounds, three artifacts. Rounds run: ~112.

## Proposed change

Three shapes were offered, led by the cheapest: a line in the round protocol's
*find the work* step — verify the item is still live before working it. Second, the
structural form: require an item that quotes a number or names a fix to record how
to re-check it. Third, extending a sweep to cover partial answers.

## Blast radius

Not stated in the filing. This is what the rejection turns on.

## Why this might be wrong

The filing's own objection, and it is a real one: this may be unfixable by protocol
and simply the nature of written state. Every list of decisions drifts, and a rule
saying "check the list is true" is close to saying "be careful."

---

<!-- Maintainer use below this line. -->

## Disposition

**Rejected 2026-09-17 — criterion 5 (Blast radius), absent; criterion 3
(Necessity) fails for the shape it leads with.**

Criterion 5 asks what the change costs a project that never had the problem, what
breaks for a project relying on current behavior, and whether it invalidates
existing `LOOP_STATE.md` files. None is addressed. The omission is load-bearing
rather than formal, because the shape most worth accepting is the one that most
needs it: requiring items that quote a number to record how to re-check it changes
the **required format of queue items**, and every existing state file has items in
the current format. Whether old items become non-conforming decides MINOR versus
MAJOR, and the filing gives a reviewer nothing to decide it with.

Criterion 3 fails for the lead shape, by the filing's own admission — a rule saying
check the list is true is "close to saying *be careful*." That is advisory prose
added to §1, always performed and rarely changing an outcome, which §C's audit
table names as the bad answer and principle 10 says never to fix by restating.

**What passed, and it is not marginal.** Criterion 1 carries the best cost statement
of its batch, with a rate: three artifacts, ten rounds, one round nearly spent
rebuilding shipped code, and 4 of 5 backlog entries already built. Criterion 2
passes for the queue and the marker — every project has lists recording decisions at
a moment. Criterion 6 passes with the right objection. And the *not just a restated
sweep* section is the strongest analytical work in the filing: showing that a sweep
step fixes at most one of three instances — because instance 2 was settled by nobody
and instance 3 by a round that knew exactly what it closed — is what earns this a
separate issue rather than a fourth comment elsewhere.

**What would change the answer, and it is one proposal rather than two.** Proposal
[004](004-round-answers-other-queue-items.md) was rejected on criterion 3 with the
note that the structural form was the available mechanism: items carrying the
measurement or falsifier that would settle them. This filing's *second* option is
exactly that form. A resubmission should:

1. Lead with the structural shape, enforced where items are **written** — §6's
   queue row and §E step 5 — not where they are read.
2. Merge this evidence with 004's. Between them that is six instances across two
   framings; the rubric's own advice is that two thin proposals lose where one
   well-evidenced proposal wins.
3. Write the blast radius, answering the existing-item question above.
4. Be explicit that the structural shape does **not** cover instance 2. A marker no
   step reads is a different defect, self-checking or not. Either home it separately
   or drop it from the count, but do not let a three-instance tally stand behind a
   fix that reaches two.

**Considered and not decided by the reviewer:** the filing offered that if the defect
is judged inherent, recording *that* in `docs/PRINCIPLES.md` would itself be useful —
telling a round to distrust the list by default. Plausible, and a posture rather than
a step, which is what that file is for. But it is not what the issue proposed, it is
growth in a file no round must read, and choosing a posture over a rule is a
judgement about the protocol's character rather than a rubric application. Flagged
for a maintainer, not decided.

Full verdict, with the criterion-by-criterion record:
[#34 comment](https://github.com/max-friedman/agentic-coding-loop/issues/34#issuecomment-5706545220).
