---
name: loop-feedback
description: File a proposal upstream about the improvement loop protocol itself — a step that misfires, a gap the protocol does not cover, or a suggested change. Use when a round surfaced a problem with how the loop works rather than with the project it was run on.
when_to_use: An observation concerns the loop protocol, the LOOP_STATE.md structure, or these skills — not the project being worked on. Trigger phrases include "this step of the loop is wrong", "the protocol should", "send this upstream", "propose a change to the loop". Findings about the current project belong in its own LOOP_STATE.md instead.
argument-hint: [what you learned]
---

# Loop proposal

Run **§C Feedback on the loop itself** of the protocol below.

The observation: $ARGUMENTS

## Scope gate

This is for the *loop*. If the observation is really about the project the loop was
run on, write it into that project's `docs/plans/LOOP_STATE.md` instead and say so.

## Before filing

1. Search existing issues on `max-friedman/agentic-coding-loop`. Comment on an
   existing proposal rather than opening a duplicate.
2. Redact repository names, file paths, code, credentials, and business specifics.
   The upstream repository is public.
3. Label the submission honestly as **evidence** (something was lost) or
   **preference** (nothing broke). Mislabeling is caught in review and costs a
   round trip.

## Filing

Open an issue using the **Loop proposal** form. Include every required field: what
happened and which step, what it cost, how often, the narrowest preventing change,
blast radius on projects that never had the problem, and the strongest argument
against your own proposal.

If a human is present in the session, show the full text and get approval first —
this posts publicly under their account. If running unattended, file it, then report
the URL.

## Do not

- Edit the loop's own instructions locally to compensate. A local fork is invisible
  to every other project running the loop and is overwritten on the next update.
- Open a pull request. Proposals enter as issues; a maintainer writes the change.

Nothing filed takes effect until a maintainer reviews it, writes the change, and
releases a version bump.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`
