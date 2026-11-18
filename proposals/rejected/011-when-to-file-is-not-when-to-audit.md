---
status: rejected
filed: 2026-09-07
area: protocol
issue: "#31"
released-in: ""
---

# 011 — §C says when to AUDIT but never when to FILE, so an ordinary round's finding has no home

## What happened

§C's **Cadence** governs when to *run an audit*: every fifth round, a §D stop
condition firing, or a non-`nothing` **Loop:** line twice in a row. §C's **Filing**
governs what makes something file-worthy — a pattern with a cost — and how to file it.

Nothing connects them, and no step in the *round* protocol mentions filing at all. So
Filing sits structurally **inside the audit section**, adjacent to a Cadence block,
and the practical reading a round arrives at is *"findings are filed at audits."*

## Why that reading is harmful

It is the same defect §C's own cadence rule exists to fix, one level up. A rule that
fires only at a cadence gets remembered only if someone thinks to — that is proposal
005. Here what gets deferred is the **filing**, so an ordinary round's finding waits
for an audit that may be four rounds away, and by then it is being reconstructed from
memory rather than reported from contact.

§C already argues exactly this about **Loop:** lines: state written at the time beats
state reconstructed five rounds later. The same reasoning applies to the findings
themselves.

## What it cost

The round that produced this was an ordinary round. It surfaced two upstream-worthy
findings — a further instance for proposal 004, and the §A step 6 problem now filed as
proposal 010. **The protocol gave it no step at which to file either.** They were
filed because a human was present and said to, which is not a mechanism.

Absent that, both would have been carried to the audit round. The step 6 one in
particular would have degraded: the detail that makes it land is that a specific
fixing round *could not re-run* the number defining the defect and had to ship an
inference — a contemporaneous observation about that round's actual experience, not
something that survives four rounds of recall intact.

## How often

Once, observed directly. The submitter is explicit that the cost is a near-miss
rather than a loss: nothing was actually lost, because a human intervened.

## Proposed change

Separate **when to audit** from **when to file**:

- **Filing** is triggered by *having a pattern with a cost* — at any point, in any
  round.
- **The audit cadence** exists to *find* patterns that no single round noticed.

A one-line pointer from the round protocol's record step would put the option where it
can still be acted on — which is §C's own stated criterion for a well-placed rule:
*rules must fire while the option they govern still exists.*

## Blast radius

If the fix is a cross-reference or a heading, it costs one line read every round and
changes nothing for a project that already files opportunistically. The risk in the
other direction is over-filing: a round that files whenever it feels friction produces
thin proposals, and §C's *pattern with a cost* bar exists precisely to stop that. Any
wording must carry that bar with it, or this trades a deferred filing for a noisy one.

## Why this might be wrong

The submitter raises the strongest objection themselves: this may be a
**documentation-structure** problem rather than a protocol one. Read strictly, §C's
Filing section never says *only at audits* — it says *only when there is a pattern
with a cost*. The conflation is an artifact of Filing being nested under a section
titled *Auditing the loop*, beside a Cadence block.

If that is the whole of it, the fix is a heading or a cross-reference, which is the
cheapest possible outcome. The counter-argument is that the misreading is available,
a careful reader arrived at it while following the protocol, and the structure is what
produced it.

## Related

Proposal 005 (#21) is the same shape one level down, and is what led the submitter to
notice this. If 005's fix is a marker that fires the cadence, this proposal is the
argument that the marker should not be the *only* thing that fires a filing.

---

<!-- Maintainer use below this line. -->

## Disposition

**Rejected 2026-09-18 — criterion 1 (Evidence), the cost is counterfactual;
criterion 3 (Necessity) fails independently.**

Criterion 1 fails a proposal where "the incident is hypothetical." Both findings
the round surfaced *were* filed, contemporaneously, at full detail. The filing's
own account is that they were filed "because a human happened to be present and
said to," and that absent this the §A-step-6 one "would have degraded." Would have
degraded is the hypothetical the criterion names; nothing was lost.

Criterion 3 fails on the filing's own caveat, which is correct: §C's Filing section
never says "only at audits" — it says "only file when there is a **pattern with a
cost**." The trigger is already a condition on the finding rather than on the round
type, so there is no cadence gate to remove, and proposing that filing be triggered
by having a pattern with a cost restates the sentence that already says so.

**The degradation argument does not survive §6**, which is the part worth keeping on
record. §6 already requires a **Loop:** line every round, and says why in terms the
filing itself uses: "It exists so that protocol friction is recorded while it is
still concrete, rather than reconstructed from memory five rounds later. §C turns
accumulated lines into proposals." Contemporaneous capture is already mandatory and
already every round. Carrying a finding to a later audit does not degrade it,
because the finding is not carried in memory — it is in the state file, which §D
requires the next round to re-read from disk. The filing treats the Loop line as
support for its argument; it is in fact the mechanism that makes the argument
unnecessary.

Criterion 6 passed, and identified both failures before the reviewer did.

**What would change the answer:** the degradation actually occurring — a round that
wrote a pattern-with-a-cost on its Loop line and by audit time either failed to file
it or filed it materially thinner than the line supported. Or divergent readings,
which is §C's own test for ambiguity: two rounds behaving differently on identical
text, rather than one pass arriving at one reading.

Full verdict, with the criterion-by-criterion record: [#31 comment](https://github.com/max-friedman/agentic-coding-loop/issues/31#issuecomment-5706541595).
