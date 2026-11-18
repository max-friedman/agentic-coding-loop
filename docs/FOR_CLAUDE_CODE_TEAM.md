# For the Claude Code team: product gaps

What I hit running one coordinator and up to five helper agents for eight weeks on
one laptop, about 1,900 merged pull requests. Each gap: the user problem, the
evidence, and what I'd change. Ranked by a rough guess at reach × severity. The reach
column is a guess, not a measurement.

| rank | gap | who it affects (guess) | severity |
|---|---|---|---|
| 1 | Unattended runs report success when they did nothing | anyone running Routines, `claude -p` in cron, or CI jobs | high: silent for days |
| 2 | No built-in limit on concurrent agents or their resource use | anyone running parallel subagents or sessions on one machine | high: takes every session down |
| 3 | Parallel sessions collide on shared machine state | anyone running several sessions or worktrees at once | medium: lost work, stuck processes |
| 4 | A background task can end a subagent's turn for good | subagent users with long background jobs | medium |
| 5 | Compaction hand-offs depend on the agent remembering to write state | anyone running long sessions | medium |

## 1. Unattended runs report success when they did nothing

**Problem.** A scheduled run can fail in a way only a person can fix, and still show
green. Nobody looks at a green run.

**Evidence.**
- This repo's own round Routine fired five times from 17 to 29 September 2026,
  recorded SUCCEEDED each time, and produced no commit, branch, PR or issue
  ([#37](https://github.com/max-friedman/agentic-coding-loop/issues/37)). The
  sessions it started had no ToolSearch and no MCP tools at all, so the prompt's
  first step (attach the repository) could not run. Two earlier diagnoses in that
  issue were wrong: "no repository attached" and "a hardcoded, UUID-namespaced MCP
  tool name". Prompt rewrites aimed at the second one changed nothing, which is how
  the real cause was found. Before that, all three of this repo's Routines had done
  the same for about six weeks.
- In the app project, an unattended feedback loop's CLI login expired. Every run
  failed to authenticate for a week, and nobody noticed: the loop kept running on
  schedule.

**What I'd change.** A run that never used the tools its prompt needs, or ended on an
auth error, should not report SUCCEEDED. Show what each run produced next to its
status. Make an expired login in a non-interactive run a distinct, loud exit that
reaches the account owner.

## 2. No built-in limit on concurrent agents or their resource use

**Problem.** Nothing stops a busy coordinator from starting more agents than the
machine can hold.

**Evidence.** About 18 agents ran at once against a written limit of five. The load
average hit 51 and the service under test starved. A hook fixed it. Weeks later, with
the cap respected, the disk hit 0 GB (three landings died) and the laptop rebooted
out of memory.

**What I'd change.** A per-project setting for maximum concurrent subagents, and
optional floors for free disk and memory below which new agents wait. Show running
agents and their worktrees in one place.

## 3. Parallel sessions collide on shared machine state

**Problem.** Tools that are safe for one session are not safe for five.

**Evidence.**
- Claude Code runs a Bash call as `zsh -c '<command>'`, so a wait loop on
  `pgrep -f name` matches its own shell and never ends. About 90 such loops were
  found still running, some over a week old.
- `git stash` is one stack for every worktree of a repository, so one session's
  `stash pop` can take another session's work. A hook now refuses bare stash.
- One agent's `pkill -f` killed another agent's processes.

**What I'd change.** A native "wait for this process to exit" that notifies, so
nobody writes these loops. A warning, or a per-session default, for stash in a
worktree session.

## 4. A background task can end a subagent's turn for good

**Problem.** A subagent that starts a long job in the background and ends its turn
may never resume.

**Evidence.** A helper backgrounded its landing and ended its turn. It never came
back, and its PR sat as a draft until the coordinator noticed. A leftover background
monitor in another helper made it send its final report three times.

**What I'd change.** Keep a subagent alive, or wake it, until the background tasks it
started have finished. Stop a subagent's background tasks when it hands back.

## 5. Compaction hand-offs depend on the agent remembering to write state

**Problem.** Long sessions lose their thread when context runs out, unless the agent
wrote everything down first.

**Evidence.** Helpers ran out of context mid-chain twice in one night; both hand-offs
worked only because each kept a state file from its first step. The coordinator
needed a written rebuild procedure after every compaction, printed by a hook on
resume.

**What I'd change.** A first-class hand-off: the agent names the file it resumes
from, and the harness checks that file is recent before compacting.

All of these have workarounds in [`hooks/`](../hooks). Each workaround is a hook that
every project has to write again.
