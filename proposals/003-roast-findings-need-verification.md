---
status: released
filed: 2026-07-27
area: protocol
issue: "#14"
released-in: "0.9.0"
---

# 003 — Roast findings need independent ground-truth verification before entering the queue

## What happened

A project ran an informal predecessor of what §E now formalizes for 60+ rounds
before this repository's roast round existed: a critic with no context examines
the product's user-facing surfaces and reports complaints, each required to cite
something it actually observed (a screen, a label, an interaction it could point
to).

A recurring pattern showed up: a noticeable minority of complaints, though each
satisfied "cite something you saw," described the wrong *cause*. What looked like
two conflicting UI elements were two independently created, legitimate instances.
What looked like a data-integrity symptom was a stale-state artifact left over
from a prior test pass, not a defect. What looked like a dropped-input bug was an
artifact of the automation harness driving the product, not something a real user
would ever hit. Every one of these passed the citation bar, because the critic
genuinely did see the thing it described — it just guessed the wrong explanation
for it.

## What it cost

Several rounds were nearly spent building fixes for problems that did not exist,
before a second pass — an agent given the same complaint plus access to ground
truth the roaster didn't have — determined the complaint's real cause differed
from what the roaster assumed. In the cases caught before a fix round started, no
work was wasted; in closer calls, a wrong root cause was briefly assumed before
the second pass corrected it.

## Disposition — MERGE, with a guardrail the submitter flagged against their own proposal

Accepted essentially as filed, with one refinement to placement and one addition
the submitter's own "why this might be wrong" section asked for.

**Shipped:**

- **§E step 2 — Verify against ground truth.** Placed *before* the verdict (§E
  step 3), not after it as originally filed. The submitter's proposal put
  verification between "roast blind" and "write the verdict" without addressing
  whether the verdict itself should be shaped by a complaint later found to be an
  environment-artifact. It should not be — a verdict is meant to represent what a
  real user would conclude, and a real user could never hit a test-harness
  artifact. Verifying first, then writing the verdict from real complaints only,
  keeps the verdict honest in the sense §E already cares about.
- **A three-way tag** — real, critic-mistake, environment-artifact — rather than
  a binary real/not-real. A critic-mistake keeps the observation and corrects the
  cause; an environment-artifact drops the complaint entirely, since no user could
  reach it. Collapsing these loses the difference between "wrong about why" and
  "not a real thing."
- **The anti-laundering guardrail**, taken directly from the submitter's own
  strongest objection to their proposal: ground truth may only correct or drop a
  complaint that turns out to be unreal. It may never be used to explain away a
  complaint a real user would still experience just because the internal cause
  differs from what the critic guessed. Without this line, the step is a truth
  check in name and an excuse-generator in practice.
- **`templates/ROAST_LOG.template.md`** — the complaint table gained a `verified`
  column, and its example rows now show a critic-mistake and an
  environment-artifact disposition alongside the existing real/queued examples.
- **`docs/PRINCIPLES.md` §11** and **`skills/loop-roast/SKILL.md`**, both carrying
  the same guardrail so it survives outside LOOP.md too.

### Why this cleared the bar

The evidence is a repeated pattern across many rounds of one project's real
history, not a hypothetical — and it names a failure mode §E's existing citation
rule cannot catch by construction: citing a real observation is not the same as
attributing it correctly. The fix is a mechanism (a required check with a named
three-way output), not prose asking roasters to be more careful.

### The objection that could have sunk it, and didn't

The submitter's own strongest argument against their proposal: a verification
step with access to internal state risks re-contaminating a roast's deliberate
blindness, and could be used to dismiss real user-facing problems by pointing at
an internal cause. That is a real risk, not a straw man — and it is why this
disposition ships the guardrail as a hard line in the mechanism itself (§E step 2,
`docs/PRINCIPLES.md` §11, and the skill), rather than trusting an agent to
self-apply the restraint. The objection improved the proposal; it did not defeat
it.

### Blast radius

One additional step in every roast, and one additional table column in the roast
log. For a project whose roaster already has ground-truth access while roasting
(reading the same state/logs it critiques), the step is close to a no-op — a
short re-confirmation of something already known. For a project that deliberately
keeps its roaster blind to internals, this is the step that catches the exact
failure this proposal evidences.
