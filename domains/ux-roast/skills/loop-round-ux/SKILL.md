---
name: loop-round-ux
description: Run one round of the UX-roast domain — a CUJ-framed critic round against docs/plans/LOOP_STATE.md, using the blind-critic/context-aware-verifier split, maker+checker fixes, and coverage-map-by-surface from DOMAIN.md, layered on the core loop protocol in LOOP.md. Use for user-facing products doing continuous UX-driven improvement.
when_to_use: The repository contains docs/plans/LOOP_STATE.md with Layers including ux-roast, or the target project is a user-facing app/site where improvement means UX quality. Trigger phrases include "roast the UX", "run a UX round", "critique this flow", "continue the UX loop". If Layers is core-only or unset, use the plain loop-round skill instead.
argument-hint: [optional surface to roast]
---

# UX-roast round

Run **§1–§6** of `LOOP.md` below, specialized by **DOMAIN.md**'s additive rules
for §1 (surfaces, not files), §2 (blind critic + context-aware verifier), §4
(parallel worktree maker agents for disjoint fixes), §5 (maker≠checker sign-off
+ environment reset), and §6 (coverage map by surface).

If a surface is named here, roast that one and skip the queue ordering:
$ARGUMENTS

If `docs/plans/LOOP_STATE.md` does not exist, use `loop-init-ux` instead — do not
improvise a bootstrap here.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`

---

!`cat "${CLAUDE_PLUGIN_ROOT}/DOMAIN.md"`
