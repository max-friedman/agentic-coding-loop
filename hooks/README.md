# Hooks

Generic, trimmed versions of the Claude Code hooks that enforce the hard rules in the
multi-agent project behind [`LOOP.md`](../LOOP.md) §F. Stdlib Python, no project
paths, thresholds as constants. Copy what you need; wire it with
[`settings.example.json`](settings.example.json) (it goes in your project's
`.claude/settings.json`). Tests: `python3 hooks/test_hooks.py`, run by this repo's gate.

| hook | blocks | why | on its own error |
|---|---|---|---|
| [`admission_gate.py`](admission_gate.py) | an agent spawn past the lane cap, onto a held hotspot, with free disk under 15 GB or swap over 6 GB | 18 agents once ran against a written cap of 5; later the disk hit zero with the cap respected | fails **closed** |
| [`git_rules.py`](git_rules.py) | a bare `git stash` / `pop` / `drop`, and `git merge` chained with `add` or `commit` | the stash stack is shared by every worktree; chained merges pushed conflict markers four times | fails open |
| [`kill_rules.py`](kill_rules.py) | `pkill` and `killall` | one agent's pattern kill took out another agent's processes | fails open |
| [`waiter_guard.py`](waiter_guard.py) | a wait loop whose `pgrep -f` pattern matches its own command line | about 90 such loops were found still running, some over a week old | fails open |
| [`live_checkout.py`](live_checkout.py) | edits and git writes in the checkout a live service runs from | an edit there is an unreviewed deploy | fails **closed** |
| [`watchdog.py`](watchdog.py) | (not a hook) a scheduled job outside any session: flags low disk, a job that keeps failing to log in, a silent coordinator, its own missed runs | an expired login failed every run for a week, unseen | prints what it can |

Hooks follow Claude Code's contract: the tool call arrives as JSON on stdin; exit
code 2 with a message on stderr blocks it. A blocked call always says what to do
instead. Fail closed when the thing guarded can't be undone; fail open when it can.
A wrong block is fixed in the hook, by pull request. An agent that routes around a
hook is the incident, not the hook.

Not included: the ledger writer for `admission_gate.py` (PostToolUse and
SubagentStop hooks that add and remove running lanes), the merge queue, and the
watchdog's notification wiring. Those depend on each project's own scripts and
channels.
