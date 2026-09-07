---
status: proposed
filed: 2026-09-07
area: protocol
issue: "#29"
released-in: ""
---

# 009 — §D's session round budget and its fresh-reviewer requirement are jointly unsatisfiable

## What happened

§D is internally inconsistent about what a "session" is, across three lines:

| §D subsection | text |
|---|---|
| Stop conditions | "Round budget for the **session** is reached. Default 3." |
| Scheduling | "Interval runs inside a session. Good for supervised sequences." |
| Reviewing the previous round | "A round never merges itself. The **next round's session** reviews and merges it — a fresh session that did not write the work and cannot be attached to it." |

The first two say a session may run up to three rounds back to back, and recommend a
mechanism for doing exactly that. The third says the reviewer must be a session that
did not author the work. **Rounds after the first cannot satisfy both.**

The submitting project hit it on its first attempt to continue a sequence: a session
ran one round and opened its pull request, and starting the next round sent §0 step
4a to review that PR with only the authoring agent available. Merging it would
collapse reviewer and author into the single agent §D itself says "destroys the only
independent check in the sequence." Skipping the review is worse, because the review
step only ever looks at the *previous* round, so the unreviewed PR becomes the orphan
§D warns about two paragraphs later.

## What it cost

Two rounds not run, against a budget that said three were available.

The larger cost is that the fork is **silent**. Nothing in the protocol names this
state, so the likely behaviour is not "stop" — it is to merge one's own round and
carry on, because that is the only path that keeps the sequence moving and no rule
visibly forbids it at the moment the choice is made. §D's independence property then
holds on paper and nowhere else.

## How often

Once in the submitting project, in one session — thin, and the submitter says so.
Two things argue it is not a one-off:

- It is checkable by **reading** rather than by running, and will fire for any
  project using the default budget of 3, or the interval-runs-inside-a-session option
  §D recommends.
- The resulting state is undetectable afterwards. A self-reviewed merge is
  indistinguishable from a reviewed one in the history, so a project that already hit
  this would not know.

Rounds run: 16 in the submitting project; 1 in the session that hit it.

## Replicated, in this repository

This repository hit the same contradiction the same day, running the loop on itself.
A session ran Round 3, opened its pull request, and had no reviewer available but its
own author.

Two refinements came out of that instance:

- **It bites one round earlier than filed.** §0.4a fires at the *start* of the next
  round, so the conflict lands at the transition into round 2, not at round 3. For a
  session with no external reviewer the budget is not merely conditional — it is
  unreachable past 1. That matches the `otherwise the budget is 1` wording the
  proposal already suggests.
- **The obvious workaround does not discharge it.** Having the authoring session
  spawn a subagent to review gives independence of *context* — the subagent reads the
  diff cold — but not of *provenance*, since the author spawned it. §D's phrase "and
  cannot be attached to it" is the clause that rules this out, and it is easy to
  satisfy in appearance while failing it in substance.

The replication is weaker than the original in one respect and this should be
weighed: a human was present and reviewed, so nothing was lost. What replicates is
the structural contradiction, not the cost.

## Proposed change

Two lines, both narrow.

**1.** Add a stop condition to the §D table, where a halting rule belongs:

> | The only available reviewer is the round's author | Review requires a session that
> did not write the work. Stop; the next firing reviews it. |

**2.** Disambiguate the budget row, which currently reads as permission for something
§D forbids:

> | Round budget for the session is reached | Default 3. Reachable only where review
> comes from outside the session; otherwise the budget is 1. |

## Blast radius

None for one-round-per-firing projects — the scheduled-Routine default, and probably
most adopters. For them the budget row change makes explicit what they already do.

It bites exactly where someone runs rounds back to back, which is where the current
text produces silent self-review, and there it converts a hidden failure into a
visible stop. The honest cost is one more row in a table read in full every round,
for a condition many projects never reach.

## Why this might be wrong

1. **The empirical evidence is thin.** One session with a measured cost, plus one
   replication with no cost. The rubric ranks measured cost above logical argument,
   and this is mostly the latter.
2. **A careful reader may already resolve it.** "The next round's *session*" arguably
   implies review comes from outside the current session, which would make the budget
   of 3 conditional by implication. If that reading is obvious enough, this is a
   wording clarification, and a clarification costing a table row every round is a
   bad trade.
3. **It is growth without deletion.** The submitter could not find a row this
   replaces. The argument for adding — that a sequence halting on a rule absent from
   the stop-condition table is the exact defect that table prevents — would justify a
   row for every rule, so it deserves weighing rather than acceptance.

## Related

[#28](https://github.com/max-friedman/agentic-coding-loop/issues/28) (proposal 010's
sibling, filed the same day) is the same underlying gap seen from the other side:
§D's *open-PR* stop condition also requires a human the running session cannot
supply. Both say §D's review and independence rules assume an actor the session
cannot provide, and neither names what to do when it is absent.

---

<!-- Maintainer use below this line. -->

## Disposition

_None yet. Accepted for consideration on 2026-09-07 — triaged, not judged. No
change has been written, and nothing here affects the protocol until one is._
