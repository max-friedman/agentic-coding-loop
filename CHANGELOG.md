# Changelog

Downstream projects are pinned to the `version` in
`.claude-plugin/marketplace.json`. A change reaches them when that version
is bumped and released — not when it is merged. Every release gets an entry here.

Versioning is [semantic](https://semver.org): MAJOR for a change to the protocol
that existing state files or rounds must adapt to, MINOR for new capability, PATCH
for wording and fixes.

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
