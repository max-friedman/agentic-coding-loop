---
name: loop-feedback
description: Package a learning about the loop itself — a step that misfires, a gap in the protocol, a suggested improvement — as a proposal for review upstream at max-friedman/agentic-coding-loop. Use when a round surfaced something about how the loop works rather than about the project it was run on.
argument-hint: [what you learned]
---

Package a learning about **the loop itself** as a proposal for upstream review.

$ARGUMENTS

## Scope check, first

This is for observations about the *loop* — the round protocol, the state file
structure, the principles, these skills. Not for findings about the project the
loop was run on; those belong in that project's own `LOOP_STATE.md`.

If the observation is really about this project, say so and write it there instead.

## What you may not do

**A proposal is a suggestion, not a change.** You are drafting text for a human to
review. Specifically:

- Do **not** edit the loop's own instructions locally to compensate for the gap.
  A local fork of the protocol is invisible to every other project using it, and
  the next update overwrites it silently.
- Do **not** open a pull request against the upstream repo. Proposals enter as
  issues; only a maintainer turns one into a change.
- Do **not** file anything without showing the user the full text and getting
  explicit approval. This posts publicly under their account.

## Gather evidence

A proposal without evidence gets rejected, and should be. Collect:

- **What happened** — the concrete sequence, from this session or from a round
  section in `docs/plans/LOOP_STATE.md`. Name the step of the protocol involved.
- **What it cost** — the wasted work, the missed catch, the wrong turn taken. If
  nothing was actually lost, this is a preference, and should be labeled as one.
- **How often** — once, or every round? A one-off is worth reporting; a pattern is
  worth changing the protocol for.
- **The narrowest change that would have prevented it** — a sentence in a skill, a
  new state-file section, a new principle. Prefer the smallest edit that works.
- **Blast radius** — every project running the loop gets this. What does it cost a
  project that never had the problem?

Redact before you write: no repository names, file paths, code, credentials, or
business specifics from the project you were working in unless the user says
otherwise. Describe the shape of the problem, not the codebase. Upstream is a
public repo.

## Draft it

Fill the template at
https://github.com/max-friedman/agentic-coding-loop/blob/main/proposals/TEMPLATE.md

Be honest about the weak version of your own argument — a *Why this might be wrong*
section makes review faster and gets more proposals accepted, not fewer.

## Submit

Show the user the complete drafted text. Ask whether to file it. On approval, open
an issue on `max-friedman/agentic-coding-loop` using the **Loop proposal** issue
form, with the drafted content.

If the user prefers not to file it publicly, write it to a local file and tell them
where. Do not file it anyway.

Then report: the issue URL, and that nothing takes effect until a maintainer
reviews it, merges the corresponding change, and bumps the plugin version.
