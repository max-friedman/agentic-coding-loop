# Loop state

The spine for the continuous-improvement loop. **Read this first, write it last.**
Context is lost between rounds; this file is not.

> Copy this file to `docs/plans/LOOP_STATE.md` in your project and delete this
> blockquote. Keep every section — an empty section is information ("nothing is
> blocked"), a deleted one is a gap the next round will not notice.

---

## Current status

<!-- Rewritten every round. Should be readable in ten seconds by an agent that
     has never seen this project. -->

- **Round:** 0 — not yet started
- **Layers:** _core, or "core + &lt;domain&gt;" if §B Bootstrap matched a domain in
  `llms.txt`'s Domains table. Set once at bootstrap; do not re-derive each round._
- **Gate:** _the command that must be green before any commit, and its current
  state, e.g. "green — 60 tests, ruff clean"_
- **Artifact:** _the thing being improved, and its current size/version_
- **Headline:** _the one result that matters right now, in a sentence_

---

## Round N — <short title naming the question, not the task>

<!-- One section per round, newest at the bottom. Never edit an old round to
     make it look better; the record of a wrong turn is worth more than a tidy
     history. Delete this instructional block once round 1 lands. -->

**Question:** the thing that was actually uncertain. Not "add X" — "does X hold?"

**Method:** how it was measured, and what a negative result would have looked
like. If there was no way to come back with bad news, this was not a round.

**Finding:** what happened, stated plainly, including when it contradicts a claim
this project makes about itself.

**Shipped:** files added or changed, tests added, docs corrected.

**Consequences:** knock-on effects, verified — not predicted.

**Noted, not built:** ideas examined and deliberately rejected, with reasoning.
Without this, the next round rediscovers the same dead end and spends a session
on it.

**Loop:** friction in the protocol itself this round, or `nothing`. Required, and
`nothing` is the common answer. Recorded while it is still concrete rather than
reconstructed five rounds later; §C turns accumulated lines into proposals.

---

## Coverage map

<!-- Where the work has and hasn't gone. The "last touched" column is how a cold
     agent finds the neglected corner without reading every file. -->

| area | last touched | probe / status |
|---|---|---|
| _path/to/module_ | _R1_ | _how you know it's healthy_ |

---

## NEEDS-MAX

Items that cannot proceed without a human. **Noted and skipped — never a reason
to halt the loop.**

<!-- A credential, a spend approval, a decision that isn't the agent's to make.
     Record the exact command or action that unblocks it, so the human can
     resolve it in one minute without reconstructing context. Then move on and
     build everything that does not depend on it. -->

1. _<what is blocked>_ — _<why>_. Unblocked by:
   ```
   <the exact command>
   ```
   _<what may not be claimed until it runs>_

---

## Queue — next rounds

<!-- Ordered. Each entry is a self-contained increment that leaves the project
     shippable. Re-rank freely as findings land; a queue that never changes order
     means the rounds are not teaching you anything. -->

1. _<next increment>_ — _<why it's next>_
2. _<the one after>_

---

## Standing invariants

Encoded as tests. Do not weaken them to make a round pass — if one fails, the
code is wrong, not the assertion.

<!-- The most important section in this file. Every one of these should be
     executable, and every one should name a specific way the project could
     silently stop working while still looking fine. -->

- _<property>_ — _<the test that enforces it>_

---

## Loop configuration

**Human-set. A round never writes this section** — an agent that can enable its
own `indefinite` setting has no limit on it. See `LOOP.md` §D and §E.

| setting | value | meaning |
|---|---|---|
| `roast-on-empty` | `off` | When the queue empties, run §E (roast round) instead of stopping. |
| `indefinite` | `off` | After a roast refills the queue, keep running rounds. Requires `roast-on-empty`. |
| `roast-budget` | `1` | Consecutive roasts allowed before stopping regardless of what they find. |

<!-- Defaults are off. Leaving them off is the recommended posture: an empty queue
     is normally a correct stop, and turning it into a trigger for generated work
     is a deliberate trade, not an upgrade.

     `indefinite` lifts ONLY the empty-queue stop condition. A red gate, a
     would-be-weakened invariant, two consecutive blocked rounds, a round with no
     commit, an item attempted twice, a dirty tree, and more than two open round
     PRs all still halt the sequence. -->

