# On a team, and how to know it works for someone else

## How this maps to a team

The roles are familiar ones. Agents just make the costs show up faster.

- **The coordinator is a tech lead and release manager.** It picks work from a ranked
  list, sizes the team to what can be merged, reviews, and is the one voice to the
  stakeholder.
- **Lanes are engineers on disjoint areas.** Hotspots are code ownership. "Finish
  before starting" is a WIP limit.
- **Prelanding and the land queue are CI and a merge queue**, shifted left so most
  failures happen before a PR waits in line.
- **Independent review is code review and design QA** by someone who didn't write the
  change, against the spec, not the author's explanation.
- **"Decided, not asked" is a decision log.** Unblock yourself, make the call
  visible, keep it reversible.
- **Retros that end in a mechanism are blameless postmortems** whose action items
  actually close.

## What I'd measure on someone else's project

Everything here comes from one person. To know it works for others, I'd measure on a
second team's project, before and after adopting it:

- **Merged PRs per day and lead time** from first commit to merge.
- **Escaped defects**: bugs found after merge per 100 PRs, and how many independent
  review caught first.
- **Owner interruptions per day**, and how many "decided, not asked" calls the owner
  reversed. A high reversal rate means the line is in the wrong place.
- **Idle and wasted time**: lanes waiting, landings failed on environment, runs that
  ran nothing.
- **Hook blocks per week**, and how many were wrong.

## Plan for a first outside user

1. **Find two or three developers who already run parallel Claude Code sessions**
   and have hit at least one failure from [`PARALLEL_LANES.md`](PARALLEL_LANES.md).
   They have a reason to try it.
2. **Give them the starter** ([`STARTER.md`](STARTER.md)), not the whole protocol.
3. **Pair for one session** to set up the state file and hooks. Note every place the
   docs were wrong or unclear, and fix them that week.
4. **Let them run it alone for two weeks.** Collect the measures above from their git
   history and hook logs, with their permission.
5. **Ask them to file what broke** through the proposal form, so their findings go
   through the same review as mine.

Success: one of them keeps using it after the two weeks without me, and files at
least one finding I couldn't have.
