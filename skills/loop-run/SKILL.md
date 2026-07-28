---
name: loop-run
description: Run the improvement loop continuously — repeated rounds against docs/plans/LOOP_STATE.md, re-reading the state file each time, until a stop condition fires. Use when asked to run the loop rather than a single round, to keep improving a repository, or to work through the queue.
when_to_use: Continuous or repeated improvement work is wanted, not one round. Trigger phrases include "run the loop", "keep going", "work through the queue", "run rounds until you are blocked", "improve this until done". For exactly one round, use loop-round instead.
argument-hint: [round budget, default 3]
---

# Continuous loop

Run rounds **repeatedly** until a stop condition in §D fires.

Round budget: $ARGUMENTS — default **3** if unspecified, **1** if no human is
present in the session. Never raise it on your own initiative.

## Sequence

For each round:

1. Re-read `docs/plans/LOOP_STATE.md` **from disk**. Treat your memory of earlier
   rounds as stale — carry conclusions through the file, not through context. If
   the file alone is not enough to proceed, the previous round wrote it badly:
   record that as a finding.
2. Run §1–§6 of the protocol below.
3. Commit. The commit is the round boundary — never start the next round's changes
   before it exists.
4. Evaluate the §D stop conditions. If none fire and budget remains, go to 1.

## Stop immediately when

Any §D condition fires. The non-negotiable ones: a red gate, a round that would
require weakening a standing invariant, an empty queue, two consecutive `blocked`
rounds, a round with no commit, or the same item attempted twice without shipping.

Report which condition fired. Do not push through it, and do not substitute
invented work for an empty queue.

## If unattended

No human in the session means the §D unattended rules are in force: work on
`loop/round-N` and open a pull request, never commit to the default branch, never
force-push, never spend money without prior recorded approval, and drop the budget
to 1.

## Report at the end

One line per round — number, title, ending state (`shipped` / `refuted` /
`blocked` / `rejected`) — then the stop condition that fired and anything added to
NEEDS-MAX. The state file holds the detail; do not restate it.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`
