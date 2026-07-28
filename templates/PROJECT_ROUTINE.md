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

FIRST, review and merge the previous round's pull request per §D "Reviewing the
previous round". Read the diff against that round's own claims, not just its CI
status. Merge only if every check passes; if one fails, comment naming it, leave
the PR open, and queue the fix. Do NOT fix the PR yourself. If more than TWO
round PRs are open, stop and start no new round.

The §D unattended rules are in force and are absolute:
- Cut the branch before the first edit (§1). Never commit to the default branch.
- Never force-push, never rewrite published history.
- Never spend money — anything metered is a NEEDS-MAX item, not a decision.
- Never weaken the project's rules, invariants, stop conditions, or the state
  file's `## Loop configuration` to make this round easier. Propose upstream via
  §C and keep running under current rules.
- Stop at the first stop condition and name which one fired.
- Fail loudly. A silent no-op is indistinguishable from a healthy quiet day.

End by opening a pull request whose body is the round's writeup: question, method,
finding, shipped, consequences, ending state. Do not merge it — the next round
reviews and merges it.

If §C says a loop audit is due, do that inside this round and file a proposal only
if there is a pattern with a cost. Most audits find nothing; report nothing found.

If there is no work — empty queue, nothing actionable — say so and stop. Do not
invent a round to justify the firing. The one exception is an empty queue when the
state file's `## Loop configuration` sets `roast-on-empty` to on: run §E instead.
Never enable that setting yourself.
```

## Cadence

Match how fast the project's ground truth moves, not how often you would like
progress. Each firing costs a session and produces a diff someone must read.

| project state | suggested |
|---|---|
| Active, queue full | Daily on weekdays |
| Steady | Two or three times a week |
| Mature, queue thin | Weekly |
| Queue empty | Pause the Routine. A loop with nothing to do should stop, not generate work — unless you have deliberately enabled `roast-on-empty` (§E), which trades that stop for generated work with evidence behind it. |

The failure mode of a scheduled loop is not running too rarely. It is producing a
pull request every day that nobody reads, until the whole stream is ignored.

## Keep the project self-contained

A project running the loop must not depend on the loop's own repository to
function. Upstream ships the protocol and nothing else — no central scheduler, no
shared watchdog, no list of adopting projects.

This is not tidiness. A watchdog upstream that babysits each downstream project
grows a hardcoded branch per project, makes every project depend on infrastructure
it does not control, and puts one repository in the position of knowing about all
the others. The state file is project memory, not global memory; the same applies
to everything around it.

So each project owns its own scheduling, its own merging, and its own liveness
check. What upstream provides is this page.

## Reviewing and merging: fold both into the round

A round never merges itself. The next round's session reviews and merges it — a
fresh session that did not write the work and cannot be attached to it. That is the
only independent check in an unattended sequence, so use it as one.

Add a step before §0:

```
Before starting, review and merge the previous round's pull request per §D
"Reviewing the previous round" — read the diff against the round's own claims,
not just its CI status. Green CI proves the code runs, not that the round did
what its writeup says.

Merge only if every check passes. If one fails, comment naming it, leave the PR
open, and queue the fix as the next round's item. Do NOT fix the PR yourself —
that collapses reviewer and author into one agent.

If more than TWO round PRs are open, STOP and start no new round.
```

Three things fall out of this for free. The gap between firings is the veto window,
with no timer to configure. The backlog check makes the Routine notice its own
overproduction. And review costs no extra Routine, because the session that would
have merged anyway is already reading the diff.

The *nothing was weakened* check is the one that cannot be skipped: an assertion
relaxed or a test exempted, **regardless of green CI**. An agent that can merge
changes to its own constraints is unconstrained, and a green suite is exactly how a
weakened assertion gets through.

## Watch for silence

A scheduled loop that has stopped working looks exactly like one with nothing to
do. Both produce silence. A dead Routine cannot report that it is dead.

Pick one:

- **Push notifications on completion.** Cheapest. The weakness is that a
  notification is ephemeral — miss it and the finding is gone, with no state and
  nothing to close when fixed.
- **A second Routine** that checks whether round pull requests have appeared on
  schedule and **files an issue** when they have not. An issue persists, dedupes if
  it searches before filing, and closes when the failure clears.

Whichever you choose, it must distinguish *broken* from *legitimately idle*: read
the state file, and treat an empty queue or everything-blocked-on-NEEDS-MAX as a
correct stop. The right response to that is pausing the Routine, not repairing it.

## What still needs a human

Two things, deliberately:

- **`NEEDS-MAX` items** — credentials, spend approval, decisions that are not the
  agent's. They accumulate in the state file with the exact command that unblocks
  each one. Read them when convenient; the loop keeps running around them.
- **Reading the diffs.** Merging can be automated, as above. Knowing whether the
  project is going somewhere good cannot.
