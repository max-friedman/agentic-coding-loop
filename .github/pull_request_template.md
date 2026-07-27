## What changes

<!-- The behavior change, in a sentence. -->

## Which proposal, if any

<!-- Link the proposal file and issue. A PR implementing a proposal should not
     paste its wording in unexamined — say what you kept and what you changed. -->

## Blast radius

<!-- Every project running the loop gets this. What does it cost a project that
     never had the problem? What breaks for someone relying on current behavior? -->

## If this adds instructions

<!-- The loop's instructions are read in full, every round, by every project.
     What does this replace? If nothing, why is the protocol missing a step? -->

## Release

- [ ] `version` bumped in `plugins/loop/.claude-plugin/plugin.json` — **without this, downstream projects never receive the change**
- [ ] `CHANGELOG.md` entry added
- [ ] Proposal status updated (`accepted` / `released`), if this implements one

<!-- Leave the boxes unchecked if this PR is docs-only and intentionally not a
     release. Say so here. -->
