---
id: C6-self-criticism
expect: REJECT
criterion: "Criterion 6 — self-criticism"
why: Strong on every other axis; the counter-argument section is a strawman.
---
### Area
Round protocol (the seven steps)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
§0.4 stops the round if the working tree is dirty. It does not check whether the
local branch is behind its remote. A round started from a stale checkout, built
against code that had been superseded, and the resulting diff conflicted with work
that had merged upstream in the meantime.

### What it cost
The round's work was rebuilt from scratch in the following round. Roughly a full
round lost, and the conflict resolution touched files the round had no business
touching.

### How often
Once

### Rounds run
9

### Proposed change
Extend the existing §0.4 precondition rather than adding a step:

> 4. If the working tree is dirty **or the branch is behind its remote**, STOP.
> Report it. A round must start from a clean, current tree or its diff cannot be
> attributed.

One clause, in a check that already runs.

### Blast radius
Projects working from a current checkout: no change, the clause reads as satisfied.
Projects that are behind: one fetch before starting. No new step, no new file.

### Why this might be wrong
Some people might find the extra check slightly inconvenient, and there is always a
case for keeping instructions as short as possible. But the benefit here clearly
outweighs a moment's inconvenience, and I do not think a reasonable objection to
this exists.
