---
name: loop-init
description: Bootstrap the continuous-improvement loop in a repository — optionally install the project kit (hooks and settings, a CLAUDE.md skeleton, process docs, prelanding and landing scripts, the watchdog), then write docs/plans/LOOP_STATE.md with a real gate command, coverage map, queue and invariants, and add the loop pointer to the project rules file. Use when adopting the loop in a repository that has no state file yet.
when_to_use: A repository has no docs/plans/LOOP_STATE.md and the loop is being adopted. Trigger phrases include "set up the loop", "adopt the loop here", "initialize the improvement loop", "start the loop on this repo", "bootstrap this project", "install the project kit". Refuses to run if a state file already exists.
---

# Bootstrap

Run **§B Bootstrap** of the protocol below, then stop. Do not run a round in the
same session — round 0 is the state file itself.

Hard precondition: if `docs/plans/LOOP_STATE.md` already exists, STOP and report
its current status. It is the project's only memory and must never be overwritten.

Fill every section from real evidence in the repository. Sections you had to guess
at must be reported as guesses.

**The project kit (when asked for the whole working environment, or the repository
is new).** Before §B, install it and run its hook tests:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap_kit.py" . --no-state --test
```

It never overwrites an existing file. Then fill the kit's `<placeholders>` in
`CLAUDE.md` and `docs/process/` from the repository, set `LOOP_LIVE_CHECKOUT` in
`.claude/settings.json`, and list each hook in the rules file's mechanisms table.
Report any hook test that failed; do not edit a hook to make it pass.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`
