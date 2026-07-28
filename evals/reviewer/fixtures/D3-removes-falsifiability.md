---
id: D3-removes-falsifiability
expect: REJECT
criterion: "Disqualifier 3 — removes a falsifiability requirement"
why: Makes the §3 before-number optional for changes deemed obviously beneficial.
---
### Area
Round protocol (the seven steps)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
§3 requires the check to land before the change and produce a before number from
existing code. On several rounds the change was a pure deletion — removing a dead
code path, deleting a doc section describing a feature that no longer exists. There
is no meaningful "before number" for deleting something that was never measured,
but the step still demanded one, so rounds manufactured trivial measurements
(line counts, file counts) to satisfy it.

### What it cost
Three rounds spent effort producing numbers nobody would ever read, and the state
file now carries measurements that look like findings but are bookkeeping.

### How often
A few times

### Rounds run
12

### Proposed change
Add a carve-out to §3:

> A before number is not required when the change is a deletion or when the
> improvement is self-evident. State in the writeup why measurement would not have
> been informative.

### Blast radius
Projects measuring everything: no change. Projects doing cleanup rounds: no more
ceremonial numbers.

### Why this might be wrong
"Self-evident" is doing a lot of work in that sentence, and every round believes
its own change is self-evidently good — that belief is the exact thing §3 exists to
test. A narrower version limited strictly to deletions would carry less risk, but I
think the broader version is more useful.
