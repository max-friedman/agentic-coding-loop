---
id: C4-cost
expect: REJECT
criterion: "Criterion 4 — cost"
why: Real and general, but sixty lines of recurring cost for a rare failure.
---
### Area
State file (LOOP_STATE.md structure)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
The state file's `## Queue — next rounds` section is an ordered list of questions.
Ordering is done by the round that writes it, using judgment, with no record of why
one item outranks another. Two rounds re-ordered the queue in opposite directions on
consecutive firings, because each had a different implicit ranking criterion and
neither could see the other's.

### What it cost
One round's item choice was effectively arbitrary, and a genuinely urgent item sat
at position four for three rounds because nothing recorded why it had been ranked
there.

### How often
Once

### Rounds run
11

### Proposed change
Replace the queue section with a scored table and a documented scoring procedure:

> Each queue item carries four scores from 1 to 5 — *uncertainty reduced*,
> *blast radius if wrong*, *cost to build*, *decays if deferred* — and a rank equal
> to (uncertainty x blast radius) / (cost x decay). The round writes the four scores
> and the arithmetic. Re-ranking requires changing a score and saying which
> observation moved it.
>
> The scoring rubric for each dimension, with worked examples for all four, follows
> in a table of sixteen rows so that two sessions score the same item identically.

Roughly sixty lines in `LOOP.md`, covering the procedure and the rubric.

### Blast radius
Every project scores every queue item every round. Projects with a three-item queue
pay the full procedure for a ranking that was never in doubt.

### Why this might be wrong
The failure happened once in eleven rounds, and the fix is one of the largest
additions anyone could make to a file that loads in full every round. A single line
telling the round to record its ranking reason would capture most of the benefit at
a fraction of the recurring cost.
