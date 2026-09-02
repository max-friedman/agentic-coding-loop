# Loop state

The spine for the continuous-improvement loop. **Read this first, write it last.**
Context is lost between rounds; this file is not.

Protocol: [`LOOP.md`](../../LOOP.md). Project rules: [`AGENTS.md`](../../AGENTS.md).

---

## Current status

- **Round:** 0 — bootstrapped. No round has run yet.
- **Layers:** core. The `ux-roast` domain in `llms.txt` was checked and rejected:
  this repository is a protocol library consumed by agents, not a user-facing
  product, so its roast mechanics have no surface to key a coverage map to.
- **Gate:** `python3 scripts/check.py` (and `python3 scripts/check.py --base
  origin/<base>` on pull requests, via `.github/workflows/checks.yml`).
  **RED.** 32 checks, 2 failed, on `main` at `405aba9`.
- **Artifact:** two plugins declared in `.claude-plugin/marketplace.json` —
  `loop` 0.10.0 (`LOOP.md`, 610 lines; 6 skills; 5 templates) and
  `loop-ux-roast` 0.1.0 (`domains/ux-roast/`).
- **Headline:** the repository that tells every adopter *"a gate that has never
  failed is not yet known to be a gate"* has been merging over its own failing
  gate since 0.10.0. Four consecutive pull requests — #15, #16, #17, #18 — were
  merged with the `gate` check red, and `main` has been red ever since.

---

## Round 0 — bootstrap: the gate has been red through four merges

**Question:** does this repository run the loop it publishes? It has no
`docs/plans/LOOP_STATE.md`, so `LOOP.md` §0.3 answers with §B Bootstrap rather
than a round. The uncertainty bootstrap had to resolve honestly was §B step 3's
"the exact gate command, and its current state."

**Method:** ran the gate before writing anything — `python3 scripts/check.py` —
and then checked whether CI agreed, rather than assuming the local result was
local. `gh run list --branch main` for the pushed state, `gh pr checks <n>` for
each recent pull request. A negative result here looked like: the gate is green
and bootstrap is uneventful paperwork.

**Finding:** the gate is red, and has been through four merges.

Local, on `main` at `405aba9`:

```
32 checks, 2 failed (version 0.10.0)

failed:
  - exactly one plugin
  - all relative links resolve
```

CI agrees, on every push to `main` since 0.10.0:

