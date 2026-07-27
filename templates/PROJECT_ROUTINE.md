# Running a project's loop unattended

One scheduled Routine per project. Each project keeps its own state file, its own
queue, and its own cadence — nothing is shared between them except the protocol.

## Create it

Ask Claude Code, from a session that has access to the project's repository:

> Create a Routine that fires a fresh session every weekday at 09:00 UTC, using the
> prompt below.

Then paste this, replacing `OWNER/REPO`:

```
Run ONE round of the improvement loop on OWNER/REPO, unattended.

Fetch the protocol and follow it:
https://raw.githubusercontent.com/max-friedman/agentic-coding-loop/main/LOOP.md

Round budget: 1.

If the repository has no docs/plans/LOOP_STATE.md, run §B Bootstrap instead of a
round, then stop. Do not run a round in the same session.

The §D unattended rules are in force and are absolute:
- Cut the branch before the first edit (§1). Never commit to the default branch.
- Never force-push, never rewrite published history.
- Never spend money — anything metered is a NEEDS-MAX item, not a decision.
- Never weaken the project's rules, invariants, or stop conditions to make this
  round easier. Propose upstream via §C and keep running under current rules.
- Stop at the first stop condition and name which one fired.
- Fail loudly. A silent no-op is indistinguishable from a healthy quiet day.

End by opening a pull request whose body is the round's writeup: question, method,
finding, shipped, consequences, ending state. A human merges it.

If §C says a loop audit is due, do that inside this round and file a proposal only
if there is a pattern with a cost. Most audits find nothing; report nothing found.

If there is no work — empty queue, nothing actionable — say so and stop. Do not
invent a round to justify the firing.
```

## Cadence

Match how fast the project's ground truth moves, not how often you would like
progress. Each firing costs a session and produces a diff someone must read.

| project state | suggested |
|---|---|
| Active, queue full | Daily on weekdays |
| Steady | Two or three times a week |
| Mature, queue thin | Weekly |
| Queue empty | Pause the Routine. A loop with nothing to do should stop, not generate work. |

The failure mode of a scheduled loop is not running too rarely. It is producing a
pull request every day that nobody reads, until the whole stream is ignored.

## What still needs a human

Two things, deliberately:

- **`NEEDS-MAX` items** — credentials, spend approval, decisions that are not the
  agent's. These accumulate in the state file with the exact command that unblocks
  each one. Read them when convenient; the loop keeps running around them.
- **Merging.** The round opens a pull request. Reviewing the diff is the point of
  the pull request existing.

If you want merging automated too, gate it: only branches the loop itself created,
only after a veto window, and never a change touching the project's rules,
invariants, or CI configuration. An agent that can merge changes to its own
constraints is unconstrained.

## Watch for silence

A scheduled loop that stops working looks exactly like a scheduled loop with
nothing to do. Both produce nothing.

Give the Routine a way to be noticed: push notifications on completion, or a second
Routine that checks whether pull requests have appeared recently and reports when
they have not. Absence of output is a signal only if something is looking for it.
