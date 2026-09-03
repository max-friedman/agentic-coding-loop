# Loop state

The spine for the continuous-improvement loop. **Read this first, write it last.**
Context is lost between rounds; this file is not.

Protocol: [`LOOP.md`](../../LOOP.md). Project rules: [`AGENTS.md`](../../AGENTS.md).

---

## Current status

- **Round:** 1 — `exactly one plugin` replaced with per-plugin validation.
- **Layers:** core. The `ux-roast` domain in `llms.txt` was checked and rejected:
  this repository is a protocol library consumed by agents, not a user-facing
  product, so its roast mechanics have no surface to key a coverage map to.
- **Gate:** `python3 scripts/check.py` (and `python3 scripts/check.py --base
  origin/<base>` on pull requests, via `.github/workflows/checks.yml`).
  **RED, improving.** 37 checks, 1 failed. Was 32 checks / 2 failed at
  bootstrap; Round 1 closed one failure and added 5 checks. The remaining
  failure is `all relative links resolve`, queue item 1.
- **Artifact:** two plugins declared in `.claude-plugin/marketplace.json` —
  `loop` 0.10.0 (`LOOP.md`, 610 lines; 6 skills; 5 templates) and
  `loop-ux-roast` 0.1.0 (`domains/ux-roast/`).
- **Headline:** the gate's `exactly one plugin` assertion was not stale, it was
  hollow — it failed loudly on a deliberate second plugin while validating
  nothing about it. A plugin with no name, a nonexistent source and a garbage
  version passed every per-plugin check. Round 1 replaced it; the gate went from
  32 checks to 37 and from 2 failures to 1.

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

## Round 1 — `exactly one plugin`: not a stale assertion, a hollow one

**Question:** is `exactly one plugin` a real invariant that 0.10.0 violated, or a
leftover from when this marketplace declared one plugin? Bootstrap left it
failing rather than picking, per the hard rule that a session does not relax the
assertion it tripped over. Max ruled it stale on 2026-09-03 (NEEDS-MAX 1).

**Method:** the ruling settled *which side is wrong*, not *whether the check was
carrying its weight*, so the round measured the second thing before touching
anything. Probe: corrupt `plugins[1]` in the manifest — delete its `name`, point
`source` at a directory that does not exist, set `version` to `not-a-version` —
and run the unmodified gate. A negative result was available and specific: if the
gate caught any of the three, the old assertion was doing real work and the fix
would have to preserve it.

**Finding:** the gate caught **none of the three**. On a manifest whose second
plugin was nameless, sourceless and unversioned, output was identical to the
clean manifest — the same 2 failures, and every per-plugin check green:

```
  FAIL  exactly one plugin — found 2
  ok    plugin has 'name'
  ok    plugin has 'source'
  ok    plugin has 'version'
  ok    version is semver
  ok    plugin source exists
```

`check_manifest()` bound `plugin = plugins[0]` and validated that one object.
`exactly one plugin` was not guarding the invariant it appeared to guard; it was
standing in for validation it never performed, and its failure since 0.10.0 was
the only reason anyone would look at the block at all. The evidence bootstrap
already had — `claude plugin validate . --strict` passing, `docs/ADOPTING.md`
documenting `/plugin install loop-ux-roast@agentic-coding-loop` in three places,
both domain skills reading `${CLAUDE_PLUGIN_ROOT}/DOMAIN.md` (which resolves to
`domains/ux-roast/` only if that directory is its own plugin) — says the manifest
encodes the design and the check was the wrong side. The probe says the check was
also worth less than its failure suggested.

**Shipped:** `scripts/check.py` — `check_manifest()` now asserts `at least one
plugin` and loops over every declared plugin, labelling each check with the
plugin's name. `docs/plans/LOOP_STATE.md`. No behavior path (`LOOP.md`,
`skills/`, `templates/`) touched, so no version bump; `--base` correctly skips
the release check. `scripts/check.py` is not among the files `AGENTS.md` puts
off-limits (`.github/workflows/`, `docs/REVIEW_RUBRIC.md`, `.github/CODEOWNERS`).

**Consequences:** verified by re-running the identical probe against the fixed
gate, not predicted.

| | checks | failures, clean manifest | defects caught in corrupted `plugins[1]` |
|---|---|---|---|
| before | 32 | 2 | **0 of 3** |
| after | 37 | 1 | **3 of 3** |

