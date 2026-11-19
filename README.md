# The agentic coding loop

[![checks](https://github.com/max-friedman/agentic-coding-loop/actions/workflows/checks.yml/badge.svg)](https://github.com/max-friedman/agentic-coding-loop/actions/workflows/checks.yml)

**How I run a team of Claude Code agents on one codebase for weeks.**

A year ago the hard part was getting an agent to finish a task. Now the hard part is
everything after that. Ten sessions in a row that don't remember each other. Five
agents on one laptop at once. A pile of finished work that still has to land safely.

I built an Android app and its agent server plugin this way. One coordinator session,
up to five helper agents, **about 1,900 merged pull requests in eight weeks**. That
product is private. This repo is the part that transfers to any project.

```bash
git clone https://github.com/max-friedman/agentic-coding-loop
python3 agentic-coding-loop/scripts/bootstrap_kit.py <your-repo> --dry-run
```

## The pain points

The model was rarely the problem. The workflow around it was.

- The next session can't see why a test exists, so it relaxes it.
- A limit in the prompt is only a suggestion. I once found **18 agents running against a limit of five** written in the coordinator's own notes.
- Parallel sessions share state they don't know about, like one `git stash` stack across every worktree.
- A scheduled run reported success for weeks while doing nothing.
- Once code got cheap to write, landing it safely became the bottleneck.

## What I do about it

**Keep one state file.** Every round reads it first and writes it last. Each round
answers one question in one pull request, and starts by writing down what would prove
it wrong. The first round on one of my own projects disproved a claim in its README:

```markdown
## Round 1: shortcut resistance
Finding: the claim was false. The probe hit 93.5% (floor 50%).
```

**Enforce rules with hooks.** If a rule has to hold, it's a hook that blocks the call
and says what to do instead:

```text
Blocked: this loop waits on `pgrep -f 'run_tests'`, which matches the loop's own
shell, so it never ends. Use `pgrep -f '[r]un_tests'`, or run the job in the
background and wait for its exit notification.
```

**Size the team to the merge path.** More agents meant a longer queue, not more
shipped work. Going from four helpers to two, and splitting the files they fought
over, **cut the cost of each merged change roughly in half**.

**Never let the author approve its own work.** A fresh agent that never saw the
session checks the build against the design. On its first night it found real bugs in
nine PRs that had passed every test.

**Only ask the human about what can't be undone.** The agents decide everything else,
log it, and keep going. I read the log when I have time.

## What it taught me about Claude Code

The gaps I'd fix first. Evidence is in [`docs/FOR_CLAUDE_CODE_TEAM.md`](docs/FOR_CLAUDE_CODE_TEAM.md).

1. **Unattended runs report success when they did nothing.** Scheduled sessions came
   up without tools and still said SUCCEEDED
   ([#37](https://github.com/max-friedman/agentic-coding-loop/issues/37)). An expired
   CLI login failed every headless run for a week without an error anyone could see.
2. **Nothing caps concurrent agents or what they use.** Prompt limits don't hold. The
   disk still hit zero after the agent count was under control.
3. **Parallel sessions share state they can't see.** The stash stack is one example.
   Shell wait loops that match their own command line are another.

## Try it

1. Start small with [`docs/STARTER.md`](docs/STARTER.md): a state file and three hooks, copied by hand.
2. Or run the full kit with the two lines above. It merges into your existing `.claude/settings.json` and never touches your `CLAUDE.md`.
3. Or install it as a plugin: [`docs/ADOPTING.md`](docs/ADOPTING.md).

## Status

I iterate on this every day in a private project and publish the generic parts here
periodically. Nobody else has run it yet. If you try it, I'd appreciate hearing
[what broke](https://github.com/max-friedman/agentic-coding-loop/issues/new?template=loop-proposal.yml).

## More

- [Lessons from running many agents](docs/PARALLEL_LANES.md)
- [One round, end to end](docs/WALKTHROUGH.md)
- [Every hook and what it blocks](hooks/README.md)
- [The full protocol](LOOP.md)
- [How this maps to a team](docs/ON_A_TEAM.md)

MIT licensed.
