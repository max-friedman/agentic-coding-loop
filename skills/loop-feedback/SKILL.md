---
name: loop-feedback
description: Audit the improvement loop protocol itself and file a proposal upstream when a pattern with a real cost has accumulated — a step that misfires, a gap the protocol does not cover, a rule placed where it cannot be followed. Use during a loop audit, or when a round surfaced friction with how the loop works rather than with the project it ran on.
when_to_use: A loop audit is due (every fifth round, after a stop condition, or when the same friction appeared twice running), or an observation concerns the protocol, the LOOP_STATE.md structure, or these skills. Trigger phrases include "audit the loop", "this step of the loop is wrong", "the protocol should", "send this upstream". Findings about the project being worked on belong in its own LOOP_STATE.md instead.
argument-hint: [what you learned]
---

# Loop audit and proposal

Run **§C** of the protocol below.

The observation, if given: $ARGUMENTS

## Scope gate

This concerns the *loop*. If the observation is really about the project the loop
ran on, write it into that project's `docs/plans/LOOP_STATE.md` and say so.

## Audit before filing

Read the **Loop:** lines from every round since the last audit and work through the
§C examination table. Most audits find nothing — record that as a result rather
than manufacturing a proposal to justify the exercise.

File only for a **pattern with a cost**. A single awkward round is not a proposal.

## Expect rejection

The reviewer's posture is reject-by-default and the rubric is a conjunction: one
failed criterion rejects, so a strong evidence section cannot offset a weak one.
Read [`docs/REVIEW_RUBRIC.md`](https://github.com/max-friedman/agentic-coding-loop/blob/main/docs/REVIEW_RUBRIC.md)
before writing. The three most common failures:

- **No evidence.** No round it actually cost something in — a preference in
  evidence's clothing.
- **Growth without deletion.** Adding without saying what it replaces.
- **Prose where a mechanism was available.** If it could be a stop condition, a
  test, or a step reordering, proposing a paragraph fails.

## Filing

1. Search existing issues. Add evidence to an existing proposal rather than
   opening a second — two thin proposals lose where one well-evidenced one wins.
2. Redact repository names, paths, code, credentials, and business specifics. The
   upstream repository is public.
3. Open an issue on `max-friedman/agentic-coding-loop` with the **Loop proposal**
   form, filling every required field.
4. If a human is present, show the full text and get approval first — this posts
   publicly under their account. If running unattended, file it and report the URL.

## Do not

- Edit the loop's instructions locally to compensate. A local fork is invisible to
  every other project running the loop and is overwritten on the next update.
- Open a pull request. Proposals are issues. The reviewer writes the change itself
  in the protocol's voice — your text is evidence, not copy.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`
