---
id: M2-gate-drift
expect: MERGE
criterion: "Passes all eight — closes a silent divergence between recorded and executed gate"
why: Evidenced, general, one clause, makes drift fail loudly instead of passing quietly.
---
### Area
Round protocol (the seven steps)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
`## Current status` records the gate command. §5.1 says to run the project's gate
command. Those are two different things and nothing checks that they agree.

The project's gate command changed when the build tooling was replaced. The rounds
around that change ran the new command, correctly, and never updated the state
file's record of it. Several rounds later a fresh session did what §0 tells it to —
read the state file, treat it as the memory — and ran the command written there. It
was a stale entry point that still existed and still exited zero, but no longer ran
the linter. Three rounds reported a green gate having run roughly half of it.

### What it cost
Three rounds of green-gate claims covering less than the gate. Two lint violations
shipped and were found when a fourth round ran the current command by coincidence.

### How often
A few times

### Rounds run
14

### Proposed change
One clause in §5.1, so the recorded command and the executed command cannot silently
diverge:

> Run the gate command **as recorded in `## Current status`**. If it is not the
> project's current gate, correcting the record is the round.

The check costs nothing when they agree, and when they disagree it converts a silent
divergence into an explicit round.

### Blast radius
Projects whose recorded gate is current: no change — the clause reads as satisfied
and adds no work. Projects where it has drifted: one round spent correcting a record
that was already wrong and already being trusted. Nothing about the state file's
shape changes, so existing files stay valid.

### Why this might be wrong
The strongest counter is that this is a special case of a rule the protocol already
has: §5.4 requires updating every document quoting something the round changed, and
the gate command is arguably such a thing. If that reading holds, this adds a second
statement of an existing rule, and duplication drifts — which is the failure mode
the rubric warns about most. My argument for it anyway is that §5.4 is scoped to
numbers a round *changed*, and the round that changes the gate command is often not
the round that notices the record is stale; the drift is discovered by a later
session that changed nothing. But that distinction is fine enough that a reviewer
could reasonably call it duplication.
