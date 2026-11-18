# The agentic coding loop

One person running a fleet of Claude Code agents to build and ship a real product:
an Android app and the plugin for the agent server it talks to. One coordinating
agent session plans and merges; up to five helper agents build in parallel, each in
its own worktree; hooks and scripts enforce the hard rules, so they hold even when
an agent forgets them.

This repository is the process behind that work, written down so it can be reused:
the protocol ([`LOOP.md`](LOOP.md)), the field notes it came from
([`docs/PARALLEL_LANES.md`](docs/PARALLEL_LANES.md)), and example hooks
([`examples/hooks/`](examples/hooks)). The product's code is private; everything
here is the part that generalizes.

## Outcomes and scale

From the project's history, late September to mid November 2026 (about eight weeks):

| | |
|---|---|
| Pull requests merged | about 1,900; up to about 90 on a busy day |
| Agents at once | 1 coordinator + 2 to 5 helper lanes, including at most one bug lane and one process lane |
| Device tests | over 300 end-to-end scenarios on an emulator and real test phones |
| Unit tests | about 5,000 JVM tests, plus about 1,600 tests for the tooling itself |
| Enforcement | 16 Claude Code hooks; a merge queue that is the only way onto main |
| Releases | a dogfood build of main about hourly after fast checks; the full suite every night |
| Hardware | one 16 GB laptop, one build slot, a small device pool |

The numbers come from the project's own logs. One project and one author: read them
as a well-kept anecdote, not a benchmark.

## How work flows

```mermaid
flowchart LR
    F[Feedback and<br/>ranked list] --> P[Coordinator plans<br/>one slice per PR]
    P --> L1[Lane 1]
    P --> L2[Lane 2]
    P --> L3[Lane ...]
    L1 & L2 & L3 --> PL[Prelanding:<br/>cheap checks on<br/>branch + main]
    PL --> R[Independent review<br/>by a fresh agent]
    R --> Q[Land queue:<br/>merge main, check,<br/>batch, merge, deploy]
    Q --> D[Hourly dogfood build]
    Q --> N[Nightly full suite<br/>+ regression gate]
    N -. reds become fixes .-> F
    W[Watchdog outside<br/>the session] -. flags .-> P
```

- **Feedback** comes from the owner, from an in-app feedback loop, and from nightly
  reds. The owner keeps one ranked list; the coordinator takes its top ready row.
- **Lanes** each get one slice, one branch, one worktree, and a prompt that points at
  a single rules file. One lane per hotspot (a screen, the wire protocol), so lanes
  don't fight over the same lines.
- **Prelanding** runs the landing's own non-device checks on the branch merged with
  current main. The queue refuses a head with no recorded pass.
- **Independent review** is a fresh, read-only agent that never saw the author's
  session. For UI it compares every built state with the approved design.
- **The land queue** is the only merge path. It batches compatible PRs, bisects a red
  batch, and deploys main.
- **After merge**: short device checks in the background, a phone build about
  hourly, the whole suite at night. A bad build is fixed by shipping a newer one.

## Key ideas

### The human decides only what can't be undone

The owner's attention is the scarcest resource. Agents decide everything reversible
themselves: take the best recommendation, act on it, and log it in a short
"decided, not asked" list with how to reverse it. The owner reviews that list when
convenient; a reversal is ordinary work.

What still waits for the owner is a short written list: anything irreversible,
anything that spends money or acts in their name, loosening a safety gate, and the
priority order.

**Why:** one night the coordinator held every lane idle, waiting for a go-ahead on
calls it could have reversed in minutes. Nothing was gained by waiting.

### Hooks are the guardrails

Rules in a prompt are advice. Every rule that must hold with zero exceptions is a
pre-tool hook:

- no edits or git writes in the checkout the live service runs from;
- no device command outside the device lock;
- no agent spawn past the lane cap, onto a held hotspot, or without the rules pointer;
- no test message to any chat channel but the testing ones;
- no merge outside the queue, no stacked PRs, no bare `git stash`, no pattern kills.

Hooks guarding something irreversible fail closed on their own errors. A blocked call
says what to do instead, and a wrong block is fixed in the hook by PR, never worked
around.

**Why:** the coordinator once had about 18 agents running against a written limit of
five. The machine's load hit 51 and the service under test starved. The limit was in
its own notes; a hook ended it.

### Verification is independent and reads real sources

The author of a change never signs off on it. A fresh reviewer gets only the real
build output: for UI, a sheet with every state of every approved design beside the
screenshot of that state, in every theme. The gate refuses a PR whose reviewer is the
author, or whose screenshots changed after the review. No agent may stub, wrap or
feed a gate its own inputs.

**Why:** a release reached the owner's phone unlike its approved designs, with every
test green. On its first night the independent reviewer found real defects in nine
PRs that every test had passed.