| push | run | conclusion |
|---|---|---|
| `07ca784` 0.10.0 (#15) | 30336023240 | failure |
| `bc4b0a0` (#16) | 30338467524 | failure |
| `4d7e2ef` (#17) | 30340313403 | failure |
| `405aba9` (#18) | 30397905519 | failure |

Last green push: `d2a6353` 0.8.0 (#12), run 30329251643. The `gate` check was
also **failing on each pull request before it was merged** (#15 run
30335999654, #16 run 30337282220, #17 run 30339142833, #18 run 30397875237), so
this was not four people missing a post-merge signal — it was four merges over a
red required-looking check that is not actually required.

The two failures, diagnosed but **deliberately not fixed in this bootstrap**:

1. `exactly one plugin` — `check.py` asserts `len(plugins) == 1`. 0.10.0
   deliberately added a second plugin, `loop-ux-roast`. Either the assertion is
   stale or the manifest is wrong. `LOOP.md`'s hard rule — *"a failing invariant
   means the code is wrong, not the assertion... if an invariant is genuinely
   mis-stated, say so in the writeup and leave it failing"* — forbids this
   session picking. It is queued and in NEEDS-MAX, still failing.

   One measurement, run and recorded but not acted on: `claude plugin validate .
   --strict` — the command `AGENTS.md` names as the pre-commit check — **passes**
   on the two-plugin manifest. The official validator and this repository's own
   gate disagree about the same file. That is evidence for the queue item, not a
   licence for this session to settle it.

2. `all relative links resolve` — `domains/ux-roast/LOOP.md` is a **symlink**
   (git mode `120000`) to `../../LOOP.md`. `check_links()` walks it with
   `os.walk`, reads the root protocol's text, and resolves its relative links
   from `domains/ux-roast/`, where `templates/` does not exist. Two links break
   (`templates/loop-workflow.template.yml`, `templates/ROAST_LOG.template.md`)
   and neither is broken for any reader. The content is fine; the checker
   double-counts a symlinked file. Also queued, also left failing.

**Shipped:** `docs/plans/LOOP_STATE.md` (this file); the §B step 5 pointer at the
top of `AGENTS.md`. No behavior path (`LOOP.md`, `skills/`, `templates/`) is
touched, so no version bump is required and none was made.

**Consequences:** verified, not predicted — creating `docs/plans/LOOP_STATE.md`
does not change the gate result. `check.py`'s `EXPECTED_DANGLING` already lists
that path, so the link checker skipped it before and skips it now. Gate output is
identical before and after this change: 32 checks, the same 2 failures.

**Noted, not built:**

- *Fixing the two gate failures here.* Both fixes are small and both are
  assertion-side. Landing them inside bootstrap would destroy the before-number
  and collapse author and reviewer into one session — and one of them is exactly
  the "assertion nudge" anti-pattern the protocol names. They are rounds, with
  their own before and after.
- *Enabling `roast-on-empty` / `indefinite`.* §D: *"`indefinite` is the setting
  most worth enabling and the one a round must never enable for itself."* The
  section is written with defaults off and is listed in NEEDS-MAX with the exact
  edit for a human.
- *Touching PR #11.* It conflicts and is five weeks stale, but §D's review step
  governs the *previous round's* PR, and there is no previous round. Merging or
  closing it is a human call; it is in NEEDS-MAX with both commands.

**Loop:** §0 orders its preconditions 1–6, so "run §B Bootstrap instead of a
round, then stop" (step 3) fires *before* "confirm the gate runs somewhere other
than this machine" (step 5). Bootstrap therefore has no instruction to check the
gate's state — §B step 3 asks for "the exact gate command" and its current state
as something to *record*, not something that can stop the sequence. Here that was
harmless because recording it was the finding. It would not be harmless if a
bootstrap wrote "Gate: green" from a command it never ran. One data point; not a
pattern; not yet a §C proposal.

**Ending state:** `shipped` — bootstrap completed, gate state recorded honestly
as red, queue seeded from the failures rather than invented.

---

## Coverage map

| area | last touched | probe / status |
|---|---|---|
| `LOOP.md` | 0.10.0 (`07ca784`) | Structural only: `check.py` asserts every skill inlines it. **Nothing reads its content.** |
| `skills/` (6) | 0.10.0 | Frontmatter parses, description present, inlines `LOOP.md`. Behavior unprobed. |
| `domains/ux-roast/` | 0.10.0 | **Unprobed.** Its `LOOP.md` symlink is one of the two current gate failures. |
| `templates/` (5) | 0.8.0 | **Unprobed.** No check that a template still matches what `LOOP.md` tells you to copy from it. |
| `scripts/check.py` | 0.6.0 | The gate itself. **Unprobed — nothing checks the checker**, and it is currently wrong about at least one of its two failures. |
| `.github/workflows/` | 0.6.0 | Runs on push + PR. Off-limits to any agent acting on a proposal (`AGENTS.md`). |
| `proposals/` | 0.10.0 | Inertness enforced: no instruction file loads `proposals/`. 003 accepted. |
| `README.md`, `docs/` | #18 (`405aba9`) | **Unprobed.** Claims about the loop are unmeasured; see queue item 5. |

---

## NEEDS-MAX

Items that cannot proceed without a human. **Noted and skipped — never a reason
to halt the loop.**

1. **`exactly one plugin` — stale assertion, or wrong manifest?** 0.10.0 added
   `loop-ux-roast` on purpose; `check.py` still asserts one plugin. A round may
   not relax an assertion to go green, so this needs a ruling on which side is
   wrong. Note that the two disagree: `claude plugin validate . --strict`
   passes on this manifest while the gate fails on it. Reproduce both with:
   ```
   python3 scripts/check.py; claude plugin validate . --strict
   ```
   Until it is ruled on, no round may claim a green gate.

2. **The gate is not enforced.** #15–#18 each merged with `gate` failing.
   Unblocked by making `gate` a required status check on `main`:
   ```
   gh api -X PUT repos/max-friedman/agentic-coding-loop/branches/main/protection/required_status_checks -f 'strict=true' -f 'contexts[]=gate'
   ```
   Until then, "the gate is green" is a claim about a check nothing consults.

3. **PR #11, open since 2026-07-28, `CONFLICTING`.** It is not superseded — the
   claim it corrects is still live on `main` at `CONTRIBUTING.md:33`
   ("Consumers are pinned to the..."). Rebase and merge, or close and let queue
   item 4 redo it:
   ```
   gh pr view 11
   gh pr close 11
   ```

4. ~~**`## Loop configuration` is at defaults (all off).**~~ **Resolved
   2026-09-01** — Max set `roast-on-empty` and `indefinite` to `on`. Kept here
   rather than deleted so the trail from bootstrap's default to the current
   value is visible. See `## Loop configuration`.

---

## Queue — next rounds

Ordered. Each is a question with a possible negative result, per §2.

1. **Is `exactly one plugin` an invariant or a leftover?** It was written when
   there was one plugin; 0.10.0 shipped two deliberately. Negative result: the
   assertion is right and the second plugin should never have been declared in
   this manifest — in which case the fix is in the manifest, not the check.
   Evidence so far points the other way: `claude plugin validate . --strict`
   passes. Blocked on NEEDS-MAX 1.
2. **Does `check_links()` know the difference between a file and a symlink to
   one?** It resolves the root `LOOP.md`'s relative links from
   `domains/ux-roast/`. Negative result: the symlink is the mistake, not the
   checker, and the domain should carry its own copy — which `AGENTS.md` forbids
   ("two copies of a rule will drift").
3. **Did the gate ever gate?** Four pull requests merged red. Measure: for every
   merged PR, was its `gate` check green at merge time? Negative result: this is
   normal for the repo and 0.6.0's "give this repo the gate it told everyone else
   to have" shipped a check nobody was ever required to pass — which would make
   `docs/CASE_STUDY.md`'s account of 0.6.0 a false claim to correct.
4. **Is `CONTRIBUTING.md`'s pinning guarantee true for the primary consumer?**
   PR #11 says no. Independently re-derive it rather than trusting the PR body.
   Negative result: the guarantee holds and #11 should be closed.
5. **§A audit candidate: which claim in `README.md` / `docs/CASE_STUDY.md` would
   still pass its supporting check if it became false?** Run when the gate is
   green and has been for several rounds — not before.

---

## Standing invariants

Encoded as tests. Do not weaken them to make a round pass — if one fails, the
code is wrong, not the assertion.

- **The protocol has exactly one copy.** Every skill inlines `LOOP.md` rather
  than restating it — `check.py` → `<skill>: inlines LOOP.md`.
- **`LOOP.md` sits at the plugin root**, or every skill silently ships empty —
  `check.py` → `LOOP.md at plugin root`.
- **No instruction file loads `proposals/`.** Untrusted submitted text never
  becomes text an agent executes — `check.py` → `no instruction file loads
  proposals/`.
- **A behavior change carries a version bump.** Without it the change reaches no
  downstream project — `check.py --base origin/<base>` → `version bumped for
  behavior change`.
- **Every relative link resolves.** `check.py` → `all relative links resolve`.
  **Currently failing.** See Round 0; left failing deliberately.
- **The manifest declares a valid semver plugin whose source exists.**
  `check.py` → the `manifest` block. **`exactly one plugin` currently failing.**
- **Not yet enforced anywhere:** that the gate is green before a merge. Named
  here because its absence is Round 0's finding, not because a test covers it.

---

## Loop configuration

**Human-set. A round never writes this section** — an agent that can enable its
own `indefinite` setting has no limit on it. See `LOOP.md` §D and §E.

| setting | value | meaning |
|---|---|---|
| `roast-on-empty` | `on` | When the queue empties, run §E (roast round) instead of stopping. |
| `indefinite` | `on` | After a roast refills the queue, keep running rounds. Requires `roast-on-empty`. |
| `roast-budget` | `1` | Consecutive roasts allowed before stopping regardless of what they find. |

**Set by Max on 2026-09-01**, by instruction, after bootstrap had written the
table at its defaults. Round 0 records it as default-off because that is what
bootstrap did; this line is the change, not a correction of that record.
`roast-on-empty` is on because `indefinite` requires it, not because it was asked
for separately. `roast-budget` was not discussed and stays at its default.

**What this does not lift.** `indefinite` lifts exactly one stop condition — the
empty queue. Every other §D condition still halts the sequence, and two of them
are live right now: the gate is red, and the ruling that would let a round fix it
is NEEDS-MAX 1. Enabling this did not start anything. It takes effect the first
time a round empties the queue, which cannot happen until the gate is green.
