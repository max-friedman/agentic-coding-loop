# The agentic coding loop

[![checks](https://github.com/max-friedman/agentic-coding-loop/actions/workflows/checks.yml/badge.svg)](https://github.com/max-friedman/agentic-coding-loop/actions/workflows/checks.yml)

One person running a fleet of Claude Code agents to build and ship a real product:
an Android app and the plugin for the agent server it talks to. One coordinator
session plans and merges. Up to five helper agents build in parallel, each in its own
worktree. Hooks enforce the hard rules, so they hold even when an agent forgets them.

This repo is that process, written down to reuse. The product's code is private.

**Words used here.** A *round* is one agent answering one question in one pull
request: it reads a state file first and writes it last, so the next memoryless
session can continue. A *lane* is one agent running rounds in its own branch and
worktree, beside others. The *coordinator* is the session that starts lanes, reviews
their work and merges it.

## For the Claude Code team

The three gaps that cost me most, ranked by a guess at reach × severity
([all five, with evidence](docs/FOR_CLAUDE_CODE_TEAM.md)):

1. **Unattended runs report success when they did nothing.** This repo's round
   Routine recorded SUCCEEDED five times with no output: its sessions had no MCP
   tools, so it couldn't attach the repo
   ([#37](https://github.com/max-friedman/agentic-coding-loop/issues/37)). Separately,
   an expired CLI login failed every run for a week, unseen. *Likely affects anyone
   running Routines, cron or CI jobs.*
2. **No built-in limit on concurrent agents or their resources.** About 18 agents ran
   against a written limit of 5 and starved the machine; later the disk hit zero with
   the cap respected. *Affects anyone running parallel agents on one machine.*
3. **Parallel sessions collide on shared state.** About 90 `pgrep -f` wait loops
   matched their own shell and never ended; `git stash` is one stack for every
   worktree. *Affects anyone running several sessions at once.*

## Outcomes and scale

About eight weeks, late September to mid November 2026. These numbers come from the private app project's own history; what's published here is the process and the six generic hooks, not that project's code.

| | |
|---|---|
| Pull requests merged | about 1,900; up to about 90 on a busy day |
| Agents at once | 1 coordinator + 2 to 5 lanes |
| Device tests | over 300 end-to-end scenarios on an emulator and real test phones |
| Unit tests | about 5,000 JVM tests, plus about 1,600 tests for the tooling |
| Enforcement | 16 hooks; one merge queue, the only way onto main |
| Releases | a test build of main about hourly; the full suite every night |
| Hardware | one 16 GB laptop, one build slot, a few test devices |
| Cost per merged change | 400–700k tokens with four feature lanes, 215–325k with two after shared files were split; three changes landed together, so no single one owns the drop |

## How work flows

```mermaid
flowchart LR
    F[Feedback and<br/>ranked list] --> P[Coordinator plans<br/>one slice per PR]
    P --> L[Lanes, each in<br/>its own worktree]
    L --> PL[Prelanding: cheap<br/>checks on branch + main]
    PL --> R[Independent review<br/>by a fresh agent]
    R --> Q[Land queue: merge main,<br/>check, batch, deploy]
    Q --> N[Nightly full suite]
    N -. reds become work .-> F
```

## Three ideas

**The human decides only what can't be undone.** Agents make every reversible call
themselves, act on it, and log it with how to reverse it. The owner reviews the log
in one pass. *Why:* one night the coordinator held every lane idle, waiting on calls
it could have undone in minutes.

**Hooks are the guardrails.** Every rule that must hold without exception is a hook:
no edits in the live checkout, no device use outside its lock, no spawn past the cap,
no merge outside the queue. A blocked call says what to do instead. *Why:* the agent
that started 18 agents had the limit of 5 in its own notes.

**The author never signs off.** A fresh reviewer that never saw the author's session
compares the real build with the approved design, state by state. *Why:* a release
reached the owner unlike its designs with every test green; the reviewer's first
night found real defects in nine PRs.

## Who this is for

- **For** people running two or more coding agents on one codebase, or one agent
  across many sessions, who need the work to compound instead of drift.
- **Not for** a single quick session, or a team that already has CI, a merge queue
  and code review and runs one agent at a time. You have most of this already.

Start small: [`docs/STARTER.md`](docs/STARTER.md) is a state file and three hooks.

## Use it in your project

`python3 scripts/bootstrap_kit.py <your-repo> --test` installs the whole working environment: hooks and settings, a
`CLAUDE.md` skeleton, process docs, prelanding and landing scripts, the watchdog and the state file. The kit is
harvested from the project that runs the loop, so it is what that project uses today; the `loop-init` skill runs it too.

## Status

- **Last round:** Round 4 run on 2026-11-18 by hand to restart; scheduled rounds
  still paused. It found that the docs promised every project was pinned to a
  release, while every non-plugin path fetches from `main`
  ([state file](docs/plans/LOOP_STATE.md)).
- **Why scheduled rounds are paused:** the round Routine's sessions had no tools to
  attach the repo, so it recorded SUCCEEDED and did nothing (#37). No date is set
  for them to resume.
- **Nothing merges itself.** The owner reviews and merges every PR; the 24-hour
  self-merge described in [`CONTRIBUTING.md`](CONTRIBUTING.md) is off.
- **One author.** Nobody else has run this yet. [`docs/ON_A_TEAM.md`](docs/ON_A_TEAM.md)
  says what I'd measure to find out, and how I'd find a first outside user.

## Where to look

| | |
|---|---|
| [`docs/STARTER.md`](docs/STARTER.md) | The 20% version: a state file and three hooks. |
| [`hooks/`](hooks) | Tested, generic hooks and an example settings file. |
| [`docs/PARALLEL_LANES.md`](docs/PARALLEL_LANES.md) | The top ten lessons from the multi-agent project, each with its incident. |
| [`docs/WALKTHROUGH.md`](docs/WALKTHROUGH.md) | One round end to end: the state file before, the finding, the PR. |
| [`docs/ON_A_TEAM.md`](docs/ON_A_TEAM.md) | How this maps to a team, what to measure, a first outside user. |
| [`LOOP.md`](LOOP.md) | The full protocol, written for agents. |
| [`docs/ADOPTING.md`](docs/ADOPTING.md) | Installing it as a Claude Code plugin, and its skills. |
| [`CHANGELOG.md`](CHANGELOG.md) | What changed, release by release, and why. |

## License

MIT. Use it, fork it, strip the parts you disagree with.
