# Loop state

The spine for the continuous-improvement loop. **Read this first, write it last.**
Context is lost between rounds; this file is not.

Protocol: [`LOOP.md`](../../LOOP.md). Project rules: [`AGENTS.md`](../../AGENTS.md).

---

## Current status

- **Round:** 3 — the gate never gated: 4 of 12 merged PRs merged red, and no red
  gate has ever blocked a merge. **Gate green on `main`.**
- **Layers:** core. The `ux-roast` domain in `llms.txt` was checked and rejected:
  this repository is a protocol library consumed by agents, not a user-facing
  product, so its roast mechanics have no surface to key a coverage map to.
- **Gate:** `python3 scripts/check.py` (and `python3 scripts/check.py --base
  origin/<base>` on pull requests, via `.github/workflows/checks.yml`).
  **GREEN — 37 checks, 0 failed.** First green state since `d2a6353` (0.8.0,
  #12). Was 32 checks / 2 failed at bootstrap: R1 added 5 checks and closed one
  failure, R2 closed the other. The merge train landed 2026-09-07, so this is now
  green **on `main`**, not only on branches. Still not *enforced*: `gate` is not a
  required status check (NEEDS-MAX 2), and R3 measured what that has cost.
- **Artifact:** two plugins declared in `.claude-plugin/marketplace.json` —
  `loop` 0.10.0 (`LOOP.md`, 610 lines; 6 skills; 5 templates) and
  `loop-ux-roast` 0.1.0 (`domains/ux-roast/`).
- **Headline:** both gate failures were in the gate, not in what it checked.
  One assertion was hollow (it failed loudly while validating nothing about the
  plugin it named); one resolved links from the directory a file was *walked*
  in rather than the directory it *lives* in. Neither was ever a defect in the
  shipped artifact — which is why four PRs could merge red without breaking
  anything, and exactly why nobody looked.

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

## Round 2 — the link checker could not tell a symlink from a file

**Question:** does `check_links()` distinguish a file from a symlink to one? It
reported `domains/ux-roast/LOOP.md -> templates/loop-workflow.template.yml` and
`-> templates/ROAST_LOG.template.md` as broken. A negative result was real and
would have reversed the fix: if the symlink is the mistake rather than the
checker, the domain needs its own copy of `LOOP.md` — which `AGENTS.md` forbids
outright ("two copies of a rule will drift, and the drift is invisible until an
agent follows the stale one").

**Method:** two measurements before changing anything.

1. Resolve the two reported targets from the root, where `LOOP.md` actually
   lives. Both exist. So the links are broken for no reader, and
   `readlink domains/ux-roast/LOOP.md` returns `../../LOOP.md`.
2. The guard that made the round falsifiable: append a genuinely broken link to
   `LOOP.md`, confirm the gate catches it *before* the fix, and require it to
   still catch it *after*. A fix that made the two false positives disappear by
   blinding the checker would pass step 1 and fail this. That outcome would have
   refuted the change.

**Finding:** the checker was resolving each file's relative links against the
directory `os.walk` handed it, not the directory the file lives in. For a
symlink those differ. `check_links()` read the root protocol's text through
`domains/ux-roast/LOOP.md` and looked for `templates/` beneath
`domains/ux-roast/`, where it has never existed.

The symlink is deliberate and load-bearing: the domain ships as its own plugin
(R1), so its skills resolve `${CLAUDE_PLUGIN_ROOT}/LOOP.md` — and
`docs/ADOPTING.md:71` states core and domain stay separately versioned by this
exact arrangement. Replacing it with a copy would have created the drift
`AGENTS.md` names. The checker was the wrong side, as in R1.

Fix: resolve against `os.path.dirname(os.path.realpath(path))`. One line, plus
the comment explaining why, since the next reader will otherwise "simplify" it
back.

**Shipped:** `scripts/check.py` (`check_links()`), `docs/plans/LOOP_STATE.md`.
No behavior path touched; no version bump.

**Consequences:** verified by re-running every probe, not predicted.

| probe | before | after |
|---|---|---|
| gate, clean tree | 37 checks, 1 failed | **37 checks, 0 failed** |
| broken link injected into `LOOP.md` (root) | caught | **caught** |
| broken link injected into `docs/ADOPTING.md` (nested, no symlink) | caught | **caught** |
| the two symlink false positives | reported | gone |
| R1's probe: corrupted `plugins[1]` | 3 of 3 caught | **3 of 3 caught** |

The last row is §5.3 — re-running an earlier round's measurement to catch a
silent regression. `claude plugin validate . --strict` still passes. The gate is
green for the first time since `d2a6353` (0.8.0, #12).

**Noted, not built:** *deduplicating the double report.* A genuinely broken link
in `LOOP.md` is now reported twice — once as `LOOP.md ->` and once as
`domains/ux-roast/LOOP.md ->`. Both statements are true: both paths do contain
that broken link. Collapsing them by `realpath` would be tidier and would also
suppress a real signal if a symlink ever pointed somewhere unexpected. Left
alone deliberately; noise in a failure message is cheaper than a checker that
hides a path.

**Loop:** the §D condition "more than two open round PRs — stop and start no new
round" is now breached: #20, #24 and this one are all open, because merging is
blocked in this environment and the human directed continuous operation. This is
recorded rather than worked around, and it is the honest cost of running rounds
faster than they can be reviewed — precisely the failure the condition names. No
further rounds should start until the train merges. Second entry in two rounds
about §D's merge step, which under §C's cadence rule ("a non-`nothing` Loop line
twice in a row") makes the *next* round owe a loop audit — noted here so it is
not lost.

**Ending state:** `shipped`.

---

## Round 3 — the gate never gated, but it was not ignored either

**Question:** did the gate ever gate? Queue item 1 asked, for every merged pull
request, whether its `gate` check was green at merge time. The negative result was
stated in advance and was specific: *this is normal for the repo, and 0.6.0's
"give this repo the gate it told everyone else to have" shipped a check nobody was
ever required to pass* — which would make the account of 0.6.0 a false claim to
correct.

**Method:** joined every workflow run of `.github/workflows/checks.yml` (27 runs,
the full history) to every merged pull request by head SHA, and read the
conclusion on the exact commit that was merged. Both sides come from the API, not
from any writeup, so no round's own account of itself is in the loop.

**Finding: the anticipated negative result did not occur, and the hypothesis
behind it is refuted.**

| era | merged PRs | green at merge | red at merge |
|---|---|---|---|
| before CI existed (#4–#7) | 4 | — | — (no gate to consult) |
| 0.6.0 → 0.8.0 (#8, #9, #10, #12) | 4 | **4** | 0 |
| 0.10.0 → #18 (#15, #16, #17, #18) | 4 | 0 | **4** |
| bootstrap + rounds (#20, #24, #25, #27) | 4 | **4** | 0 |

Twelve pull requests have merged since the gate existed. Four merged red, and all
four are **consecutive** — 0.10.0 and the three README changes after it. Every
merge from the gate's introduction through 0.8.0 was green.

So the repo was not habitually merging over a red check. The gate was green on
every merge for five merges, went red at 0.10.0, and was then merged over four
times in a row because nothing required it and nobody looked. **0.6.0's claim —
that the workflow runs on every push and pull request — is true, was true then,
and is still true.** It claims running, not blocking, and running is what it does.

The sharper answer to the question as asked: **there is no evidence the gate has
ever blocked anything.** Not once in twelve merges did a red gate stop a merge —
the four times it was red, the merge happened anyway. Green merges do not
demonstrate gating; they demonstrate agreement. `LOOP.md`'s hard rule says *a gate
that has never failed is not yet known to be a gate*. This gate has failed, four
times, and did not gate. That is the stronger version of the same finding and it
is now measured rather than asserted.

**Honesty about two rows.** #20 and #24 are recorded green at merge, and that is
what the API says, but they were red when opened. They became green only because
the stack was collapsed bottom-up before merging, so each was measured on a head
that already contained the rounds that fixed the failures. Read as *"each round's
own work was green"* the row would be false. Read as *"what was merged was green"*
— the question queue item 1 actually asked — it is true.

**Shipped:** a correction to `CONTRIBUTING.md`, found while looking for where the
0.6.0 claim lived. It stated *"this repo does not keep its own `LOOP_STATE.md`"*
— made false by Round 0 and left standing through three merges. The correction
keeps the original reasoning rather than deleting it, because the reasoning was
wrong in an instructive way: `CHANGELOG.md` and `proposals/` are both
outward-facing records of what shipped, and neither carries a queue, a coverage
map, or standing invariants. Nothing was responsible for noticing the red gate.

**Noted, not built:**

- *A probe wired into the gate.* §A wires a probe in when a claim **holds**; this
  one was refuted, and the fix is branch protection, which lives outside the
  repository and cannot be asserted by `check.py`. A check that cannot fail when
  the thing it checks breaks is worse than none.
- *Correcting the 0.6.0 entry.* Nothing to correct — the measurement says it is
  accurate.

**Swept — queue items this round answered that were not its own:**

- Queue item 1's premise cited `docs/CASE_STUDY.md` as the home of the 0.6.0
  claim. It is not there; it is in `CHANGELOG.md`, and it is true. The item was
  filed against a document it had not checked.
- Queue item 3 scopes the doc audit to `README.md` and `docs/CASE_STUDY.md`. The
  false claim this round actually found was in `CONTRIBUTING.md`, which no queue
  item covered. Item 3 re-scoped accordingly.

**Loop:** the audit owed under §C — two consecutive non-`nothing` `Loop:` lines,
both about §D's merge step — ran with this round, per §C's *"it is not its own
round."* Against §C's six questions:

1. *Disproportionate effort:* nothing found in three rounds.
2. *A rule that fires where it can no longer be acted on:* **found, second
   instance.** R0 recorded that §0's ordering means bootstrap never reaches the
   "confirm the gate runs elsewhere" precondition, and called it one data point.
   Filed proposal #26 now proposes adding a gate-integrity check to that same
   precondition — which a bootstrap would also never run. Two independent
   arrivals at one ordering defect. Recorded on #26 as an argument for §B, not
   §0, as its home.
3. *A state-file section never read:* insufficient data at three rounds.
4. *An ending state §D does not name:* R0 ended `shipped`, but a bootstrap is not
   an item landing. One instance of a forced bucket; not filed.
5. *A stop condition that fired late or failed to fire:* **found, and filed as
   #28.** §D's open-PR condition fired correctly but cannot be cleared by the
   runner that hits it — its exit is "a human merges," and §0.4a plus "a round
   never merges itself" mean merges happen only at the start of the next round.
   Cost: the stack sat four days. `indefinite` was `on` throughout and lifts only
   the empty-queue condition, so the setting enabled to keep the sequence running
   did not address the condition that stopped it.
6. *An ambiguous instruction read two ways:* none evidenced across rounds.

**Ending state:** `refuted` — the round's own hypothesis was killed by the
measurement. The doc correction shipped alongside it is incidental to the
question, not an answer to it.

---

## Coverage map

| area | last touched | probe / status |
|---|---|---|
| `LOOP.md` | 0.10.0 (`07ca784`) | Structural only: `check.py` asserts every skill inlines it. **Nothing reads its content.** |
| `skills/` (6) | 0.10.0 | Frontmatter parses, description present, inlines `LOOP.md`. Behavior unprobed. |
| `domains/ux-roast/` | R2 | Symlink confirmed deliberate and load-bearing (own plugin + `${CLAUDE_PLUGIN_ROOT}`, `docs/ADOPTING.md:71`). `DOMAIN.md` content still unprobed. |
| `templates/` (5) | 0.8.0 | **Unprobed.** No check that a template still matches what `LOOP.md` tells you to copy from it. |
| `scripts/check.py` | R2 | **Probed, both halves.** R1: corrupted `plugins[1]`, 0 of 3 caught → 3 of 3. R2: injected broken links at root and nested depth, caught before and after the symlink fix. |
| `.claude-plugin/marketplace.json` | 0.10.0 | Every declared plugin now validated for name/source/version/semver, not just `plugins[0]` (R1). |
| `.github/workflows/` | 0.6.0 | **Probed (R3).** Runs on push + PR, on all 12 merges since 0.6.0. 4 merged red; no red gate has ever blocked a merge. Off-limits to any agent acting on a proposal (`AGENTS.md`). |
| `proposals/` | 0.10.0 | Inertness enforced: no instruction file loads `proposals/`. 003 accepted. |
| `README.md`, `docs/` | #18 (`405aba9`) | **Unprobed.** Claims about the loop are unmeasured; see queue item 2. |
| `CONTRIBUTING.md` | R3 | One false claim found and corrected (it denied this repo keeps a `LOOP_STATE.md`, which R0 made false). Found by reading, not by a probe — the rest is unprobed. |

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
   gh api -X PUT repos/max-friedman/agentic-coding-loop/branches/main/protection/required_status_checks -F strict=false -f 'contexts[]=gate'
   ```
   Until then, "the gate is green" is a claim about a check nothing consults.

   **Corrected 2026-09-07.** The command recorded here would have failed: `-f`
   sends `strict` as the string `"true"`, which the API rejects as a non-boolean.
   `-F` types it. A command written into NEEDS-MAX is meant to be pasted by a
   human who will not debug it — an unrunnable one is worse than none, because it
   reads as unblocked. `strict` is now `false` by Max's decision on 2026-09-07:
   the goal is that nothing merges red, not that every branch is current, and
   `CONTRIBUTING.md` argues that friction which invites admin bypass is worse
   than the protection it buys.

3. ~~**PR #11, open since 2026-07-28, `CONFLICTING`.**~~ **Resolved 2026-09-07**
   — closed by Max's decision, with the reasoning recorded on the PR. Not
   superseded and not judged wrong: the claim it corrects is still live at
   `CONTRIBUTING.md:33`, and queue item 2 now owns settling it by measurement
   rather than by merging an assertion. The cost accepted in closing it is that
   the claim stays on `main` until that round runs.

4. ~~**`## Loop configuration` is at defaults (all off).**~~ **Resolved
   2026-09-01** — Max set `roast-on-empty` and `indefinite` to `on`. Kept here
   rather than deleted so the trail from bootstrap's default to the current
   value is visible. See `## Loop configuration`.

---

## Queue — next rounds

Ordered. Each is a question with a possible negative result, per §2.

1. **Is `CONTRIBUTING.md`'s pinning guarantee true for the primary consumer?**
   PR #11 said no. Independently re-derive it rather than trusting the PR body.
   Negative result: the guarantee holds as written and no doc change is owed.
   #11 was closed on 2026-09-07 without settling this — its argument is the
   starting hypothesis for this item, not its answer, and its diff is available
   in the closed PR if the round confirms it.
2. **§A audit candidate: which claim in `README.md`, `docs/CASE_STUDY.md` or
   `CONTRIBUTING.md` would still pass its supporting check if it became false?**
   Run when the gate is green and has been for several rounds — not before; it
   has been green on `main` for one. **Re-scoped by R3:** this item previously
   covered only `README.md` and `docs/CASE_STUDY.md`, and the false claim R3
   actually found was in `CONTRIBUTING.md`, which no item covered. The scope was
   drawn around the docs someone expected to be wrong.
3. **Does anything make a red gate cost something?** R3 measured that no red gate
   has ever blocked a merge here, and NEEDS-MAX 2 names the fix — but branch
   protection lives outside the repository and `check.py` cannot assert it.
   Question: is there any in-repo check that would fail if `gate` stopped being
   required? Negative result: there is not, the property is unassertable from
   inside, and the honest move is to say so in the standing invariants rather
   than leave the line reading as though a test is owed.

~~**Did the gate ever gate?**~~ **Answered by R3, 2026-09-07** — 4 of 12 merged
PRs merged red, all four consecutive, and no red gate has ever blocked a merge.
The item's own negative case was refuted: 0.6.0's account is accurate, and it
cited the wrong file for it. See Round 3.

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
- **Every relative link resolves**, against the directory the file really lives
  in — `check.py` → `all relative links resolve`, resolving via
  `os.path.realpath` so a symlinked file is judged at its true location (R2).
  Verified by injecting broken links at root and nested depth.
- **Every declared plugin has a name, a semver version, and a source directory
  that exists** — `check.py` → `<plugin>: has ...` / `version is semver` /
  `source exists`, run for each entry in `plugins`, not just the first (R1).
  Verified by corrupting `plugins[1]` and confirming the gate fails.
- **Not yet enforced anywhere:** that the gate is green before a merge. Named
  here because its absence is Round 0's finding, not because a test covers it.
  **Measured by R3:** 4 of 12 merged pull requests merged red, and no red gate
  has ever blocked a merge. This is not a test that is missing — it is a property
  no in-repo test can assert, because it lives in branch protection. Queue item 3
  asks whether that is final.

---

## Loop configuration

**Human-set. A round never writes this section** — an agent that can enable its
own `indefinite` setting has no limit on it. See `LOOP.md` §D and §E.

| setting | value | meaning |
|---|---|---|
| `roast-on-empty` | `on` | When the queue empties, run §E (roast round) instead of stopping. |
| `indefinite` | `on` | After a roast refills the queue, keep running rounds. Requires `roast-on-empty`. |
| `roast-budget` | `2` | Consecutive roasts allowed before stopping regardless of what they find. |

**Set by Max on 2026-09-01**, by instruction, after bootstrap had written the
table at its defaults. Round 0 records it as default-off because that is what
bootstrap did; this line is the change, not a correction of that record.
`roast-on-empty` is on because `indefinite` requires it, not because it was asked
for separately. `roast-budget` was not discussed and stays at its default.

**`roast-budget` raised 1 → 2 by Max on 2026-09-07**, by instruction. The value
had never been chosen — it was the default sitting under a setting that *was*
chosen, which is the reason it came up for decision at all. Max asked for "2–3";
2 is the conservative end of that range and is what is recorded here. Raising it
further is a one-line edit, and the reason to prefer the low end first is that
this setting has still never taken effect once.

**What this does not lift.** `indefinite` lifts exactly one stop condition — the
empty queue. Every other §D condition still halts the sequence. As of 2026-09-07
the two that were live are cleared — the gate is green on `main` (37 checks, 0
failed, first green push since `d2a6353`) and NEEDS-MAX 1 was resolved by Max's
ruling — so this configuration can now actually take effect the first time a
round empties the queue. It has not yet: the queue holds three items.

**Still not enforced:** `gate` is not a required status check on `main`
(NEEDS-MAX 2). `indefinite` keeps a sequence running; nothing yet stops a round
in that sequence from merging red.
