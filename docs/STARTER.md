# Starter: the 20% version

You don't need lanes, a merge queue or a watchdog to get most of the value. Start
with a state file and three hooks. Add the rest only when a failure asks for it.

## 1. A state file the agent reads first and writes last

Copy [`../templates/LOOP_STATE.template.md`](../templates/LOOP_STATE.template.md) to
`docs/plans/LOOP_STATE.md`. Fill in four sections and leave the rest empty:

- **Current status**: the test command and whether it passes.
- **Queue**: the next few pieces of work, each written as a question that could
  come out "no".
- **NEEDS-OWNER**: what only you can unblock, with the exact command.
- **Standing invariants**: what must never break, each with the test that guards it.

Put one line at the top of your `CLAUDE.md`: *Read `docs/plans/LOOP_STATE.md` first
and write it last.*

## 2. Three hooks

Copy these and `_shell.py`, which they share, from [`../hooks/`](../hooks) into your
project's `.claude/hooks/`, and the matching entries from the kit's
[`settings.json`](../templates/project-kit/.claude/settings.json) into
`.claude/settings.json`. They need no other setup.

| hook | stops |
|---|---|
| `git_rules.py` | a `git stash` that can take another worktree's entry; a merge chained with commit |
| `waiter_guard.py` | wait loops that wait on themselves forever |
| `kill_rules.py` | one agent killing another agent's processes by pattern (`pkill -f`, `killall`) |

## 3. When to add more

| when this happens | add |
|---|---|
| You run more than two agents at once | `admission_gate.py` and its ledger writer, `lane_ledger.py` |
| A service runs from your checkout | `live_checkout.py` |
| You schedule unattended runs | `watchdog.py`, reading each job's own output |
| PRs wait in line to merge | one merge script, then a queue ([`../LOOP.md`](../LOOP.md) §F) |
