# agentic-coding-loop

[![checks](https://github.com/max-friedman/agentic-coding-loop/actions/workflows/checks.yml/badge.svg)](https://github.com/max-friedman/agentic-coding-loop/actions/workflows/checks.yml)

A working system for running a team of Claude Code agents on one codebase for weeks,
and still shipping code you can trust. One person used it to merge about 1,900 pull
requests in eight weeks.

## The problem

Coding agents are now good at finishing a single task. The problems start when you
use several of them at once, or one of them across many sessions.

- Each new session starts with no memory, so it undoes or repeats earlier work.
- Agents ignore rules written in their prompts once they get busy.
- Agents running in parallel break each other's work through shared state they can't see.
- Finished work piles up faster than it can be reviewed and merged safely.
- Automated runs fail silently and report success.

The result is that adding more agents stops adding more shipped work. Writing code got
cheap. Coordinating it and landing it safely did not.

## Who it's for

Developers and small teams who run two or more coding agents on the same repo, or one
agent over weeks, and want the work to keep adding up.

## What I built

1. **A one-command setup** that installs the whole working environment into any repo:
   the hooks, the settings, a starting `CLAUDE.md`, process docs and a state file.
2. **Twelve Claude Code hooks** that enforce the rules agents break. They cap how many
   agents run at once and stop them when disk or memory runs low. They block the git
   and shell commands that let one agent destroy another's work, and they keep agents
   out of anything a live service depends on.
3. **A state file protocol.** Every session reads one file first and updates it last,
   so the next session picks up where the last one stopped. Each round of work starts
   by writing down what result would prove it wrong.
4. **A team model.** One coordinator agent plans and merges. Two to five helper agents
   each work in their own branch. The team size is set by how fast work can be merged
   safely, not by how much work is waiting.

## Results

I've run this since late September on my own project, an Android app plus a plugin for
the agent server it talks to.

| | |
|---|---|
| Pull requests merged | about 1,900 in eight weeks, up to about 90 in one day |
| People | one, plus one coordinator and two to five helper agents |
| Cost per merged change | cut roughly in half after sizing the team to the merge path |
| Quality | an independent review agent found real bugs in nine PRs that had passed every test, on its first night |
| Tests | about 5,000 unit tests and over 300 device tests on real phones |

The same method found a false claim in a benchmark I maintain. Its README said the
test cases couldn't be gamed by keyword matching. The first round measured it: a
simple keyword probe scored 93.5% where it should have scored about 50%.

## How it works

Every rule that matters is a hook. I learned this after finding 18 agents running at once while the coordinator's own notes said five.
A hook now refuses the sixth. When a hook blocks something, it tells the agent what to
do instead:

```text
Blocked: this loop waits on `pgrep -f 'run_tests'`, which matches the loop's own
shell, so it never ends. Use `pgrep -f '[r]un_tests'`, or run the job in the
background and wait for its exit notification.
```

No agent approves its own work. A fresh agent that never saw the original session
reviews it.

The human only decides what can't be undone. Agents make every reversible call
themselves, act on it, and log it with how to reverse it. I review the log when I
have time. That keeps me out of the critical path without giving up control of
anything that matters.

## What it taught me about Claude Code

Running agents this hard surfaced product gaps I'd prioritize:

1. **Automated runs should fail loudly when they did nothing.** My scheduled runs
   reported success five times with no tools loaded
   ([#37](https://github.com/max-friedman/agentic-coding-loop/issues/37)), and an
   expired CLI login failed every headless run for a week before I noticed.
2. **Claude Code should limit concurrent agents and the resources they use.** Limits
   in a prompt don't hold, and parallel sessions can't see state they share, like
   git's stash list.

The full write-up, with evidence for each, is in
[docs/FOR_CLAUDE_CODE_TEAM.md](docs/FOR_CLAUDE_CODE_TEAM.md).

## Try it

```bash
git clone https://github.com/max-friedman/agentic-coding-loop
python3 agentic-coding-loop/scripts/bootstrap_kit.py path/to/your/repo --dry-run
```

Drop `--dry-run` to apply it. It merges into your existing `.claude/settings.json` and
never edits your `CLAUDE.md`. For a lighter start, [docs/STARTER.md](docs/STARTER.md)
is a state file and three hooks you can copy by hand. To install it as a Claude Code
plugin, see [docs/ADOPTING.md](docs/ADOPTING.md).

## Status

I'm the only user so far. The numbers above come from a private repo, so they can't be
checked here. I update this repo from my private copy every few weeks. If you try it,
I'd like to hear
[what worked and what broke](https://github.com/max-friedman/agentic-coding-loop/issues/new?template=loop-proposal.yml).

More detail: [lessons from running several agents](docs/PARALLEL_LANES.md),
[every hook and its settings](hooks/README.md), [the full protocol](LOOP.md).

MIT license.
