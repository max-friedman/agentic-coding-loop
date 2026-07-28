---
id: M1-unenforceable-stop
expect: MERGE
criterion: "Passes all eight — makes an existing stop condition checkable"
why: Evidenced, general, mechanism-shaped, tiny; turns a rule that cannot fire into one that can.
---
### Area
State file (LOOP_STATE.md structure)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
§D stops the sequence when "the same item has been attempted twice without
shipping." Nothing records an attempt. A round that pulls an item, works it, finds
it mis-scoped and puts it back leaves no trace in the state file — the round section
describes what it did instead, and the queue entry is unchanged. A fresh session
starting the next round therefore cannot know the item has been attempted at all,
let alone twice.

The same item was picked up in three separate rounds. Each session read the queue,
saw a reasonable-looking item at the top, started it, discovered the same
mis-scoping the previous two had discovered, and redirected. The stop condition
existed the whole time and could not fire, because the fact it depends on was never
written down.

### What it cost
Two rounds effectively repeated a third. The mis-scoping was rediscovered from
scratch each time, and the item was only split when a human happened to read three
consecutive round sections together and noticed the pattern.

### How often
A few times

### Rounds run
17

### Proposed change
Make the attempt count a field the queue carries, so the condition reads a number
instead of requiring memory:

> §6, `## Queue — next rounds`: an item a round started and did not ship carries an
> attempt count and one line naming what stopped it.

§D's condition then checks that number rather than depending on a session
remembering rounds it never saw.

This adds no step. It writes down the fact an existing stop condition already
depends on — the condition was unenforceable as written, which is why it never
fired.

### Blast radius
Projects whose rounds always ship: no change, no item ever carries a count.
Projects where an item is abandoned: one number and one line, written by the round
that abandoned it, at a moment when the reason is still known. No existing
`LOOP_STATE.md` becomes invalid — an absent count reads as zero.

### Why this might be wrong
The strongest argument against is that the round section already records a
redirected round, so the information is technically present and the real failure was
a session not reading the history carefully enough. If that is the right reading,
the fix is not a new field but making §0's read of past rounds more deliberate — and
adding a field would then be treating a reading failure as a data failure. I think
the data reading is correct, because the cost of finding the pattern scaled with the
number of round sections between the attempts, which is exactly what a counter
removes. But a reviewer who thinks §0 is the real defect has a case.
