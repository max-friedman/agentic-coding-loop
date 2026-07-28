---
id: D8-growth-without-deletion
expect: REJECT
criterion: "Disqualifier 8 — growth without deletion"
why: Adds a whole new section without arguing the protocol was missing a step or naming what it replaces.
---
### Area
Round protocol (the seven steps)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
Rounds routinely rediscover the project's architecture. §0 has the session read the
state file and the project rules, but neither describes the shape of the codebase —
which modules exist, what depends on what, where the seams are. Every round spends
its first stretch re-deriving this by reading source, and the derivation is thrown
away when the session ends.

### What it cost
Consistently the opening portion of each round, across all of them. On one round the
re-derivation was wrong and a change landed in the wrong module, which took a
follow-up round to move.

### How often
Every round

### Rounds run
13

### Proposed change
Add a new section to the protocol, §E *Architecture memory*:

> Maintain `docs/plans/ARCHITECTURE.md` alongside the state file. It records the
> module graph, the seams, and the invariant boundaries. Read it in §0 after the
> state file. Update it in §6 whenever a round adds, removes, or moves a module.
> Where it disagrees with the code, the code is right and the round fixes the file.

Roughly fifteen lines in `LOOP.md`, plus a template.

### Blast radius
Every project gains a second memory file to maintain. Small projects with three
modules pay the maintenance cost for very little.

### Why this might be wrong
The state file's coverage map already gestures at this, and two memory files drift
apart — which is the argument `CONTRIBUTING.md` makes for not keeping a
`LOOP_STATE.md` in this repo. If the coverage map were extended instead, the same
benefit might arrive without a new file.