### Resources are admitted, not cleaned up after

On one machine the limit is the slowest shared thing: memory, disk, the build slot,
the devices, the merge queue. Lanes are added by the queue's length, not by appetite,
and a new lane is refused below a disk floor or above a swap ceiling. One build at a
time. Cleanup still runs, as the backstop.

**Why:** in one day the disk hit zero (three landings died), swap filled, about 90
orphaned wait loops were found, some over a week old, and the laptop rebooted out of
memory. Each of those had a cleanup job; none had a gate.

### Every repeated failure becomes a mechanism

A daily blameless retro is compiled from local state. A slip seen twice in two weeks
becomes a hook, a queue refusal or a watchdog flag; a note in an agent's memory
doesn't count. Some of the stories behind the rules:

| what happened | what changed |
|---|---|
| The nightly skipped its device stage five nights running and read as green. | A stage that ran nothing is "not run", never green or red; a missing stage is an alarm. |
| An unattended job's login expired; every run failed for a week and nobody saw. | The watchdog reads each job's own output; a failure only the human can fix reaches them at once, with the one command to run. |
| Wait loops matched their own command line and never ended. | A hook refuses the self-matching form; a reaper kills old ones. |
| A bad "merge main" silently reverted another PR's work. | The queue refuses a PR missing lines main added to a file it also changes. |
| About 2 of 15 fixes written for nightly reds were real bugs. | One targeted retry before a red counts; quarantine with an owner after two. |
| The watchdog was installed with a trigger that fired once. | It stamps every run; a stale stamp is itself an alarm. |

More, with numbers: [`docs/PARALLEL_LANES.md`](docs/PARALLEL_LANES.md).

## The protocol, as a plugin

The general part is packaged as a Claude Code plugin. It covers one agent improving a
codebase across weeks of memoryless sessions, and scales to parallel lanes.

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
| `loop-lanes` | Opt-in: coordinate several agents running rounds in parallel. |

Any agent, any harness: [`LOOP.md`](LOOP.md) is self-contained, one fetch. On a
benchmark project, the loop's first round tested a robustness claim the README had
made since its first commit and never measured; the claim was false
([`docs/CASE_STUDY.md`](docs/CASE_STUDY.md)). Changes to the protocol go through
reject-by-default review ([`CONTRIBUTING.md`](CONTRIBUTING.md)).

## Where to look

| | |
|---|---|
| [`LOOP.md`](LOOP.md) | The protocol: round steps, hard rules, §F parallel lanes and goal loops. |
| [`docs/PARALLEL_LANES.md`](docs/PARALLEL_LANES.md) | Field notes from the multi-agent project: each rule with the incident behind it. |
| [`docs/PRINCIPLES.md`](docs/PRINCIPLES.md) | Why each rule exists and the failure it prevents. |
| [`examples/hooks/`](examples/hooks) | Generic lane-cap and admission hook, wait-loop guard, outside watchdog. |
| [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md) | Every round of the single-agent loop on a benchmark, including what it cost. |
| [`CHANGELOG.md`](CHANGELOG.md) | What changed in the process, release by release, and why. |

## How this maps to a team

The roles are familiar ones; agents just make the costs show up faster.

- **The coordinator is a tech lead and release manager**: picks work from a ranked
  list, sizes the team to what can be merged, reviews, and is the one voice to the
  stakeholder.
- **Lanes are engineers on disjoint areas.** Hotspots are code ownership; "finish
  before starting" is a WIP limit.
- **Prelanding and the land queue are CI and a merge queue**, shifted left so most
  failures happen before a PR waits in line.
- **Independent review is code review and design QA** by someone who didn't write the
  change, against the spec rather than the author's explanation.
- **"Decided, not asked" is a decision log**: unblock yourself, make the call visible,
  keep it reversible.
- **Retros that end in a mechanism are blameless postmortems** whose action items
  actually close.

The main lesson carries over directly: writing code got cheap; landing it safely
didn't. Most of this process exists to keep the path onto main fast and honest.

<details>
<summary><b>What's not verified</b></summary>

- **One author.** The app project, the benchmark and an earlier production app all
  trace back to the same person. No independent team has run this process.
- **The multi-agent rules are one project's lessons.** §F was accepted from that
  project's logs directly, not through the proposal review, and no other project has
  run it as released.
- **Goal loops are new.** The first one started in November 2026 and was parked within
  hours when the machine ran out of memory; there is no result yet.
- **The scheduled proposal reviewer is unproven**, and the GitHub Actions fallback is
  untested.
- **Cost figures mix several changes made at once**, so no single rule can claim them.

</details>

## License

MIT. Use it, fork it, strip the parts you disagree with.
