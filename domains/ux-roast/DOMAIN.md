# DOMAIN.md — the UX-roast domain

Additive. Everything here layers onto `LOOP.md`'s round steps and **§E Roast
round** — it never restates them and never contradicts them. Read `LOOP.md`
first; this file only makes sense as a diff against it.

**Fetch this domain when:** the target project is a user-facing product (an app,
a site) doing continuous UX-driven improvement and wants stricter roast mechanics
than core §E alone — verification at scale when a pass surfaces many findings at
once, parallelized fixes for disjoint findings, and a coverage map keyed by
user-facing surface rather than by file or module. If the project's central
claims are about an algorithm, a dataset, or a model rather than an experience a
person navigates, this domain is the wrong fit; use core `LOOP.md` alone.

**What this domain deliberately does not add:** core §E (as of protocol 0.9.0)
already does blind-critic roasting, verdict-before-fixes, dedup against the
roast log, falsifiability conversion, and ground-truth verification with a
real/critic-mistake/environment-artifact taxonomy. None of that is repeated or
reinterpreted here — this file only adds what core doesn't cover.

**Also deliberately excluded:** an unattended auto-merge tier that skips the
separate review session `LOOP.md` §D requires (*a round never merges itself*).
That MUST exists because an unreviewed unattended sequence pushing through a red
gate produces a PR nobody can read — weakening it, even as an opt-in domain
setting, is the exact "escape hatch" the review rubric's first disqualifier
names. A project that wants unattended auto-merge for narrow, mechanical changes
keeps that as its own documented, local divergence from upstream — never as
something this domain, or any domain, offers.

---

## What this domain adds

### Coverage map, keyed by surface

Organize `## Coverage map` by **user-facing surface** (a flow: "drawer search,"
"share-an-app," "voice input"), not by file or module. When §1 picks the next
item and the queue is empty of surface-specific work, prefer the
**least-recently-roasted** surface over a fresh goal-driven critique — the
coverage map's "last touched" column is exactly the signal §1 already asks for.

Before a surface is roasted the first time, frame it as a **Critical User
Journey (CUJ)**: the goal in the user's words (never a feature name), why it's
critical (what it proves if it works or breaks if it doesn't), the concrete demo
flow a critic will be told to attempt (mechanics only, never the expected
result), and the internal success bar (never shared with the critic). This is a
sharper version of §E step 1's "approach the artifact the way a user meets it" —
naming the journey before roasting it, rather than wandering the surface blind
to what matters about it.

### Verification at scale

§E step 2 requires ground-truth verification of every surviving complaint. When
a single roast pass on this kind of product surfaces several complaints at once
— common for a surface with many interactive elements — verify them with
**independent, parallel checks** rather than one serial pass: each complaint
gets its own context-aware check against the actual DB/OS/code state, and the
three-way tag (real / critic-mistake / environment-artifact) is assigned
per-complaint before any of them reach the verdict or the queue. This is a
scale-up of step 2's existing requirement, not a new rule — it exists here
because not every project running the loop has the harness capacity or the
volume of simultaneous findings to make it worth the overhead.

### Maker+checker parallel fixes

When a roast's **real** complaints (post-verification) land in disjoint files,
fix them with parallel maker agents, each in its own worktree, rather than
serializing unrelated fixes through one session — §4's "keep the repo shippable
at every commit" applies to each worktree independently. Findings touching the
same file still serialize.

Every fix, regardless of parallelization, still gets an adversarial checker
distinct from the agent that built it, who signs off before the round's normal
gate-and-branch shipping process (§4, §5, §D) proceeds — this is in addition to
the core gate, not instead of it.

### Environment hygiene before a first-run roast

Reset the target to a realistic clean state before roasting a first-run or
onboarding surface specifically. Accumulated fixtures, prior test data, and
leftover session state manufacture complaints that look identical to real
regressions until §E step 2's verification catches them — resetting first means
fewer round-trips through verification finding the same artifact repeatedly.
Keep whatever long-lived credential or config the product needs; clear anything
the product itself would consider a fresh user's history.

---

## What stays exactly as core defines it

Ending states, the audit round, the stop conditions, the round boundary, the
review-before-merge requirement, and §E's own steps 1 and 3–7 are unchanged.
This domain adds a coverage-map convention, a scale-up of an existing
verification requirement, and a parallelization pattern for fixes — it does not
add new ending states, new stop conditions, or a way to ship without review.
