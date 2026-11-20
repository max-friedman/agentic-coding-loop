# Helper rules

A helper starts with no memory of the conversation, so this file is its rulebook. The spawn prompt carries the task,
the model and `Lane: <kind>; Hotspot: <area>`, and tells the helper to read this file.

## Where and what

- One task per helper, in its own worktree, on its own branch from `origin/main`. Never stack pull requests. After a
  PR's third conflict, rebuild it fresh on main.
- **Your worktree goes in a managed dir** (`git_rules.worktree_dirs`: `.claude/worktrees/` or `../<repo>-worktrees/`),
  never anywhere else, and you remove it (`git worktree remove <path>`) once your PR is queued. Worktrees elsewhere are
  forgotten and fill the disk. `git_rules.py` blocks a helper's `git worktree add` outside them;
  `scripts/worktree_gc.py` removes finished ones anywhere.
- Never edit the live checkout. Set work aside with a WIP commit, not `git stash`: the stash stack is shared by every
  worktree (a tagged `git stash push -m <tag>`, restored by sha, is the only stash the hook allows).
- Never chain `git merge` with `add` and `commit`; check the merge result first.
- Kill only PIDs you started; never `pkill -f <pattern>`.
- No secrets or personal values (ids, hostnames, emails, home paths) in code or docs.
- **Never skip, stub or loosen a gate**: no `--no-verify`, no wrapper that fakes a pass, no env var that turns a check
  off on the command line, no landing override flag (those are the coordinator's, and logged). `git_rules.py` blocks the
  common forms. If a gate is wrong, hand back with its output; the gate gets fixed in its own pull request.
- **A gate change is its own pull request.** A branch that changes a gate (a file that decides what runs, what is
  skipped or what passes: the landing scripts, the hooks, their settings, CI) together with product code is refused by
  `prelanding.py` unless its body says `Gate change: reviewed by <reviewer>`, naming a fresh reviewer agent or the owner,
  never you and never the coordinator. Split it out when you can.
- **Write each PR body to its own file** (`body<PR>.md` in your worktree, or `$TMPDIR/<PR>/body.md`), never a shared
  `pr_body.md`: two PRs sharing one once got each other's body. `gh_rules.py` warns on a shared path.
- **A check that picks where something runs fails closed.** When the list that says "this needs the strict target"
  can't be read, send everything to the strict target; never treat an unreadable list as empty, or the checks it
  names get skipped and read as passed.
- <Your project's own rules: design gates, devices, channels, shared files.>

## The pull request and landing

- Run `python3 scripts/prelanding.py` on your final head before handing back. A stale or badly resolved merge that
  undoes lines main gained is refused there; merge main again keeping both sides (or say `Intentional revert: <why>`).
- Your own work is never reviewed by you: user-visible results and gate changes get a fresh reviewer that did not
  write or steer the work.
- Land only through `scripts/land.sh <PR>` (or the queue that runs it); never `gh pr merge`.
- Stop every Monitor and background task you started, then send one short report: what changed, tests run, the pull
  request, anything the coordinator must decide.
