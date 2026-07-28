---
id: M3-audit-window
expect: MERGE
criterion: "Passes all eight — makes the §C audit able to determine its own window"
why: Evidenced, general, one line, makes an existing instruction executable.
---
### Area
Round protocol (the seven steps)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
§C says to read the `Loop:` lines "from every round since the last audit." Nothing
records when the last audit happened. The cadence triggers are checkable — round
number, a stop condition, two non-`nothing` lines in a row — but the window the
audit is supposed to read is not.

In practice each audit picked its own window. One read the last five rounds because
the cadence is every fifth; one read everything back to round one and produced a
long, mostly stale list; one read back to the previous friction it could find and
missed two rounds before it. The three audits saw overlapping and inconsistent
evidence, and the middle one re-surfaced a friction that had already been examined
and dismissed.

### What it cost
One audit re-examined ground a previous audit had already covered and reached the
opposite conclusion, with no record that the question had been settled. Roughly half
a round, and a proposal drafted against a finding that had already been considered
and rejected upstream.

### How often
A few times

### Rounds run
21

### Proposed change
Have the audit record itself, so the next one can find the boundary:

> §C: an audit records the round it ran in on that round's `Loop:` line. The next
> audit reads from there.

One line, written by the audit, in a field that already exists.

### Blast radius
Projects that never reach an audit cadence: no change, the instruction never fires.
Projects that do: one extra clause on one `Loop:` line every fifth round. No new
section, no new file, and existing `LOOP_STATE.md` files stay valid — an audit with
no recorded predecessor reads from round one, which is the current behavior.

### Why this might be wrong
The strongest argument against is that audits finding the same friction twice may be
a feature rather than a bug: a friction that resurfaces after being dismissed is
evidence the dismissal was wrong, and a window that hides it would suppress exactly
the signal §C exists to catch. That is a real cost of this change, and it is the
reason to prefer recording the boundary over enforcing it — the audit can still read
further back, it just knows where the last one stopped. If a reviewer thinks the
overlap is worth more than the consistency, this proposal is not worth its line.
