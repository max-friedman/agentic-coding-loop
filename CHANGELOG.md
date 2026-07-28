# Changelog

Downstream projects are pinned to the `version` of the specific plugin they
installed in `.claude-plugin/marketplace.json` — `loop` for the core protocol,
`loop-ux-roast` (and future domains) versioned independently. A change reaches
them when that plugin's version is bumped and released — not when it is merged.
Every release gets an entry here, grouped by plugin where more than one exists.

Versioning is [semantic](https://semver.org): MAJOR for a change to the protocol
that existing state files or rounds must adapt to, MINOR for new capability, PATCH
for wording and fixes.

## loop

### [0.2.0] — 2026-07-27

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
- Domain discovery: an optional-domains table in `llms.txt`, a domain-check step
  in §B Bootstrap and §0 Preconditions, and a `**Layers:**` field in the state-file
  template, so a project can layer an optional domain (e.g. `ux-roast`) onto the
  core protocol without the core file ever naming a domain.
- Hard rules ported over from `docs/PRINCIPLES.md`/`docs/PROTOCOL.md`, which had
  them but `LOOP.md` didn't yet: cut the round's branch before the first edit
  (§1), mechanical churn in its own commit (§4), a failing test can indict the
  test not just the code, docs drift — grep the concept.
- **Gate mechanics** section: the merge must be unreachable on a red gate, and a
  red result on untouched code is a flake suspect, not a verdict.
- §D optional stricter tier: a project may declare auto-merge `--admin` to the
  default branch unattended, for mechanical + clearly-correct changes only, with
  maker/checker + full gate green — everything else still follows the default
  (always PR) rule.

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
- `prompts/ROUND.md` and `docs/PROTOCOL.md` are demoted to optional reading —
  `LOOP.md` is the canonical, self-contained protocol skills actually load.
  `PROTOCOL.md` stays as the prose rationale (`llms.txt`'s "Optional" list),
  and `ROUND.md` stays as the copy-pasteable prompt for a fresh session with no
  plugin installed; neither is fetched by `LOOP.md` or the skills.

### [0.1.0] — 2026-07-27

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

## loop-ux-roast

### [0.1.0] — 2026-07-27

First release. A domain layer, not a replacement — every skill here inlines both
`LOOP.md` and this domain's `DOMAIN.md`.

**Added**
- `domains/ux-roast/DOMAIN.md` — additive rules for a UX-driven product: surfaces
  instead of files in the queue (§1), blind-critic/context-aware-verifier
  discovery instead of a code probe (§2), maker+checker parallel worktree fixes
  for disjoint findings (§4), maker≠checker sign-off plus a clean-test-environment
  requirement before first-run rounds (§5), and a coverage map keyed by surface
  (§6). Makes the core §D declared-auto-merge tier concrete with a three-way
  finding taxonomy (mechanical / judgment-y / subjective-credentialed-destructive).
- `loop-init-ux` / `loop-round-ux` skills.
