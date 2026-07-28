---
name: loop-init
description: Bootstrap the continuous-improvement loop in a repository — read the project, write docs/plans/LOOP_STATE.md with a real gate command, coverage map, queue and invariants, and add the loop pointer to the project rules file. Use when adopting the loop in a repository that has no state file yet.
when_to_use: A repository has no docs/plans/LOOP_STATE.md and the loop is being adopted. Trigger phrases include "set up the loop", "adopt the loop here", "initialize the improvement loop", "start the loop on this repo". Refuses to run if a state file already exists.
---

# Bootstrap

Run **§B Bootstrap** of the protocol below, then stop. Do not run a round in the
same session — round 0 is the state file itself.

Hard precondition: if `docs/plans/LOOP_STATE.md` already exists, STOP and report
its current status. It is the project's only memory and must never be overwritten.

Fill every section from real evidence in the repository. Sections you had to guess
at must be reported as guesses.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`
