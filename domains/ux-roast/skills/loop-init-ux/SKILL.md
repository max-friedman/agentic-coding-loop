---
name: loop-init-ux
description: Bootstrap the UX-roast domain loop in a repository — write docs/plans/LOOP_STATE.md with Layers declared as "core + ux-roast", a surface-based coverage map, and CUJ-framed queue items, then add the loop pointer to the project rules file. Use when adopting the UX-roast domain in a user-facing product repository that has no state file yet.
when_to_use: A repository has no docs/plans/LOOP_STATE.md, the project is a user-facing app/site, and this plugin was installed deliberately for it. Trigger phrases include "set up the UX loop", "adopt the ux-roast domain here", "initialize UX-driven improvement". Refuses to run if a state file already exists.
---

# UX-roast bootstrap

Run **§B Bootstrap** of `LOOP.md` below, specialized by **DOMAIN.md**. Installing
this plugin for this project already counts as the deliberate domain match §B
step 2 asks about — set `**Layers:** core + ux-roast` directly rather than
re-deriving it from `llms.txt`.

Frame the initial queue as Critical User Journeys (DOMAIN.md's §1 spec: goal, why
critical, demo flow, success bar) rather than generic tasks, and shape the
coverage map by surface, not by file.

Then stop. Do not run a round in the same session — round 0 is the state file
itself.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`

---

!`cat "${CLAUDE_PLUGIN_ROOT}/DOMAIN.md"`
