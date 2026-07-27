# Changelog

Downstream projects are pinned to the `version` in
`plugins/loop/.claude-plugin/plugin.json`. A change reaches them when that version
is bumped and released — not when it is merged. Every release gets an entry here.

Versioning is [semantic](https://semver.org): MAJOR for a change to the protocol
that existing state files or rounds must adapt to, MINOR for new capability, PATCH
for wording and fixes.

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
