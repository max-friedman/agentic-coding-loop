---
id: C2-generality
expect: REJECT
criterion: "Criterion 2 — generality"
why: Real evidence from one project, shaped by its stack, with no argument that it generalizes.
---
### Area
Round protocol (the seven steps)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
§5.3 says to re-run measurements from earlier rounds that the change could have
moved. Determining *which* earlier measurements a change could have moved requires
knowing what the measurement depends on, and the protocol offers no way to record
that. In practice rounds either re-ran everything or guessed, and guessing missed a
regression: a change to a tokenizer moved a metric established four rounds earlier,
and nobody re-ran it because the connection was not obvious from the diff.

### What it cost
One silent regression that stood for four rounds before an audit found it. The
metric had been quoted in two documents in the meantime.

### How often
Once

### Rounds run
10

### Proposed change
Have each measurement declare its inputs when it is created:

> §3: when the check is written, record the module paths it depends on in the state
> file's coverage map. §5.3 re-runs any measurement whose declared paths intersect
> the round's diff.

This turns "measurements this could have moved" from a judgment call into a set
intersection.

### Blast radius
One extra column in the coverage map, filled in when a measurement is added.
Projects with few measurements barely notice.

### Why this might be wrong
Path-level dependency is a crude proxy — a change can move a metric without touching
any declared path, through configuration or data. It would produce false confidence
in exactly the case §5.3 exists for.
