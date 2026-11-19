# The agentic coding loop

[![checks](https://github.com/max-friedman/agentic-coding-loop/actions/workflows/checks.yml/badge.svg)](https://github.com/max-friedman/agentic-coding-loop/actions/workflows/checks.yml)

How I run Claude Code agents for weeks on one codebase so their work adds up instead
of drifting: a short protocol, a set of tested hooks, and a kit that installs both.

It comes from building a real product this way: an Android app plus the plugin for the
agent server it talks to. One coordinator session and up to five helper agents merged
about 1,900 pull requests in eight weeks, on one 16 GB laptop. That product is private;
this repo is the method, made generic.

## The problem

A single agent session is good at a task. Long-running work with many agents fails in
duller ways:

- **Sessions forget.** The next session relaxes a test the last one wrote, or redoes a
  fix it can't see.
- **Written rules get ignored.** About 18 agents ran at once against a limit of five
  that was written in the coordinator's own notes.
- **Parallel agents collide.** `git stash` is one stack for every worktree; one
  session's `stash pop` takes another's work.
- **Landing becomes the bottleneck.** Writing code got cheap; merging it safely didn't.
- **Unattended runs fail quietly.** A scheduled job reported success for weeks while
  doing nothing.

## What's in it

**A state file read first and written last.** Each round is one agent answering one
question in one pull request. It reads the state file, writes down what would prove
it wrong, does the work, and records what it found. Here, a round tested a claim in a
benchmark's own README:

```markdown
## Round 1 — shortcut resistance
Finding: the claim was false. The probe hit 93.5% (floor 50%).
Fix: both sides share an identical body; one signal swaps roles. Probe: 57.5%.
```

**Hooks for every rule that must hold.** A rule in a prompt is a suggestion; a hook is
a rule. When a hook blocks a call it says what to do instead:

```text
Blocked: this loop waits on `pgrep -f 'run_tests'`, which matches the loop's own
shell, so it never ends. Use `pgrep -f '[r]un_tests'`, or better, run the job in the
background and wait for its exit notification.
```

The [hooks](hooks/README.md) cap concurrent agents by count, disk and memory, block
bare `git stash` and blanket process kills, catch self-matching wait loops, and keep
agents out of the checkout a live service runs from. Each one is tested.

**A coordinator, lanes, and a size set by landing.** One session plans and merges.
Helpers each work in their own branch and worktree. How many run at once is set by how
fast work can land safely, not by how much work is waiting. Cutting from four lanes to
two, and splitting the files they shared, halved the tokens spent per merged change.

**The author never signs off.** A fresh agent that never saw the author's session
reviews the result: the build against the approved design, the claim against the
evidence. Its first night found real defects in nine PRs whose tests all passed.

**The human decides only what can't be undone.** Agents make reversible calls
themselves, act on them, and log each with how to reverse it. Spending money, acting
as the owner, anything public or irreversible still waits for the owner.

## Try it

- **Small:** [`docs/STARTER.md`](docs/STARTER.md): a state file and three hooks,
  copied by hand. Ten minutes.
- **Full kit:** `python3 scripts/bootstrap_kit.py <your-repo> --dry-run` shows what it
  would add, then run it without `--dry-run`. It merges into an existing
  `.claude/settings.json` and never overwrites your `CLAUDE.md`.
- **As a Claude Code plugin:** [`docs/ADOPTING.md`](docs/ADOPTING.md).

## What it showed about Claude Code

Gaps I hit, ranked by a guess at how many users they affect
([details and evidence](docs/FOR_CLAUDE_CODE_TEAM.md)):

1. **Unattended runs report success when they did nothing.** Scheduled sessions had
   no tools to attach the repo and still recorded SUCCEEDED
   ([#37](https://github.com/max-friedman/agentic-coding-loop/issues/37)); an expired
   CLI login failed every headless run for a week without a visible error.
2. **No built-in limit on concurrent agents or their resources.** Limits written in
   prompts didn't hold; the disk later hit zero with the agent count respected.
3. **Parallel sessions share state they can't see.** The stash stack, and shell
   wait loops that match themselves.

## By the numbers

From the private product, over about eight weeks:

| | |
|---|---|
| Pull requests merged | about 1,900, up to about 90 on a busy day |
| Agents at once | 1 coordinator and 2 to 5 lanes |
| Tests | about 5,000 unit tests, over 300 device scenarios on real phones |
| Hardware | one 16 GB laptop, one build at a time |

## Status

Used every day on that one private project. Nobody else has run it yet; if you try it,
[open an issue](https://github.com/max-friedman/agentic-coding-loop/issues/new?template=loop-proposal.yml)
with what broke. [`docs/ON_A_TEAM.md`](docs/ON_A_TEAM.md) covers how it maps to a team
and what I'd measure there.

## Deep dive

- [`docs/PARALLEL_LANES.md`](docs/PARALLEL_LANES.md): the lessons from running many agents, each with its incident.
- [`docs/WALKTHROUGH.md`](docs/WALKTHROUGH.md): one round end to end.
- [`LOOP.md`](LOOP.md): the full protocol, written for agents to follow.
- [`hooks/README.md`](hooks/README.md): every hook, what it blocks, and its settings.
- [`CHANGELOG.md`](CHANGELOG.md): release history.

## License

MIT.
