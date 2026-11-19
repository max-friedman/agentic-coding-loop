# agentic-coding-loop

[![checks](https://github.com/max-friedman/agentic-coding-loop/actions/workflows/checks.yml/badge.svg)](https://github.com/max-friedman/agentic-coding-loop/actions/workflows/checks.yml)

Hooks, a state file and a setup script for running several Claude Code agents on one
repo across many sessions.

I use this every day on a private project, an Android app plus a plugin for the agent
server it talks to. Since late September that project has had one coordinator session
and two to five helper sessions working in parallel, and about 1,900 pull requests
merged. Most of the hooks exist because an agent broke something on that project.

## Install

```bash
git clone https://github.com/max-friedman/agentic-coding-loop
python3 agentic-coding-loop/scripts/bootstrap_kit.py path/to/your/repo --dry-run
```

Drop `--dry-run` to apply it. The script adds its hooks to `.claude/settings.json`,
merging with what's already there and keeping a backup. It writes `CLAUDE.loop.md`
next to your `CLAUDE.md` instead of editing it. Then put your test command in
`.loop/config.json` under `prelanding.checks`, so `scripts/prelanding.py` has
something to run.

If you just want the idea, [docs/STARTER.md](docs/STARTER.md) is a state file and
three hooks you can copy by hand.

## The hooks

| Hook | What it stops |
|---|---|
| `admission_gate` | Starting a new agent past the cap, or when disk or memory is low |
| `lane_ledger` | Nothing. It records which agents are running so the cap can count them |
| `git_rules` | A bare `git stash` or `stash pop`, and `git merge` chained with a commit |
| `kill_rules` | `pkill -f` and `killall`, which also hit other sessions' processes |
| `waiter_guard` | A wait loop on `pgrep -f` that matches its own command line |
| `live_checkout` | Edits in the checkout a running service is deployed from |
| `gh_rules` | PRs against a branch other than main. Optionally, `gh pr merge` |
| `session_reminder` | Nothing. It prints how to rebuild state after a context reset |

I added the cap after finding 18 agents running at once while the coordinator's own
notes said five. The stash rule is there because one session's `git stash pop` picked
up another session's unfinished work; every worktree in a repo shares one stash list,
which I didn't know until then. And at one point I counted about 90 shell loops, some
a week old, waiting on `pgrep` patterns that matched their own command line.

When a hook blocks something it says what to do instead. [hooks/README.md](hooks/README.md)
lists the settings for each.

## The state file

Every session reads `docs/plans/LOOP_STATE.md` before doing anything and updates it
before it stops. Each round answers one question in one pull request and writes down
first what result would prove it wrong. This is from a benchmark I maintain:

```markdown
## Round 1: shortcut resistance
Finding: the claim was false. The probe hit 93.5% (floor 50%).
Fix: both scenarios in a pair now use the same text, and only one detail differs. Probe: 57.5%.
```

That benchmark's README claimed its paired test scenarios couldn't be gamed by keyword
matching. Nobody had measured that until the first round, which showed it was false.

## What I'd change in Claude Code

1. A scheduled run should fail when it did nothing. Mine reported SUCCEEDED five
   times with no tools loaded ([#37](https://github.com/max-friedman/agentic-coding-loop/issues/37)).
   Separately, the CLI login expired and every headless run failed for a week before
   I noticed.
2. There should be a built-in limit on concurrent subagents, and on the disk and
   memory they use. A limit written in a prompt didn't hold for me, and parallel
   sessions had no way to know they were sharing things like the stash list.

The longer version, with evidence, is in [docs/FOR_CLAUDE_CODE_TEAM.md](docs/FOR_CLAUDE_CODE_TEAM.md).

## Limitations

- I'm the only person who has used it. If you try it, I'd like to hear
  [what broke](https://github.com/max-friedman/agentic-coding-loop/issues/new?template=loop-proposal.yml).
- [LOOP.md](LOOP.md), the full protocol, is long. It's written for agents to follow
  more than for people to read.
- The kit's `land.sh` is simple. The landing queue I use depends on that project's
  builds and test phones, so it isn't included.
- The numbers above come from a private repo, so you can't check them here.
- This repo lags my private copy. I update it every few weeks.

To install it as a Claude Code plugin instead, see [docs/ADOPTING.md](docs/ADOPTING.md).
The longer write-up of what went wrong running several agents is
[docs/PARALLEL_LANES.md](docs/PARALLEL_LANES.md).

MIT license.
