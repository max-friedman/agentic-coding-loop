---
name: loop-round
description: Run one round of the continuous-improvement loop on this repository, driven by docs/plans/LOOP_STATE.md. Use when the user asks to run a round, continue the loop, or pick up the improvement work where it left off.
disable-model-invocation: true
argument-hint: [optional item to work on]
---

Run **one** round of the improvement loop on this repository.

$ARGUMENTS

## Read first

1. `docs/plans/LOOP_STATE.md` — in full, including the sections at the bottom. It
   is the only memory of previous rounds. If it does not exist, stop and tell the
   user to run `/loop-init` first.
2. The project rules file (`CLAUDE.md` or `AGENTS.md`).

If the user named a specific item above, do that item and skip the queue ordering.

## The round

**1. Pick exactly one item.** From the queue, unless a finding from the last round
makes something else clearly more urgent — then take it and say why in the writeup.
One item, not three: a round that half-lands three things leaves the next round
unable to attribute a regression to any of them.

**2. Ask what would prove it wrong.** Write the question the round answers into
your notes before building. If no outcome would count as bad news, you picked a
task, not a round — reframe until a negative result is possible.

**3. Build the check before the thing, and run it on the current code.** The
measurement lands first and produces a *before* number from the existing state. A
check written afterward tends to be one the new code already passes, and without a
before number "it improved" cannot be falsified.

**4. Build it.** Keep the repo shippable at every commit.

**5. Verify wider than you changed.**
- Run the project's gate command — tests and lint, both green, no exceptions.
- Look at real output (failures, samples, rendered results), not just the summary
  number. A metric can look reasonable while the thing underneath is visibly wrong.
- Re-run measurements from *earlier* rounds that this change could have moved.
- Update every document quoting a number you changed.

**6. Write `docs/plans/LOOP_STATE.md` last, and treat it as the deliverable.**
- Append a `## Round N` section: question, method, finding, shipped, consequences
  (verified, not predicted), and *noted, not built*.
- Rewrite **Current status**.
- Update the **coverage map**.
- Re-rank the **queue** based on what you just learned.
- Add any new **standing invariant** you encoded as a test.
- Add anything blocked to **NEEDS-MAX**.

Write it for a stranger with no context, because that is who reads it next.

## Rules

- **If a standing invariant fails, the code is wrong, not the assertion.** Never
  relax an assertion to make a round pass. If you genuinely believe an invariant is
  mis-stated, say so in the writeup and leave it failing.
- **If a claim this project makes about itself turns out to be false, that IS the
  round.** Report it plainly, fix what you can, correct the docs. Deleting a false
  claim beats adding a feature.
- **Blocked is not stopped.** Anything needing a human — a credential, a spend
  approval, a decision that isn't yours — goes to NEEDS-MAX with the exact command
  that unblocks it. Then build around the block. Never guess the result. Never
  publish a number you did not measure.
- **Never edit a previous round's section** to make the history look tidier.

## Ending

End the round in exactly one of these states, and name which in the writeup:
**shipped**, **refuted** (the measurement killed the plan — the highest-value
ending), **blocked** (moved to NEEDS-MAX, round redirected), or **rejected** (built
enough to evaluate, deliberately not kept, reasoning recorded).

There is no "partially done". If the item is bigger than a round, that finding is
the round's output: split it in the queue and stop.

Commit with a message naming the round's **finding**, not its task.

## If the round taught you something about the loop itself

Not about this project — about the loop. A step that misfires, a section of the
state file that never gets used, a failure mode the protocol does not cover.

Mention it to the user and offer `/loop-feedback`, which packages it as a proposal
for review upstream. Do not change the loop's own instructions locally to
compensate; that fork is invisible to every other project using it.
