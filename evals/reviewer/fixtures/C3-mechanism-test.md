---
id: C3-mechanism-test
expect: REJECT
criterion: "Criterion 3 — necessity, the mechanism test"
why: Real general failure, but proposes advisory prose where a stop condition was available.
---
### Area
Round protocol (the seven steps)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
§1 says the round must take exactly one item. Across a long sequence, rounds
gradually widened: an item would be taken, a closely related fix noticed mid-round,
and both would land because separating them felt wasteful. By round twelve a typical
round touched three concerns, and when a regression appeared it could not be
attributed to any of them.

### What it cost
One regression that took two rounds to localise, because three unrelated changes
had shipped together and each looked plausible as the cause.

### How often
A few times

### Rounds run
15

### Proposed change
Strengthen the wording in §1 so the requirement is harder to rationalise past:

> MUST be exactly one. It is always tempting to fold in a small related fix found
> mid-round. Do not. The second change is a queue item, not part of this one. Three
> half-landed changes leave the next round unable to attribute a regression to any
> of them, and the cost of separating them now is far lower than the cost of
> untangling them later.

### Blast radius
Four extra lines in `LOOP.md`, read every round by every project. No behavior change
for projects already keeping rounds narrow.

### Why this might be wrong
The rule already exists and already says MUST. Restating it more emphatically may
change nothing — the sessions that widened their rounds had read the existing
wording and widened anyway. If emphasis were sufficient, the current text would have
been sufficient.