The change is strictly a strengthening: five checks added, none removed, and
three real defect classes that were previously invisible now fail the gate. That
distinction is what separates this from the assertion-nudge anti-pattern —
`len(plugins) == 1` → `len(plugins) <= 2` would have gone green while leaving all
three invisible. `claude plugin validate . --strict` still passes.

**Noted, not built:** *checking that `loop-ux-roast`'s version tracks `loop`'s.*
They are versioned independently on purpose (`docs/ADOPTING.md:71`), so an
equality check would encode the opposite of the design. There may be a real
invariant nearby — a domain declaring a `loop` version it cannot work with — but
nothing in the repo currently expresses that dependency, so there is nothing to
check against and inventing one would be a rule cited later as load-bearing.

**Loop:** the hard rule "if an invariant is genuinely mis-stated, say so in the
writeup and leave it failing" got this exactly right, and would have been worth
following even under pressure to go green: leaving it failing is what made the
before-probe possible. Had bootstrap quietly fixed it, the discovery that the
check validated nothing would have been lost with it. Second bootstrap-adjacent
note: §D's "a round never merges itself" could not be honoured this round — the
merge of the previous round's PR (#20) was blocked in this environment, so the
rounds are stacked as branches for a human to merge in order. Recorded, not
worked around.

**Ending state:** `shipped`.

---

## Coverage map

| area | last touched | probe / status |
|---|---|---|
| `LOOP.md` | 0.10.0 (`07ca784`) | Structural only: `check.py` asserts every skill inlines it. **Nothing reads its content.** |
| `skills/` (6) | 0.10.0 | Frontmatter parses, description present, inlines `LOOP.md`. Behavior unprobed. |
| `domains/ux-roast/` | 0.10.0 | **Unprobed.** Its `LOOP.md` symlink is one of the two current gate failures. |
| `templates/` (5) | 0.8.0 | **Unprobed.** No check that a template still matches what `LOOP.md` tells you to copy from it. |
| `scripts/check.py` | R1 | **Probed.** R1 corrupted `plugins[1]` and confirmed the manifest block caught 0 of 3 defects; after the fix, 3 of 3. `check_links()` is still unprobed — queue item 1. |
| `.claude-plugin/marketplace.json` | 0.10.0 | Every declared plugin now validated for name/source/version/semver, not just `plugins[0]` (R1). |
| `.github/workflows/` | 0.6.0 | Runs on push + PR. Off-limits to any agent acting on a proposal (`AGENTS.md`). |
| `proposals/` | 0.10.0 | Inertness enforced: no instruction file loads `proposals/`. 003 accepted. |
| `README.md`, `docs/` | #18 (`405aba9`) | **Unprobed.** Claims about the loop are unmeasured; see queue item 5. |

---

## NEEDS-MAX

Items that cannot proceed without a human. **Noted and skipped — never a reason
to halt the loop.**

1. ~~**`exactly one plugin` — stale assertion, or wrong manifest?**~~
   **Resolved 2026-09-03** — Max ruled the assertion stale. R1 acted on it and
   found the check was additionally hollow: it validated nothing about the
   plugin it was failing over. See Round 1.

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

1. **Does `check_links()` know the difference between a file and a symlink to
   one?** It resolves the root `LOOP.md`'s relative links from
   `domains/ux-roast/`. Negative result: the symlink is the mistake, not the
   checker, and the domain should carry its own copy — which `AGENTS.md` forbids
   ("two copies of a rule will drift").
2. **Did the gate ever gate?** Four pull requests merged red. Measure: for every
   merged PR, was its `gate` check green at merge time? Negative result: this is
   normal for the repo and 0.6.0's "give this repo the gate it told everyone else
   to have" shipped a check nobody was ever required to pass — which would make
   `docs/CASE_STUDY.md`'s account of 0.6.0 a false claim to correct.
3. **Is `CONTRIBUTING.md`'s pinning guarantee true for the primary consumer?**
   PR #11 says no. Independently re-derive it rather than trusting the PR body.
   Negative result: the guarantee holds and #11 should be closed.
4. **§A audit candidate: which claim in `README.md` / `docs/CASE_STUDY.md` would
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
- **Every declared plugin has a name, a semver version, and a source directory
  that exists** — `check.py` → `<plugin>: has ...` / `version is semver` /
  `source exists`, run for each entry in `plugins`, not just the first (R1).
  Verified by corrupting `plugins[1]` and confirming the gate fails.
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
