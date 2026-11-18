# Working with the owner in this repository

Instructions for agent sessions. Project rules live in [`AGENTS.md`](../AGENTS.md);
the protocol lives in [`LOOP.md`](../LOOP.md). This file is about how to *report*.

## End substantive replies with a decision matrix

Whenever a turn leaves anything undecided, close with a table of the decisions that
are actually required — not a summary of what happened.

Give each decision its own matrix with the real options, and for each option: what it
buys, what it costs, and what happens if it turns out to be the wrong call. Mark one
option `(rec.)` and say why. Lead with a summary table when there is more than one
decision, ordered so the blocking one is first.

The purpose is that the owner can decide without reconstructing the context, and can see
what he is trading away rather than only what he is choosing.

## Route decisions away from the owner wherever the machinery allows

**The goal of the loop is that the owner is never in it except for genuinely important
decisions.** Before putting a decision in front of them, check whether something is
already supposed to handle it. This repository has three scheduled Routines:

| Routine | Cadence | Does |
|---|---|---|
| Loop round — agentic-coding-loop | Tue/Thu 09:00 UTC | Reviews and merges the previous round's PR, then runs one round |
| Loop proposal reviewer | every 6h | Verdicts on `proposal` issues, reject-by-default |
| Loop watchdog | daily 07:00 UTC | Merges PRs open ≥24h; detects a dead reviewer |

**Paused since late September 2026.** The round Routine's sessions were provisioned
without the tools to attach the repository, so every firing recorded SUCCEEDED and did
nothing ([#37](https://github.com/max-friedman/agentic-coding-loop/issues/37)). No round
has run since 2026-09-16, and nothing merges itself. Until the owner restarts the
Routines, **the owner reviews and merges every PR**; say so plainly rather than waiting
for a watchdog merge that will not come.

When they run: **do not ask the owner to merge a round pull request.** The watchdog merges
it after the 24-hour veto window, or the next round's session reviews it. Do not merge it yourself
either — §D forbids a round merging its own work, and a subagent you spawn does not
discharge that, because §D requires a reviewer that "cannot be attached to" the author.

A decision genuinely belongs to the owner when it is one no Routine is permitted to make:
anything touching `.github/workflows/`, `docs/REVIEW_RUBRIC.md`, `.github/CODEOWNERS`,
`LICENSE`, repository settings and branch protection, the state file's
`## Loop configuration`, or anything that spends money. Those escalate always,
regardless of merit — a reviewer that can rewrite its own limits has none.

If you find yourself about to ask the owner for something outside that list, the more likely
explanation is that a piece of the machinery is broken. Check it before escalating.

## Verify the machinery is alive before trusting it

A Routine that fires, finds it can't do its job, and exits still records its run as
`SUCCEEDED`. On 2026-09-07 all three Routines above had been doing exactly that —
firing on schedule, running 17 to 63 seconds, and doing nothing. The round Routine
then did it five more times, 17 to 29 September
([#37](https://github.com/max-friedman/agentic-coding-loop/issues/37)). The cause, as
#37 established: the fired sessions had **no ToolSearch and no MCP tools at all**, so
no prompt could attach the repository. Two earlier diagnoses were wrong — "no
repository attached" and "a hardcoded, namespaced tool name" — and prompt rewrites
aimed at them changed nothing. That is why the loop is paused (above).

The general rule, which is the same one the protocol applies to test suites: a green
status is not evidence of work. Check run duration and check for the artifact the run
was supposed to produce.
