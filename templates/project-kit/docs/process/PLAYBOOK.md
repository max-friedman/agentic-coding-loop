# Playbook

How this project runs with one coordinator session and a few helper sessions (*lanes*). The hooks in
`.claude/hooks/` quote the section names below; keep them when you edit this file.

## Coordinator checklist

- Register the session for the coordinator-only hooks: `python3 .claude/hooks/coordinator_session.py register`.
- Keep the lanes full, one lane per hotspot, under the caps in `.loop/config.json` (`admission_gate.py` enforces
  them; `python3 .claude/hooks/lane_ledger.py list` shows what runs).
- Keep one quiet watch running (a background task that exits only when something needs you) and a sparse check-in
  (a session cron every two hours): touch the heartbeat, land what is ready, refill lanes. Each idle wake-up re-reads
  the whole context, so routine events don't wake you.
- One lane number: the cap in `.loop/config.json` is the number. Don't keep a second, remembered limit in notes or
  prompts; change the config, by pull request.
- **Never wait on the owner.** Decide every reversible call yourself, act on it, and add a row to
  `docs/process/assumptions-log.md` (date, decision, why, how to revisit, `open`) the same hour; the owner reviews the
  open rows when they have time (`coordinator_digest.py` shows the count). Ask only for what cannot be undone. Zero
  lanes while ready work exists is never "waiting on the owner": the watchdog flags it as `lanes_idle`.
- **A rule the owner gives you goes into these docs by pull request the same day**, not only into your private notes:
  notes die with the session and no hook enforces them. The watchdog flags `rule_drift` when a rule note is newer than
  the last commit here.
- You are never the reviewer of work you steered: a fresh reviewer agent or the owner reviews gate changes and
  user-visible work.

## Spawning a helper

The prompt carries the task, the model, `Lane: <kind>; Hotspot: <area>`, and "Read docs/process/helper-rules.md and
follow every rule in it" (`.claude/hooks/spawn_gate.py` checks for the last two once `spawn_gate.require_model` and
`require_rules` are on in `.loop/config.json`). One task per helper, in its own worktree.

## Watching

<What the coordinator looks at on each check-in: open pull requests, the land queue, the watchdog's flags, free disk.>
Schedule next to the watchdog: `python3 scripts/worktree_gc.py --apply` (finished worktrees, anywhere) and
`python3 scripts/waiter_reaper.py --apply` (orphaned waiter shells).

## After a context loss

`.claude/hooks/session_reminder.py` prints these steps after a compaction or resume: re-read this file, list open
pull requests and running landings, list helpers and their worktrees, restart the quiet watch and the check-in cron,
and re-register the session.

## Landing

See `docs/process/landing.md`.
