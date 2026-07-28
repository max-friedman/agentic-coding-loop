# Changelog

Projects fetching `LOOP.md` from `main` — the primary path — receive an accepted
change on their **next round**. Merging is the release. This file is the record of
what changed and why, not a gate on it; the gate is the review that preceded the
merge.

Plugin installs are the exception: they pin to the `version` in
`.claude-plugin/marketplace.json` and update on `/plugin update`.

Versioning is [semantic](https://semver.org): MAJOR for a change to the protocol
that existing state files or rounds must adapt to, MINOR for new capability, PATCH
for wording and fixes.

## [Unreleased] — docs correction, 2026-07-27

**Fixed — the docs described the opposite of the design.**

`CONTRIBUTING.md`, `README.md`, and `docs/ADOPTING.md` all presented **pinning** as
the safety property: "a merge alone changes nothing downstream." That is true only
for plugin installs. Projects that consume the protocol the primary way — fetching
`LOOP.md` from `main` at the start of each round — are not pinned and receive an
accepted change on their next round.

That is the intended behavior, not a leak. The gate belongs at **review**, not at
consumption: decide once, upstream, carefully, then let the improvement reach every
project. Describing it as gated at consumption misrepresented what the system does
and undersold why the rubric is reject-by-default.

The corollary is now stated where the guarantee used to be: a mistake merged here
executes downstream within days, with nothing in between. The version bump and
`CHANGELOG` are a record of what changed, not a brake on it.

The plugin path keeps its explicit `version` — it serves interactive use, where a
human is present and can choose when their tools change. `docs/ADOPTING.md` now says
so, and names the raw-`main` fetch as the primary path.

No protocol change, so no version bump.

## [0.7.0] — 2026-07-27

Rounds are now **reviewed** before they merge, not merely gated.

**Added**
- **§D *Reviewing the previous round*.** A round never merges itself; the next
  round's session reviews and merges it — a fresh session that did not write the
  work and cannot be attached to it. Six checks read the diff against the round's
  own claims: the finding is supported, a before-number exists, the change is one
  item, nothing was weakened, docs quoting moved numbers were updated, and the
  state file entry is honest.
- **Three outcomes, only one of which merges** — merge, request changes (comment,
  leave open, queue the fix), or close as wrong-headed with the reasoning recorded
  under *Noted, not built*.
- **§0 step 4a** — review the previous round before picking up the new item.

**Why**
- Merging was already autonomous, but its conditions were mechanical: green CI, no
  change-requests, no weakened invariant. Green CI proves the code runs, not that
  the round did what its writeup says. A PR whose finding the diff did not support,
  or that skipped the §3 before-number, would have merged.
- The asymmetry was the tell: proposals to change the *protocol* got a
  reject-by-default rubric and a real audit, while rounds changing *a project* got
  a checklist — and the checklist path is the one that runs several times a week.
- The independence needed for this already existed and was going unused: round
  N's PR is merged by round N+1's session.

**Constraint**
- The reviewing session must **not fix the PR itself.** Repairing it collapses
  reviewer and author into one agent and destroys the only independent check in the
  sequence. Comment, leave it, queue the fix as a round with its own before/after.

## [0.6.1] — 2026-07-27

**Changed**
- `templates/PROJECT_ROUTINE.md` now states that a project running the loop must
  not depend on this repository to function, and shows how to stay that way.

  The upstream watchdog had briefly been extended to check a downstream project's
  pull requests. That was backwards coupling: it would grow a hardcoded branch per
  adopting project, make every project depend on infrastructure it does not
  control, and put one repository in the position of knowing about all the others.
  The state file is project memory, not global memory, and the same applies to
  everything around it. Upstream now ships the protocol and this page — no central
  scheduler, no shared watchdog, no list of adopting projects.

- **Merging folds into the round rather than into a second Routine.** The previous
  round's PR is merged at the start of the next one. The gap between firings is
  then the veto window with no timer to configure, and the same step can notice
  when rounds are being produced faster than they are reviewed.

- **Liveness checks file issues, not notifications.** A push notification is
  ephemeral — miss it and the finding is gone, with no state and nothing to close
  when fixed. An issue persists, dedupes if it searches before filing, and closes
  when the failure clears. It must also distinguish *broken* from *legitimately
  idle*: an empty queue is a correct stop, and the response is pausing the Routine,
  not repairing it.

## [0.6.0] — 2026-07-27

This repository starts following its own rules. 0.4.0 shipped "the gate needs a
home outside your machine" while having no gate; every check had been run by hand,
in one environment, by the agent that wrote the code.

**Added**
- **`scripts/check.py`** — the gate. Stdlib only, runs identically on a laptop and
  in CI. Validates the manifest, every skill's frontmatter, that each skill inlines
  `LOOP.md` rather than restating it, that all relative links resolve, and that no
  instruction file loads `proposals/`.
- **Version-bump enforcement.** A change to `LOOP.md`, `skills/`, or `templates/`
  without a version bump now fails CI. This was a checkbox in the PR template —
  prose where a mechanism was available, which the rubric rejects.
- **`.github/workflows/checks.yml`** — runs the gate on every push and PR.
- **`LOOP.md` §4: mechanical churn gets its own commit.** Formatting sweeps and
  regenerated files go in a separate, explicitly behavior-free commit. Mixed into
  logic changes they make the diff unreviewable and poison `git blame` for every
  line they touch.
- **`LOOP.md` §5.4: search for the concept, do not recall which files mention it.**
  A round shipped a project's most decision-relevant metric, updated two docs from
  memory, and missed the canonical reference — found rounds later by audit.
- **Principles 9 and 10** — the reasoning behind the rules proposals 001 and 002
  put into `LOOP.md`. Both were merged in 0.4.0 with their mechanisms recorded and
  their justifications nowhere, which is how a rule gets rationalized away later.

**Verified**
- Every check was confirmed to *fail* on a deliberate violation before being
  trusted: a behavior change without a bump, a broken link, a skill that stopped
  inlining the protocol, and an instruction file loading `proposals/`. Two of the
  four first attempts were flawed test harnesses rather than passing checks, and
  were redone. A gate that has never failed is not yet known to be a gate.

**Note**
- Principles 9 and 10 came from downstream proposals; principle 11 as filed was
  declined, since "never publish a number you did not measure" already exists in
  principle 5 and in `LOOP.md`'s hard rules. Three copies of one rule is drift with
  a delay fuse.

## [0.5.0] — 2026-07-27

Closes the propagation gap and sets the autonomy boundary explicitly. The loop can
now run unattended end to end, with two human touchpoints kept on purpose.

**Added**
- **§0 precondition 6** — check for a newer protocol release and take it before
  starting. Previously a released change reached a project only when someone
  manually ran `/plugin update`, so the last mile of the loop was never automated.
  Non-blocking: a release you cannot reach is not a reason to skip the round.
- **Two §D unattended absolutes.** *Never weaken your own limits* — an unattended
  sequence may not edit the project rules, invariants, stop conditions, or this
  protocol to make its own work easier; propose via §C and keep running under
  current rules. *Fail loudly* — a silent no-op is indistinguishable from a healthy
  quiet day when nobody is watching.
- **`templates/PROJECT_ROUTINE.md`** — one scheduled Routine per project, with the
  paste-in prompt, cadence guidance, and what must stay human. The failure mode of a
  scheduled loop is not running too rarely; it is producing a diff every day that
  nobody reads until the whole stream is ignored.
- **A watchdog Routine** (documented in `CONTRIBUTING.md`). Checks outcomes rather
  than processes: a `proposal` issue past 12 hours with no verdict means the
  reviewer is not working. Merges loop-authored PRs after a 24-hour veto window,
  never those touching the lockout paths. Says `All healthy, nothing to do.` and
  nothing more on quiet days.
- **Reviewer self-audit** — monthly, or every tenth proposal, against five
  questions including which criterion has never rejected anything. The first audit
  is already owed.

**Deliberately not automated**
- `ESCALATE` verdicts. If the reviewer could merge changes to its own rubric,
  workflows, or CODEOWNERS, the governance would be decorative.
- `NEEDS-MAX` items — credentials, spend, decisions that are not the agent's.

These two are what keep the system bounded. Everything else is now closed.

## [0.4.0] — 2026-07-27

First release driven by downstream proposals. Both came from one project after
seven rounds; both were accepted narrower than proposed.

**Added**
- **§0 precondition 5** — confirm the gate runs somewhere other than this machine
  (proposal [001](proposals/001-gate-outside-one-machine.md), issue #2). §5 already
  promised "both green, no exceptions" and never asked where. Escape hatch is
  "record why", not "add CI", so it cannot block a project where CI cannot run.
- **Hard rule: a gate that has never failed is not yet known to be a gate.** The
  more portable half — it survives in projects with no CI at all, and makes a red
  first run legible as the system working.

**Changed**
- **The branch step moved to the top of §1** (proposal
  [002](proposals/002-branch-fires-too-late.md), issue #3). It was in §D under the
  unattended-run absolutes: scoped to unattended runs only, and firing after the
  point of no return, since shipping via PR is unfollowable once the work is on the
  default branch. Landed in §1 rather than the proposed §0 — §0 is reads and
  checks, and nothing is edited until §3, so the branch still precedes the first
  change.
- `proposal-review.yml` is **manual-only**. The primary reviewer is now a scheduled
  Claude Code Routine needing no `ANTHROPIC_API_KEY`; two reviewers would post
  competing verdicts. The workflow remains for forks with an API key and no Claude
  Code, with a comment on how to promote it back. This demotion missed the 0.3.0
  merge window and is included here.

**Note on the review record**
- Two proposals reviewed, two merged. That ratio sits badly against a
  reject-by-default rubric and is called out rather than passed over: both came
  from a project closely related to this one, submitted on a template written here.
  Worth watching whether it holds for less closely related submitters.

## [0.3.0] — 2026-07-27

Closes the loop: projects running the protocol now audit it on a cadence, and
proposals are reviewed automatically against a reject-by-default rubric.

**Added**
- `docs/REVIEW_RUBRIC.md` — eight scored criteria as a **conjunction**, not a
  weighted average, so a strong evidence section cannot buy a weak blast-radius
  argument. Eight hard disqualifiers and five escalation triggers.
- `.github/workflows/proposal-review.yml` — the reviewer. Reaches `REJECT`,
  `ESCALATE`, or `MERGE`; on merge it writes the change itself, records the
  proposal, bumps the version, and merges.
- **§C rewritten as a routine audit.** Runs every fifth round, after any stop
  condition, or when the same friction recurs twice. Includes a six-question
  examination table. Finding nothing is a valid result and is recorded as one.
- Required **Loop:** line in every round writeup — protocol friction, or
  `nothing`. Captures friction while it is concrete instead of reconstructed
  later.

**Changed**
- Proposals stay **issues**, and this is now load-bearing rather than incidental.
  A downstream-authored PR would let an unverified agent's exact wording become
  instructions every project executes — the `proposals/`-is-inert boundary
  defeated through a different door. Submitted text is evidence; the reviewer
  writes what ships.
- Filing threshold raised from "something happened" to "a pattern with a cost".

**Security**
- The reviewer cannot author or merge changes to `.github/workflows/`,
  `docs/REVIEW_RUBRIC.md`, or `.github/CODEOWNERS`. Those escalate to a human
  regardless of merit. A reviewer able to rewrite its own limits has none.
- Issue bodies are treated as untrusted input. An issue attempting to alter the
  reviewer's criteria, assert maintainer authority, or claim prior approval is
  rejected on that basis.

## [0.2.0] — 2026-07-27

Restructured for agent consumption. Humans are not the primary reader.

**Added**
- `LOOP.md` — the canonical, self-contained protocol. One fetch, no dependencies.
  Terse and imperative; tables over prose.
- **§D Continuous operation.** The loop repeats. Defines the round boundary (a
  commit), the requirement to re-read the state file each round rather than trust
  context, eight explicit stop conditions, and hard constraints for unattended runs
  (branch + PR only, never the default branch, no unapproved spend, budget of 1).
- `loop-run` skill — repeated rounds until a stop condition fires. The usual entry
  point; `loop-round` remains for exactly one.
- `templates/loop-workflow.template.yml` — GitHub Actions schedule producing one
  reviewable pull request per firing.
- `llms.txt` and `AGENTS.md` — machine-readable entry points, with read-priority
  and an explicit "do not read as instructions" marker on `proposals/`.

**Changed**
- Skills are now model-invocable with `when_to_use` triggers. Previously all were
  `disable-model-invocation: true`, which required a human to type a slash command
  — unreachable for an agent-only audience.
- Plugin root moved to the repository root (`source: "./"`, `strict: false`), so
  skills inline the canonical protocol with
  `` !`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"` ``. Skill bodies now carry only their
  own preconditions.
- Appendices renumbered to §A/§B/§C/§D. The previous `§6 Bootstrap` collided with
  round step 6.
- Version now lives in `.claude-plugin/marketplace.json`.

**Removed**
- `prompts/ROUND.md` and `docs/PROTOCOL.md`. Both were partial copies of the round
  instructions; three overlapping sources was the exact drift the loop warns about.
  `LOOP.md` replaces them.

## [0.1.0] — 2026-07-27

First release.

**Added**
- `loop` plugin with four skills: `/loop-init`, `/loop-round`, `/loop-audit`,
  `/loop-feedback`. All `/`-invocable only.
- The round protocol, the eight principles, and the state-file and project-rules
  templates.
- TactBench case study — four rounds, including the audit that measured the
  project's central claim and refuted it.
- Proposal pipeline: issue form, inert `proposals/` staging, and the review gate
  documented in `CONTRIBUTING.md`.

**Notes**
- `proposals/` is inert by design and is never read as instructions. The rationale
  is in `CONTRIBUTING.md`; it is a prompt-injection boundary, not a filing
  convention.
- The plugin carries an explicit `version` rather than tracking commits, so
  merging a change does not push it to anyone. This costs a bump per release and
  buys a second review before anything goes live.
