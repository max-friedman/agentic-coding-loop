# The agentic coding loop

**A protocol that lets a coding agent improve a codebase over weeks, across
sessions that start with no memory of the last one — plus a governance layer so
the protocol itself can't be quietly weakened.**

It's running on real projects. It has already deleted one of its own false claims
and rejected part of its own proposed changes.

## The problem it solves

Long-running agent work fails quietly: session four re-derives what session two
already established, and relaxes an assertion that was inconvenient. Nothing
looks broken — the tests are green — but the work has stopped compounding. The
fix is a **written spine**: one state file the agent reads before acting and
writes before stopping, holding the queue and the invariants that may never be
weakened.

## Does it work?

Yes — and the clearest evidence is a claim it deleted, not a feature it shipped.
Run against [TactBench](https://github.com/max-friedman/tactbench), whose README
claimed immunity to a specific failure mode, unmeasured: round 1's job was to
build a probe for exactly that failure, and it scored **93.5% against a 50%
floor**. The claim had been false since the first commit — caught by the
process, not avoided by it. Full account, round by round:
[`docs/CASE_STUDY.md`](docs/CASE_STUDY.md).

## Using it

```
/plugin marketplace add max-friedman/agentic-coding-loop
/plugin install loop@agentic-coding-loop
```

| skill | what it does |
|---|---|
| `loop-init` | Bootstrap the state file from the real project. |
| `loop-run` | Repeated rounds until a stop condition fires. |
| `loop-round` | Exactly one round. |
| `loop-audit` | Measure whether the project's strongest claim still holds. |
| `loop-roast` | Opt-in: critique the product as a first-time user. |
| `loop-feedback` | File a proposal upstream about the protocol. |

Any agent, any harness: [`LOOP.md`](LOOP.md) is self-contained, one fetch.
Optional project-shaped add-ons ("domains," e.g. `ux-roast`) layer on top — see
`llms.txt`. Details: [`docs/ADOPTING.md`](docs/ADOPTING.md).

## How the protocol improves itself

A project's finding goes upstream as an **issue** (evidence, never a pull
request), gets judged reject-by-default, and only reaches every other project on
a deliberate version bump. Full mechanism and why each safeguard exists:
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Learn more

| | |
|---|---|
| [`LOOP.md`](LOOP.md) | The protocol itself — round steps, hard rules, roast round. |
| [`docs/PRINCIPLES.md`](docs/PRINCIPLES.md) | Why each rule exists and the failure it prevents. |
| [`docs/REVIEW_RUBRIC.md`](docs/REVIEW_RUBRIC.md) | The standard a proposal must clear. Reject by default. |
| [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md) | Every round, in full, including what it cost. |
| [`domains/`](domains) | Optional, project-shaped rule sets on top of the core protocol. |

<details>
<summary><b>Design decisions worth defending, and what's not yet verified</b></summary>

Each decision below was chosen against a plausible alternative, for a reason
that's in the repo rather than in someone's head:

| decision | the alternative, and why it lost |
|---|---|
| **Stop conditions are explicit and non-overridable** | "Use judgment" — but an unattended sequence with judgment pushes through a red gate and produces a PR nobody can review. |
| **Invariants may never be relaxed to make a round pass** | Case-by-case exceptions — but relaxing an assertion is always the locally cheapest fix, and invisible in a diff that also has real work. |
| **Blocked work is recorded, never estimated** | Publishing a plausible number — but a fabricated measurement has no natural discovery path. One project's test harness has sat built, tested, and unrun for three rounds for lack of an API key, with zero numbers published about it. |
| **Rules fire where skipping them forecloses the option** | Stating rules where they read most naturally — but four rounds ignored a correct rule sitting at step 7, past the point it could still be acted on. |
| **The reject-by-default rubric is a conjunction, not a score** | Weighted scoring — but that lets a strong evidence section buy a weak blast-radius argument, the exact trade the rubric exists to forbid. |

This repo's credibility rests on the next part being accurate rather than short:

- **The scheduled reviewer is unproven.** It has never completed a real review;
  its first smoke test was inconclusive.
- **The GitHub Actions fallback is untested.** It needs an API key and a live
  proposal to exercise.
- **Three proposals reviewed, three merged** — a poor ratio for reject-by-default.
  Two came from a closely related project on a template written here; the third
  came from an unrelated downstream project's own history — better evidence, but
  still three data points, not a pattern.
- **One project, seven rounds.** Every claim above generalizes from a single
  codebase.

</details>

## License

MIT. Use it, fork it, strip the parts you disagree with.
