# <Project name>: notes for Claude

<One line on what this project is and where its parts live.>

**Working the improvement loop? Read `docs/plans/LOOP_STATE.md` first and write it last.** It holds the queue, the
coverage map, the NEEDS-OWNER list and the standing invariants. Context is lost between sessions; that file is not.

## Hard rules

Each rule here that must hold without exception is also a hook in `.claude/hooks/`, wired in `.claude/settings.json`.
A blocked call says what to do instead. Fix a wrong block in the hook, by pull request; never route around it.

- **Never edit the live checkout.** `<path the running service uses>` is what runs: every session works on its own
  branch in its own worktree and lands by pull request (`live_checkout.py`; set `LOOP_LIVE_CHECKOUT`).
- **No `git stash` that can take another session's entry**: the stash stack is shared by every worktree. Set work
  aside with a WIP commit. `git_rules.py` blocks a bare `git stash`, `pop`, `clear`, and an `apply`/`drop` that names
  no entry; a tagged `git stash push -m <tag>`, restored by sha, is allowed. Never chain `git merge` with `add` and
  `commit` (`git_rules.py`).
- **Pull requests reach main one way: `scripts/land.sh <PR>`**, never `gh pr merge` or the merge button
  (`gh_rules.py`). `python3 scripts/prelanding.py` passes on the branch first.
- **Kill by PID, never by pattern** (`kill_rules.py`); **no `pgrep -f` wait loop that matches itself**
  (`waiter_guard.py`).
- **A helper is spawned under the lane cap** (`admission_gate.py`; `lane_ledger.py` records running lanes). A spawn
  prompt carries `Lane: <kind>; Hotspot: <area>`; without it the spawn counts as the default kind, with a warning.
  `spawn_gate.py` can also require a model and the rules (`docs/process/helper-rules.md`): opt in through
  `.loop/config.json`.
- <Your project's own hard rules: a shared device behind a lock, a test-only channel, a build slot. Add a hook for
  each one that must never fail.>

## Choosing what to build

<Where the ranked list lives and who reorders it. One milestone per pull request.>

## Commands

- Tests: `<test command>` (pick the smallest set that covers the change; say which and why).
- Before handing back: `python3 scripts/prelanding.py`.
- Land: `scripts/land.sh <PR>`.
- Hook tests: `for t in .claude/hooks/test_*.py; do python3 "$t" || echo "FAILED $t"; done`.
- Running lanes: `python3 .claude/hooks/lane_ledger.py list`. Caps, floors and gates: `.loop/config.json`.
- Watchdog (from the OS scheduler, every 15 minutes): `python3 scripts/watchdog.py`.

## Read when it applies

- Roles, spawning helpers, after a context loss → `docs/process/PLAYBOOK.md`
- The rules every helper follows → `docs/process/helper-rules.md`
- Landing: prelanding, the queue, red main → `docs/process/landing.md`
