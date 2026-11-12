---
name: loop-lanes
description: Coordinate several agents running loop rounds in parallel on one repository — start lanes within the cap and one per hotspot, review and merge their PRs through one merge path, batch merges, and handle a red default branch without freezing the queue. Use when `lanes` in Loop configuration is above 1.
when_to_use: The state file's Loop configuration sets lanes above 1 and the work is to run several rounds at once, as their coordinator. Trigger phrases include "run lanes", "coordinate the helpers", "run rounds in parallel", "start the lanes". With lanes at 1, use loop-run instead.
argument-hint: [optional number of lanes to start now, never above the configured cap]
---

# Coordinate parallel lanes

You are the **coordinator** in §F of the protocol below. You do not write lane work
yourself; you start lanes, review their PRs, merge them, and keep the state file's
shared sections.

Lanes to start now: $ARGUMENTS — never more than `lanes` in `## Loop configuration`,
and never by raising that setting yourself.

## Each cycle

1. Re-read `docs/plans/LOOP_STATE.md` from disk, including `## Lanes`.
2. Review and merge what waits (§D *Reviewing the previous round*, through the one
   merge path, batched where §F allows).
3. Check the floors: memory, disk, the merge queue. Above the queue threshold, point
   free lanes at what unblocks merging instead of new items.
4. Fill free lanes from the top of the queue, skipping items whose files fall in a
   held hotspot. Every lane prompt names its item, its hotspot, and the project rules
   file; it says the lane never merges and never edits the shared state sections.
5. Update `## Lanes`, append merged rounds, and record any call you made for the
   human under `## Decided, not asked`.
6. Evaluate §D and §F stop conditions.

## Report

Lead with what waits on the human and what each item unblocks. Then one line per
lane: item, state. Nothing on routine events.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`
