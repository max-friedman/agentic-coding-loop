# Changelog

Downstream projects are pinned to the `version` in
`.claude-plugin/marketplace.json`. A change reaches them when that version
is bumped and released — not when it is merged. Every release gets an entry here.

Versioning is [semantic](https://semver.org): MAJOR for a change to the protocol
that existing state files or rounds must adapt to, MINOR for new capability, PATCH
for wording and fixes.

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
