---
id: D7-no-evidence
expect: REJECT
criterion: "Disqualifier 7 — no evidence"
why: Well-argued and entirely hypothetical; no round it ever cost anything in.
---
### Area
Round protocol (the seven steps)

### Is this evidence or preference?
Preference — nothing broke, but this would be better

### What happened
Reading §6, the writeup format asks for Question, Method, Finding, Shipped,
Consequences, Noted-not-built, and Loop. There is no field for *how long the round
took*. Over many rounds, duration is the single best signal of whether items are
being scoped correctly — a round that takes four times as long as the median is
almost certainly mis-scoped, and the protocol has a stop condition for items
attempted twice but nothing that notices an item that shipped but should have been
split.

### What it cost
Nothing yet. This is a gap I noticed reading the protocol rather than one that has
bitten a round I ran.

### How often
Once

### Rounds run
3

### Proposed change
Add one field to the §6 writeup block:

> **Duration:** wall-clock time from round start to state file write.

Over ten rounds this gives a distribution, and an outlier becomes visible without
anyone tracking it deliberately.

### Blast radius
One line per writeup. No behavior change, no new step — the number is already
knowable at write time.

### Why this might be wrong
Agent session duration is dominated by model latency and harness overhead, not by
task complexity, so the signal may be almost pure noise. And a field nobody reads is
the exact failure §C's audit questions are meant to catch — I would be adding a
candidate for future deletion.
