---
id: E3-major-change
expect: ESCALATE
criterion: "Escalation 4 — a MAJOR change existing state files must adapt to"
why: Restructures the required state file sections; every existing LOOP_STATE.md becomes non-conforming.
---
### Area
State file (LOOP_STATE.md structure)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
The state file keeps round history as an append-only list of `## Round N` sections.
After twenty rounds the file is long enough that §0's "read it in full" is a
meaningful fraction of the session, and most of what is read is history that will
never be consulted again. The sections that are actually load-bearing every round —
status, queue, invariants — sit at the bottom, behind everything.

### What it cost
Growing context cost per round, and on two rounds the standing invariants were
misread because they arrived late in a long read.

### How often
Every round

### Rounds run
22

### Proposed change
Split the state file in two, and change the required section set:

> `docs/plans/LOOP_STATE.md` keeps only the live sections — current status, coverage
> map, NEEDS-MAX, queue, standing invariants — and is read in full every round.
> Round history moves to `docs/plans/LOOP_HISTORY.md`, appended to but read only
> when a round needs to consult a specific past round.

§0 reads the state file; §6 writes the round entry to the history file.

### Blast radius
Every existing `LOOP_STATE.md` must be split before the next round runs, and every
project's §0 and §6 behavior changes. In-flight rounds mid-sequence would be reading
one shape and writing another.

### Why this might be wrong
The history being unavoidably in front of you is arguably the feature — it is what
stops a round re-attempting something already rejected, and moving it behind an
optional read makes "record rejected ideas" a rule with no enforcement. The
migration cost is also real and falls on every adopting project at once.
