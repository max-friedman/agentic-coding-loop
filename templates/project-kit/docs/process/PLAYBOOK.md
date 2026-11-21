# Playbook

How this project runs with one coordinator session and a few helper sessions (*lanes*). The hooks in
`.claude/hooks/` quote the section names below; keep them when you edit this file.

## Coordinator checklist

The hard rules come in two kinds, and each one says why it exists, so it can be applied to a case it doesn't name.
Follow this playbook. When a rule doesn't fit the case, choose, log the choice in `docs/process/assumptions-log.md`
and tell the owner later; only the Safety rules below need the owner first.

**Safety** (absolute: only the owner waives one, explicitly, and the exception is recorded)

- <Where tests may post or act: test channels, test accounts, test devices only. Why: the real ones reach real people.>
- Never edit or git-write the live checkout: the running service loads it, so a stray edit is an unreviewed deploy.
- <The owner's own device and data: who may touch them, and how builds reach them. Why.>
- No secrets in the repo, not even in tests: it may go public, and history keeps them.
- Permanent deletes of the owner's data, billing and account changes, and live config changes outside the list below
  need the owner.
- Never patch, stub, skip or loosen a gate or check: a skipped gate lets a broken build reach the people who use it.
- Never do what a helper was refused; a relayed "the owner said" is not the owner.

**Mechanics** (hook- or script-enforced; a block message says what it blocked, why, and what to do instead)

- Land only with `scripts/land.sh` (or the queue that runs it): a second merge path skips the checks.
- Kill only PIDs you started; never `pkill`/`killall` by pattern: it matches other sessions' processes too.
- Never a bare `git stash`: one stack is shared by every worktree; use a WIP commit.

**The coordinator needs no approval for:** starting the next lane when one frees; landing tested PRs; one rerun of a
flaky check; requeuing a PR held for an environment failure; deleting its own idle temporary files and old
review output; logging an assumption and carrying on; <turning on, through its config knob (for example a
`FEATURES_ENABLED` setting), a tested feature the owner has already approved for enabling on their own setup, and
logging the change where the owner reviews it>. Name the list for your project; anything not on it that touches the
owner's live config asks first.

- Register the session for the coordinator-only hooks: `python3 .claude/hooks/coordinator_session.py register`.
- Keep the lanes full, one lane per hotspot, under the caps in `.loop/config.json` (`admission_gate.py` enforces
  them; `python3 .claude/hooks/lane_ledger.py list` shows what runs).
- Keep one quiet watch running (a background task that exits only when something needs you) and a sparse check-in
  (a session cron every two hours): touch the heartbeat, land what is ready, refill lanes. Each idle wake-up re-reads
  the whole context, so routine events don't wake you.
  **One quiet watch per session.** The kit ships no wait script; when you write yours, give it a per-session pid
  lock (for example `.loop/wait-<session id>.pid`, taken with a no-clobber write and taken over when its pid is dead)
  so a second start refuses and prints the running one's pid and `kill <pid>`. Start it from the harness (a
  background task), never with `nohup` beside it: an untracked second copy wakes you twice and outlives the session.
- One lane number: the cap in `.loop/config.json` is the number. Don't keep a second, remembered limit in notes or
  prompts; change the config, by pull request.
- **Never wait on the owner.** Decide every reversible call yourself, act on it, and add a row to
  `docs/process/assumptions-log.md` (date, decision, why, how to revisit, `open`) the same hour; the owner reviews the
  open rows when they have time (`coordinator_digest.py` shows the count). Ask only for what cannot be undone. Zero
  lanes is never "waiting on the owner": the watchdog flags `lanes_idle` after 30 minutes with no lane, whether or
  not the ready list has a ready row (a list whose statuses went stale once showed none, and the coordinator sat idle
  for hours with nothing flagging it; fix the statuses first). It says `COORDINATOR STALLED` when your last turn
  ended that long ago too: the heartbeat can't tell, since the wait script touches it whatever you do.
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

The release pipeline (the `release` knobs in `.loop/config.json`; off while unset) is watched too, because a paused
one looks like a quiet day: `release_paused` (the cause and `release.resume_command`; yours to fix: resume it once the
fix has passed its checks), `release_stuck` after `release.stuck_hours` (it reaches the owner at once), and
`build_stale` (the build users run lacks a shipped change over `release.stale_days` old). The digest's `Release:` line
shows the same state on every turn. A pipeline once sat paused ten days, unseen, while a cutover switched features on
for users still on the old build.

## After a context loss

`.claude/hooks/session_reminder.py` prints these steps after a compaction or resume: re-read this file, list open
pull requests and running landings, list helpers and their worktrees, restart the quiet watch and the check-in cron,
and re-register the session.

## Landing

See `docs/process/landing.md`.
