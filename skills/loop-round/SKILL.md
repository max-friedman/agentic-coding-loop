---
name: loop-round
description: Run one round of the continuous-improvement loop against docs/plans/LOOP_STATE.md — pick one queue item, state what would falsify it, measure before changing, ship, then rewrite the state file. Use when continuing long-running improvement work on a repository, or when asked to run a round or continue the loop.
when_to_use: The repository contains docs/plans/LOOP_STATE.md and there is improvement work to continue. Trigger phrases include "run a round", "continue the loop", "pick up the improvement work", "what is next in the queue". If no state file exists, use loop-init instead.
argument-hint: [optional item to work on]
---

# Round

Run **§1–§6** of the protocol below. One round, one item.

If an item is named here, do that one and skip the queue ordering: $ARGUMENTS

If `docs/plans/LOOP_STATE.md` does not exist, do not improvise — use the
`loop-init` skill instead.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`
