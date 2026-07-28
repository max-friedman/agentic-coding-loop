# The agentic coding loop

**A coding agent forgets everything between sessions. This is the file that
remembers, the protocol that makes forgetting survivable, and the rules for
repeating it until there is nothing left to do.**

Long-running agent work fails in a characteristic way. Session one is excellent.
Session four re-derives what session two established, re-litigates a decision
already made, and quietly relaxes an assertion that was inconvenient. Nothing
looks broken. The tests are green. The work has stopped compounding.

The fix is not a bigger context window. It is a **written spine**: one file the
agent must read before acting and write before stopping, holding the queue, the
coverage map, the blocked items, and the invariants that may not be weakened.

## For agents

Read **[`LOOP.md`](LOOP.md)**. It is self-contained — round steps, hard rules,
ending states, audit rounds, bootstrap, feedback, and continuous operation. One
fetch, no dependencies:

```
https://raw.githubusercontent.com/max-friedman/agentic-coding-loop/main/LOOP.md
```

Then check the **Domains** table in [`llms.txt`](llms.txt) — optional, additive
layers (e.g. a UX-roast domain for user-facing products) that a matching project
should fetch alongside `LOOP.md`, before bootstrapping. No match → proceed
core-only.

Machine index at [`llms.txt`](llms.txt). Repo conventions at [`AGENTS.md`](AGENTS.md).

## For Claude Code

```
/plugin marketplace add max-friedman/agentic-coding-loop
/plugin install loop@agentic-coding-loop
```

Five skills. Each inlines `LOOP.md` at load time, so there is exactly one copy of
the protocol and no way for a skill to drift from it.

| skill | what it does |
|---|---|
| `loop-init` | Bootstraps `docs/plans/LOOP_STATE.md` from the real project. Refuses to overwrite an existing one. |
| `loop-run` | **Repeated rounds** until a stop condition fires. The usual entry point. |
| `loop-round` | Exactly one round. |
| `loop-audit` | Ships nothing. Measures whether the project's strongest claim still holds. |
| `loop-feedback` | Files a proposal upstream about the protocol itself. |

All five carry `when_to_use` triggers, so an agent picks them up from intent — no
one has to type a slash command.

**Domain plugins are separate and optional.** `loop-ux-roast@agentic-coding-loop`
layers UX-roast-specific mechanics (blind critic / context-aware verifier split,
maker+checker worktree fixes, coverage-map-by-surface) on top of the same five
core skills — install it only if the target project fits. See the Domains table
in [`llms.txt`](llms.txt) or [`domains/`](domains/).

Other harnesses, and the copy-the-templates path: [`docs/ADOPTING.md`](docs/ADOPTING.md).

## The shape of a round

Read state → pick one item → **ask what would prove it wrong** → build the check
first → build the thing → verify → write state → decide whether to continue.

The third step is what separates this from a task list. An agent asked to "improve
the dataset" will improve the dataset and report success. An agent asked to
*measure whether the dataset's central claim holds* may come back with the claim
refuted — which is the outcome worth having.

## Running it repeatedly

A round is the unit, not the job. `LOOP.md` §D governs the sequence:

- **The round boundary is a commit.** Never start the next round's changes before
  the previous round's commit exists.
- **Re-read the state file every round** and treat memory of earlier rounds as
  stale. This is also the loop's own correctness check: if round N+1 cannot proceed
  from the file alone, round N wrote it badly, and that is a finding.
- **Explicit stop conditions.** Red gate, an empty queue, two consecutive blocked
  rounds, a round with no commit, the same item attempted twice, or any round that
  would require weakening an invariant. Stop and report which fired — never push
  through, never invent work to keep the sequence alive.
- **Unattended runs are constrained.** Branch and pull request only, never the
  default branch, never force-push, never spend money without recorded approval,
  budget of one round per firing.

Scheduled runs: [`templates/loop-workflow.template.yml`](templates/loop-workflow.template.yml)
produces one reviewable pull request per firing.

## Does it work?

One data point, reported honestly. Four rounds on
[TactBench](docs/CASE_STUDY.md), a benchmark whose README claimed its matched-pair
design defeated keyword matching.

Round 1's assignment was not "add features." It was "build a probe that would
detect the failure this project claims to be immune to." The probe scored
**93.5% against a 50% floor**. The claim was false, and had been false since the
first commit — the headline numbers were measuring leakage, not skill.

That round rebuilt the generator around role permutation (93.5% → 57.5%),
collapsed the reference heuristic from 0.818 precision to chance where it
belonged, and caught a set of inverted labels on the way. Round 3 added three
scenario families; the same probe flagged one at 82.5% **before it landed**, from a
one-token asymmetry no reviewer would have seen by eye.

A round that deletes a false claim is a good round. The loop is built to make that
outcome reachable rather than embarrassing.

## The parts that matter most

**NEEDS-MAX.** Items that cannot proceed without a human — a credential, a budget
approval, a decision that isn't yours. Recorded with the exact command that
unblocks them, then skipped. Never a reason to halt the loop, and never a reason to
fake the result. TactBench's LLM harness has been built, tested, and cached for
three rounds without ever being run, because no API key exists. Zero numbers about
it appear anywhere in that repo.

**Standing invariants.** Properties encoded as tests, with a written prohibition on
weakening them. When one fails, the code is wrong, not the assertion. This is the
highest-value rule in the system, because relaxing an assertion is always the
locally cheapest way to make a round pass.

**Noted, not built.** Ideas examined and deliberately rejected, with the reasoning.
Without it, every round rediscovers the same dead end.

## Feedback, and why it goes through review

Projects running the loop learn things about the loop. `loop-feedback` packages one
as a proposal and files it as an issue here. It does not take effect:

```
loop-feedback → issue → proposals/*.md → maintainer writes the change
                        (inert)          → PR + review → version bump
                                                          ↑ goes live here
```

**`proposals/` is inert, and that is a security boundary rather than a filing
convention.** Downstream agents write proposals; upstream agents read this repo. If
proposals were read as instructions, any project running the loop could change how
the loop behaves in *every other project running it*, unreviewed. So nothing here
loads or executes anything from `proposals/`, and the only path from a suggestion
to a behavior change runs through a human writing that change by hand.

**A merge alone changes nothing downstream.** The plugin carries an explicit
`version`; consumers keep what they have until it is bumped and released.

Full flow: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT. Use it, fork it, strip the parts you disagree with.
