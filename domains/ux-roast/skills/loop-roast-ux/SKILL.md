---
name: loop-roast-ux
description: Run a UX-roast domain roast round — core §E's blind-critic/verify/verdict/queue mechanics, specialized with a coverage map keyed by user-facing surface, verification at scale for multi-complaint passes, and parallelized maker+checker fixes for disjoint findings. Use for user-facing products doing continuous UX-driven improvement that want stricter roast mechanics than core §E alone.
when_to_use: The repository contains docs/plans/LOOP_STATE.md with Layers including ux-roast, or the target project is a user-facing app/site wanting surface-based coverage and parallelized verification/fixes. Trigger phrases include "roast the UX", "run a UX round", "critique this surface". If Layers is core-only or unset, use the plain loop-roast skill instead.
argument-hint: [optional surface to roast]
---

# UX-roast round

Run **§E** of `LOOP.md` below, specialized by **DOMAIN.md**'s additive rules:
coverage-map-by-surface and CUJ framing (for picking and defining what to roast),
verification at scale (for §E step 2 when a pass surfaces several complaints at
once), and parallelized maker+checker fixes (for building the real ones).

If a surface is named here, roast that one: $ARGUMENTS

If `docs/plans/LOOP_STATE.md` does not exist, use `loop-init-ux` instead — do not
improvise a bootstrap here.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`

---

!`cat "${CLAUDE_PLUGIN_ROOT}/DOMAIN.md"`
