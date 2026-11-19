# Playbook

How this project runs with one coordinator session (the *master*) and a few helper sessions (*lanes*). The hooks in
`.claude/hooks/` quote the section names below; keep them when you edit this file.

## Master checklist

- Register the session for the master-only hooks: `python3 .claude/hooks/master_session.py register`.
- Keep the lanes full, one lane per hotspot, under the cap in `.claude/hooks/admission_gate.py`.
- Every 30 minutes (a session cron): touch the heartbeat, read the event stream, land what is ready, refill lanes.
- Decide every reversible call yourself, act on it, and log it with how to reverse it; ask the owner only for what
  cannot be undone.

## Spawning a helper

The prompt carries the task, the model, `Lane: <kind>; Hotspot: <area>`, and "Read docs/process/helper-rules.md and
follow every rule in it" (`.claude/hooks/spawn_gate.py` checks for it). One task per helper, in its own worktree.

## Watching

<What the master looks at on each check-in: open pull requests, the land queue, the watchdog's flags, free disk.>

## After a context loss: rebuilding the master's state

`.claude/hooks/session_reminder.py` prints these steps after a compaction or resume: re-read this file, list open
pull requests and running landings, list helpers and their worktrees, re-arm the event Monitor and the check-in cron,
and re-register the session.

## Landing

See `docs/process/landing.md`.
