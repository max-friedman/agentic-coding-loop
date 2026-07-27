---
status: released
filed: 2026-07-27
area: protocol
issue: "#3"
released-in: "0.4.0"
---

# 002 — The branch rule fired after the point of no return

## What happened

The branch instruction lived in §D under the unattended-run absolutes. Two defects,
and the second is the one that matters.

It was scoped to unattended runs, so an attended round had no branch instruction
anywhere. And even where it applied, it fired too late: "ship via pull request" is
unfollowable once the work is already committed to the default branch, because
there is nothing left to open a PR from. The only recovery is the history surgery
the same section forbids.

## What it cost

Four rounds out of four committed straight to the default branch while the rule
existed and was read. No review gate and no revert boundary for any of them. The
project's first four rounds have no PR trail; every round after does.

Ancillary: a formatting sweep landed mixed into logic changes, because there was no
PR to structure commits around.

It did not self-correct. It was found by a round that took the loop itself as its
target, not by any round following the protocol.

## Disposition — MERGE, placement amended

Accepted. The branch step now opens **§1**, before any edit.

### Why this cleared the bar

The submitter proposed a step reordering and explicitly declined to propose a
principle — "the general form, *if it is worth stating*." That instinct is the
reason this merged. A rule that four rounds ignored while reading it is not fixed
by a better-written rule; the rubric rejects prose where a mechanism was available,
and this brought the mechanism.

Corroborating evidence the submitter did not have: `LOOP.md` §D reproduced the
identical misplacement independently, in the file meant to encode the lesson. Two
independent instances is a pattern, not an incident.

### Placement resolved against the primary proposal

The proposal put the step in §0. Its own second objection argued for §1 instead,
and that objection wins: §0 is reads and checks, and making it the first
state-mutating step muddies a clean boundary for no gain. §1 works because nothing
is edited until §3, so the branch still precedes the first change — the only
property that actually matters.

§D keeps "never commit to the default branch" as the unattended-specific absolute.
It is no longer load-bearing but it is not redundant either, since unattended runs
additionally require the pull request.

### Objection rejected

> It may be self-correcting in practice. The cost is bounded to the early rounds of
> a project, which is also when the stakes are lowest.

The cost is not bounded: unreviewable history is permanent, and the submitter's own
project retains four rounds with no PR trail because the only remedies were history
surgery or acceptance. "Self-correcting" also does no work here — it corrected
because an audit went looking, not because the protocol noticed. A failure that
requires an audit to surface is the failure this loop is built around.
