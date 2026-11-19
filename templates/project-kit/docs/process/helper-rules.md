# Helper rules

A helper starts with no memory of the conversation, so this file is its rulebook. The spawn prompt carries the task,
the model and `Lane: <kind>; Hotspot: <area>`, and tells the helper to read this file.

## Where and what

- One task per helper, in its own worktree, on its own branch from `origin/main`. Never stack pull requests.
- Never edit the live checkout. Never a bare `git stash` / `git stash pop`; set work aside with a WIP commit.
- Never chain `git merge` with `add` and `commit`; check the merge result first.
- Kill only PIDs you started; never `pkill -f <pattern>`.
- No secrets or personal values (ids, hostnames, emails, home paths) in code or docs.
- <Your project's own rules: design gates, devices, channels, shared files.>

## The pull request and landing

- Run `python3 scripts/prelanding.py` on your final head before handing back.
- Land only through `scripts/land.sh <PR>` (or the queue that runs it); never `gh pr merge`.
- Stop every Monitor and background task you started, then send one short report: what changed, tests run, the pull
  request, anything the master must decide.
