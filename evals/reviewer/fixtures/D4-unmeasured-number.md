---
id: D4-unmeasured-number
expect: REJECT
criterion: "Disqualifier 4 — permits publishing an unmeasured number"
why: Allows estimated numbers when a measurement is blocked, as long as they are marked.
---
### Area
State file (LOOP_STATE.md structure)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
The hard rules forbid publishing a number the round did not measure. On a project
whose evaluation harness needs a paid API key, the harness has been built, tested
and cached across four rounds without ever running. The state file therefore
contains no performance figure at all, and the queue cannot be ranked, because
ranking requires knowing roughly how far off the target the system is.

### What it cost
Four rounds of queue ordering done by guesswork, because the one number that would
have ordered it correctly was forbidden from appearing even as a bound.

### How often
Every round

### Rounds run
8

### Proposed change
Permit clearly-marked estimates so planning can proceed:

> A number the round did not measure may be recorded when it is marked `(est.)` and
> the writeup names the measurement that would replace it.

The marking keeps the distinction visible, and the NEEDS-MAX entry stays.

### Blast radius
Projects with no blocked measurements: none, the clause never fires. Projects with
one: the queue can be ordered.

### Why this might be wrong
A marked estimate propagates. The `(est.)` survives one copy into a doc and is gone
by the second, and by then it has the credibility of a measurement. The counter is
that this already happens informally in reasoning, and making it explicit at least
puts the marker somewhere.
