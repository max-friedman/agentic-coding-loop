# The agentic coding loop

**A coding agent forgets everything between sessions. This is the file that
remembers, and the protocol that makes forgetting survivable.**

Long-running agent work fails in a characteristic way. Session one is excellent.
Session four re-derives what session two established, re-litigates a decision
already made, and quietly relaxes an assertion that was inconvenient. Nothing
looks broken. The tests are green. The work has stopped compounding.

The fix is not a bigger context window. It is a **written spine**: one file the
agent must read before acting and write before stopping, holding the queue, the
coverage map, the blocked items, and the invariants that may not be weakened.
Everything else in this repo exists to support that file.

## Install

```
/plugin marketplace add max-friedman/agentic-coding-loop
/plugin install loop@agentic-coding-loop
```

Then, in any project:

| command | what it does |
|---|---|
| `/loop-init` | Reads the project, drafts its `docs/plans/LOOP_STATE.md`, adds the loop section to `CLAUDE.md`. Won't overwrite an existing state file. |
| `/loop-round` | Runs one round. Optional argument overrides the queue: `/loop-round tighten the retry test`. |
| `/loop-audit` | Ships nothing. Measures whether the project's strongest claim still holds. |
| `/loop-feedback` | Packages a learning about the loop as a proposal for upstream review. |

All four are `/`-invocable only — Claude won't start a round on its own, since a
round mutates the repo and costs a session.

Not using Claude Code? The loop is plain markdown and assumes nothing about the
harness — see [`docs/ADOPTING.md`](docs/ADOPTING.md) for the copy-the-templates and
other-agent paths.

## What's here

| file | what it is |
|---|---|
| [`plugins/loop/`](plugins/loop) | The four skills. `skills/loop-round/SKILL.md` is the canonical round text. |
| [`templates/LOOP_STATE.template.md`](templates/LOOP_STATE.template.md) | The spine, blank, with per-section guidance. |
| [`templates/PROJECT_RULES.template.md`](templates/PROJECT_RULES.template.md) | The `CLAUDE.md` / `AGENTS.md` the agent reads on every session. |
| [`docs/PROTOCOL.md`](docs/PROTOCOL.md) | What one round is, step by step, and the four ways it can end. |
| [`docs/PRINCIPLES.md`](docs/PRINCIPLES.md) | The eight rules the loop runs on, and what each one prevents. |
| [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md) | Four real rounds, including the one that proved the project's central claim false. |
| [`docs/ADOPTING.md`](docs/ADOPTING.md) | Setup for Claude Code, for copy-paste, and for other agents. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How feedback flows in, and why a merge alone changes nothing downstream. |
| [`examples/tactbench-LOOP_STATE.md`](examples/tactbench-LOOP_STATE.md) | A real, filled-in state file after four rounds. |

The first line of your project rules should be the pointer, because it is the
only thing a cold agent is guaranteed to read:

```markdown
**Working the improvement loop? Read [`docs/plans/LOOP_STATE.md`](docs/plans/LOOP_STATE.md)
first and write it last.** It holds the queue, the coverage map, the NEEDS-MAX list,
and the standing invariants. Context is lost between rounds; that file is not.
```

## The shape of a round

Read state → pick one item → **ask what would prove it wrong** → build the check
first → build the thing → verify → write state.

The third step is what separates this from a task list. An agent asked to
"improve the dataset" will improve the dataset and report success. An agent asked
to *measure whether the dataset's central claim holds* may come back with the
claim refuted — which is the outcome worth having. See
[`docs/PROTOCOL.md`](docs/PROTOCOL.md).

## Does it work?

One data point, reported honestly. Four rounds on
[TactBench](docs/CASE_STUDY.md), a benchmark whose README claimed its matched-pair
design defeated keyword matching.

Round 1's assignment was not "add features." It was "build a probe that would
detect the failure this project claims to be immune to." The probe scored
**93.5% against a 50% floor**. The claim was false, and had been false since the
first commit — the headline numbers in the README were measuring leakage, not
skill.

That round then rebuilt the generator around role permutation (93.5% → 57.5%),
collapsed the reference heuristic from 0.818 precision to chance where it
belonged, and caught a set of inverted labels on the way. Round 3 added three
scenario families; the same probe flagged one of them at 82.5% **before it
landed**, from a one-token asymmetry no reviewer would have seen by eye.

A round that deletes a false claim is a good round. The loop is built to make
that outcome reachable rather than embarrassing.

## The parts that matter most

**NEEDS-MAX.** Items that cannot proceed without a human — a credential, a
budget approval, a decision that isn't yours. They are recorded with the exact
command that unblocks them, then skipped. They are never a reason to halt the
loop, and never a reason to fake the result. TactBench's LLM harness has been
built, tested, and cached for three rounds without ever being run, because no API
key exists. Zero numbers about it appear anywhere in that repo.

**Standing invariants.** Properties encoded as tests, with a written prohibition
on weakening them. When one fails, the code is wrong, not the assertion. This is
the single highest-value line in the whole system, because relaxing an assertion
is always the locally cheapest way to make a round pass.

**Noted, not built.** A section for ideas examined and deliberately rejected,
with the reasoning. Without it, every round rediscovers the same dead end.

## Feedback, and why it goes through review

Projects running the loop learn things about the loop. `/loop-feedback` packages
one as a proposal and files it as an issue here.

It does not take effect. That is the design:

```
/loop-feedback  →  issue  →  proposals/*.md  →  maintainer writes the change
                             (inert)             →  PR + review  →  version bump
                                                                    ↑
                                                        the moment it goes live
```

Two properties worth stating plainly.

**`proposals/` is inert, and that is a security boundary rather than a filing
convention.** Downstream agents write proposals; upstream agents read this repo. If
proposals were read as instructions, any project running the loop could change how
the loop behaves in *every other project running it*, unreviewed. So nothing in
this repo loads or executes anything from `proposals/`, and the only path from a
suggestion to a behavior change runs through a human writing that change by hand.

**A merge alone changes nothing downstream.** The plugin carries an explicit
`version`, so consumers keep what they have until it is bumped and released. That
costs a version bump per release and buys a second look before anything reaches
someone else's repository.

Full flow, and what gets accepted or rejected: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT. Use it, fork it, strip the parts you disagree with.
