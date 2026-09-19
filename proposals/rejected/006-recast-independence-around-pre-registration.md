---
status: rejected
filed: 2026-09-02
area: protocol
issue: "#22"
released-in: ""
---

# 006 — §A step 3's independence requirement does not fit code-level probes

## What happened

§A step 3 requires that **the probe must not import the machinery it checks**.

That is written for a corpus-style probe: score a model against data it did not
produce. Two audits in one project hit cases where it is not satisfiable as
written.

- One audited a **pure function**. Measuring it means calling it. Import
  independence is impossible by construction, and the requirement pushed toward a
  probe that cannot exist.
- One audited a security gate by **mutation testing** — apply a change that removes
  a protection, run the suite, see whether anything goes red. That probe does not
  merely import the machinery, it *edits* it. Strictly further from the letter of
  the rule, and it was the sharpest instrument available: it found two protections
  a 1900-test suite could not see leave.

Both audits followed the rule's *intent* and produced findings the project acted
on. The wording is therefore not blocking — it is misleading, and it points away
from the technique that worked.

## What it cost

No round was lost outright. The cost is that the rule as written argues against the
strongest §A instrument the submitting project has used, and a project reading it
literally would decline to reach for mutation testing at all.

## How often

Twice, in two different probe shapes.

## What actually kept both probes honest

Not import independence — **pre-registration**:

- the claim quoted verbatim, from its source, before measuring;
- the falsifying observation stated as a number or condition, before measuring;
- for the mutation probe, a per-mutation prediction committed too — one of which
  was wrong, which is the point, and it was left standing in the record.

The corpus-style audit added corpus and labeller independence on top. That is one
*way* to achieve honesty for a corpus probe, not the thing itself.

## Proposed change

Re-cast §A step 3 around **pre-registration as the requirement**, with independence
(corpus, labeller, import) listed as means of achieving it, chosen to fit the
probe's shape. Concretely:

> The probe must be **pre-registered**: the claim quoted from source, and the
> observation that would falsify it, committed before any measurement. Where the
> probe *can* be independent of the machinery it checks — an independent corpus, a
> blind labeller, no import — prefer that. Where it structurally cannot (a pure
> function must be called; a mutation probe must edit the code), pre-registration
> is what carries the honesty, and the probe should say so explicitly.

## Blast radius

Wording only, in a step every audit reads. Projects whose probes already satisfy
import independence are unaffected — that path stays recommended. It widens what
counts as a valid probe rather than narrowing it, so no existing audit becomes
non-compliant.

## Why this might be wrong

Loosening a hard structural requirement into a procedural one trades a check a
reader can verify from the probe's source for a check that depends on when the
author claims to have written something down. Import independence is auditable
after the fact; pre-registration is auditable only if the record is honest. A
maintainer could reasonably hold that the current wording's occasional
unsatisfiability is a smaller cost than a requirement that cannot be checked from
the artifact.

## Also worth recording

The same round found mutation testing's limit: **it only finds protections that can
be removed — it is blind to one that was never built.** Three of that audit's
findings were absences, and no mutation could have produced any of them; an
adversarial review pass did. If step 3 is re-cast, pairing the two methods is worth
a sentence.

---

<!-- Maintainer use below this line. -->

## Disposition

**Rejected 2026-09-16 — hard disqualifier 3, with disqualifier 1 on the same text.**

Disqualifier 3 is "removes a falsifiability requirement — the before-number, the
'what would prove this wrong' step, or *the independence of an audit probe*." The
filing proposed to re-cast §A step 3 "around pre-registration as the requirement,
with independence (corpus, labeller, import) listed as means of achieving it."
Independence of the audit probe is named in the disqualifier by those words;
demoting it from requirement to means is the removal. The "where it structurally
cannot" clause is the escape hatch disqualifier 1 names in the same breath, against
a MUST.

A disqualifier ends the review; the rubric forbids weighing it against merit.

**The trade was also worse than it appeared**, which a resubmission must reckon
with: §A step 2 already requires the claim quoted verbatim and the falsifying
number stated, both before measuring. That is substantially pre-registration
already, so the filing offered to give up independence in exchange for something
the protocol largely has — which is separately criterion 3's "does not restate
something the protocol already says."

The underlying observation is legitimate and is not what was rejected: measuring a
pure function does mean calling it, and a mutation probe does edit the code. The
note that mutation testing is blind to a protection that was never built is a
genuinely useful finding this verdict does not touch.

**What would change the answer:** propose only the *addition* — what §A step 2
lacks relative to what kept those audits honest, which on this evidence is the
per-mutation prediction committed before running, including the one that came back
wrong. Leave step 3 alone; a probe that must call what it measures can still be
barred from seeing the answer. Alternatively, a clarification that a mutation probe
satisfies step 3's intent, without relaxing it, hits no disqualifier.

Full verdict, with the criterion-by-criterion record: [#22 comment](https://github.com/max-friedman/agentic-coding-loop/issues/22#issuecomment-5697440917).
