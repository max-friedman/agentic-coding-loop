# LOOP.md — the improvement loop protocol

Canonical and self-contained. Everything needed to run the loop is in this file;
no other file needs to be fetched. Other docs in this repo are optional evidence
and rationale.

**Audience: coding agents.** Written to be executed, not read for pleasure.

**You are running one round** of a continuous-improvement loop on a repository.
State lives in `docs/plans/LOOP_STATE.md`. You have no memory of previous rounds.
That file is the memory. Read it first, write it last.

---

## 0. Preconditions

1. Read `docs/plans/LOOP_STATE.md` in full, including the bottom sections. The
   standing invariants are at the bottom and are the most important part. If
   Current status declares a `**Layers:**` beyond core, fetch that domain's
   `DOMAIN.md` too (see §B step 2) and apply it for the rest of this round — the
   declaration was made once at bootstrap precisely so later rounds don't have to
   re-derive it.
2. Read the project rules (`CLAUDE.md` or `AGENTS.md`) if present.
3. If `docs/plans/LOOP_STATE.md` does not exist, run **§B Bootstrap** instead of a
   round, then stop.
4. If the working tree is dirty, STOP. Report it. A round must start from a clean
   tree or its diff cannot be attributed.

The loop runs **repeatedly**. One round is the unit; §D governs the sequence.

---

## 1. Pick exactly one item

Take the top queue item, unless the last round's finding makes another clearly more
urgent — then take that and record why.

MUST be exactly one. Three half-landed changes leave the next round unable to
attribute a regression to any of them.

Then **cut the round's branch, before the first edit** — `git checkout -b
<type>/<slug>`. Stated here, not next to the ship instruction in §6, because here
is the last moment it can still be acted on — a rule that only fires at ship time
is unfollowable once the work is already sitting on the default branch.

## 2. State what would prove it wrong

Write the question the round answers before building anything.

- Task (wrong): "add three more scenario families."
- Round (right): "six families is six degrees of freedom regardless of item count —
  does adding three change what the probe sees?"

If no outcome would count as bad news, you picked a task. Reframe until a negative
result is possible.

## 3. Build the check first, run it on current code

The measurement lands before the change and produces a **before** number from the
existing code.

- A check written afterward is shaped to accept what was just built.
- Without a before number, "it improved" is unfalsifiable.

If the round adds a component (a module, a dataset family, a scenario), it MUST be
added to the existing checks. Never exempt new work from a check to make it pass.

## 4. Build it

Keep the repo shippable at every commit. A round that ends mid-refactor produced
nothing — the next session starts cold and cannot distinguish a deliberate
half-state from a broken one.

**Mechanical churn gets its own commit.** Formatting sweeps, renames, and
regenerated files go in a commit separate from the logic change, verified
behavior-free by running the gate before and after and confirming identical
results. Mixed into a logic change, churn makes the diff unreviewable and poisons
`git blame` for every line it touches.

## 5. Verify wider than you changed

1. Run the project's gate command (tests + lint). Both green. No exceptions.
2. Inspect real output — failures, samples, rendered results. A metric can look
   reasonable while the thing underneath is visibly wrong.
3. Re-run measurements from **earlier** rounds that this change could have moved.
   Silent regressions live here.
4. Update every document quoting a number you changed.

## 6. Write `docs/plans/LOOP_STATE.md` last

This is the deliverable, not a summary of it. Write for a stranger with no context.

Append:

```markdown
## Round N — <short title naming the question, not the task>

**Question:** what was actually uncertain.
**Method:** how it was measured, and what a negative result would have looked like.
**Finding:** what happened, including when it contradicts a claim this project makes.
**Shipped:** files, tests, docs.
**Consequences:** knock-on effects, verified — not predicted.
**Noted, not built:** ideas examined and rejected, with reasoning.
```

Then update, in place:

| section | contains |
|---|---|
| `## Current status` | round number, gate command + state, artifact + version, one-sentence headline |
| `## Coverage map` | table: area \| last touched \| probe/status. Write "unprobed" where true. |
| `## NEEDS-MAX` | blocked-on-human items, each with the exact unblocking command |
| `## Queue — next rounds` | ordered next increments, each phrased as a question |
| `## Standing invariants` | properties + the test enforcing each |

Never edit a previous round's section to make the history look tidier.

Commit with a message naming the round's **finding**, not its task. Then merge
the round's branch to the default branch on local green (supervised sessions may
merge directly; unattended runs follow §D and always open a pull request instead).

## 7. Decide whether to continue

Evaluate the stop conditions in **§D**. If none fire, start the next round at §0 —
re-reading the state file, not relying on what you remember. If one fires, stop and
report which.

---

## Hard rules

| rule | why |
|---|---|
| **A failing invariant means the code is wrong, not the assertion.** Never relax an assertion to make a round pass. If an invariant is genuinely mis-stated, say so in the writeup and leave it failing. | Relaxing is always the locally cheapest fix and is invisible in a diff containing real work. |
| **A false claim found is the round.** Report it, fix what you can, correct the docs. | Deleting a false claim beats adding a feature. |
| **Blocked is not stopped.** Needs a human? Add to NEEDS-MAX with the exact unblocking command, then build around the block. | Halting burns the round. |
| **Never publish a number you did not measure.** No estimating a blocked result, however obvious. | A guessed number is worse than a missing one. |
| **Never edit past round sections.** | The wrong turn is the only reason the next agent won't take it. |
| **Record rejected ideas** in *Noted, not built*, with reasoning. | Otherwise the same dead end is rediscovered every few rounds. |
| **A failing test can indict the test, not just the code.** Decide deliberately which is wrong and say so in the commit — a test asserting behavior since deliberately changed is obsolete, not sacred. This is distinct from the invariant rule above: an invariant is a *property* that must hold; a test can simply go stale. | Reflexively "fixing" a red test in either direction without deciding which is true hides the answer instead of finding it. |
| **Docs drift silently.** When a round changes a contract, metric, or default, grep the repo for the *concept* — not just the filenames you remember — and update every hit, including a previous round's doc edit. | More than one doc usually states the same fact. Recall finds some of them; grep finds all of them. |

## Gate mechanics

| rule | why |
|---|---|
| **The merge must be unreachable on a red gate.** Never chain the gate command and the merge command in one sequential script block that continues past a failure — check the gate's exit status explicitly, then merge as a separate step. | A red gate scrolls past in a long log and the merge still runs anyway; the failure is invisible until someone reads the log after the fact, by which point it already shipped. |
| **A red gate on code the round didn't touch is a flake suspect, not a verdict.** Rerun the failing check 3× plus one clean full-suite run before deciding to ship or revert. If it is a flake, queue the deflake as its own item — don't wave it off. | A real regression and an infrastructure flake look identical from a single red run; only repetition tells them apart, and an ignored flake becomes a false "green" the next round trusts. |

## Ending states

End in exactly one, and name which in the writeup.

| state | meaning |
|---|---|
| `shipped` | Item landed, gate green, docs match the numbers. |
| `refuted` | The measurement killed the plan. Finding recorded, queue re-ranked. **Highest value.** |
| `blocked` | Needs a human. Moved to NEEDS-MAX, round redirected to something buildable. |
| `rejected` | Built enough to evaluate, deliberately not kept, reasoning recorded. |

There is no "partially done". If the item is bigger than a round, that finding is
the output: split it in the queue and stop.

## Anti-patterns

| pattern | signal | action |
|---|---|---|
| Green streak | Several rounds where everything passes and ships | Checks stopped being adversarial. Run §A Audit. |
| Assertion nudge | A test fails and the smallest fix is in the test | Fix the code. |
| Unmeasured claim | Publishing a number the round did not produce | Do not. Leave it blocked. |
| Tidy history | Editing an old round to read better | Leave it. |
| Context bet | Relying on remembering rather than writing it down | Write it down. |
| Scope drift | Docs describe the work more generously than it is | Shipping a capability removes a limitation; finding a weakness adds one. |

---

## §A Audit round

Ship no features. The deliverable is a measurement. Run when the project has been
green for several rounds, or on request.

1. Find the strongest claim the project makes about itself. Prefer, in order: a
   claim central to its value; a claim never measured; a claim whose supporting
   test would still pass if the claim became false.
2. State the claim verbatim and the number that would falsify it. Both before
   measuring.
3. Build a probe independent of the code under test. It must not import the
   machinery it checks, and must not be able to see the answer. Where the project's
   tests and the probe disagree, trust the probe — the tests were written by
   whoever wrote the claim.
4. Run it. Report the number, especially if bad.
5. **Do not fix it in this round.** The fix is a separate round with its own
   before/after. Fixing inside the audit destroys the before number.
6. If it fails: correct the claim in the doc that makes it, immediately, weakening
   the wording to what the evidence supports. Queue the fix at the top.
   If it holds: wire the probe into the gate and add the threshold to the standing
   invariants.

Verdict is one of: `holds`, `fails`, `unmeasurable as stated`.

---

## §B Bootstrap (no state file yet)

1. If `docs/plans/LOOP_STATE.md` exists, STOP. Never overwrite it.
2. Check for a domain fit before reading further. Fetch the Domains table in
   `llms.txt` (`https://raw.githubusercontent.com/max-friedman/agentic-coding-loop/main/llms.txt`)
   and compare its descriptions against the target project. A clear match → fetch
   that domain's `DOMAIN.md` too and layer it in for the rest of bootstrap and every
   round after. No clear match, or it's a stretch → proceed core-only. Record the
   choice as a `**Layers:**` line in the state file's Current status — never guess
   silently and never force a fit.
3. Read enough to fill it honestly: README and purpose docs; the exact gate command
   (from `package.json`, `pyproject.toml`, `Makefile`, CI config); tests asserting
   *properties* rather than behavior (candidate invariants); TODO/FIXME clusters and
   known-weakness sections (candidate queue items).
4. Write `docs/plans/LOOP_STATE.md` with every section from step 6 above. Round 0.
   Headline is often "unmeasured" — say so.
5. Add to the project rules file, at the very top:

   ```markdown
   **Working the improvement loop? Read [`docs/plans/LOOP_STATE.md`](docs/plans/LOOP_STATE.md)
   first and write it last.** It holds the queue, the coverage map, the NEEDS-MAX list,
   and the standing invariants. Context is lost between rounds; that file is not.
   ```

6. Write only rules you can justify from code you read. An invented rule is worse
   than no rule — it gets cited later as if load-bearing.
7. Report the drafted queue and invariants, which domain (if any) was matched, and
   say which sections you guessed at.

---

## §C Feedback on the loop itself

If a round surfaced a problem with **this protocol** — not with the project it ran
on — file it upstream at `max-friedman/agentic-coding-loop` using the *Loop
proposal* issue form.

- MUST NOT edit this protocol locally to compensate. A local fork is invisible to
  every other project running the loop and is overwritten on update.
- MUST NOT open a pull request. Proposals enter as issues.
- MUST redact repository names, paths, code, credentials, and business specifics.
  The upstream repo is public.
- Search existing issues first; add to an existing proposal rather than duplicating.
- If a human is present, show the full text and get approval before filing.

Required content: what happened (which step), what it cost, how often, the narrowest
change that would have prevented it, blast radius on projects that never had the
problem, and the strongest argument against your own proposal.

Nothing filed takes effect until a maintainer reviews it, writes the change, and
releases a version bump.

---

## §D Continuous operation

The loop repeats. A single round is the unit of work, not the whole job.

### The round boundary

A round ends when the state file is written and the work is committed. That commit
is the boundary. Never begin the next round's changes before the previous round's
commit exists — an uncommitted round cannot be attributed, reverted, or trusted.

### Context hygiene between rounds

At the start of every round, **re-read `docs/plans/LOOP_STATE.md` from disk** and
treat your memory of earlier rounds as stale. Do not carry conclusions forward from
context; carry them forward through the file.

This is not ceremony. It is the loop's own correctness check: if round N+1 cannot
proceed from the file alone, round N wrote it badly, and that is a finding worth
recording. Every round is a test of the previous round's handoff.

When the harness compacts or resets context mid-sequence, nothing is lost. That is
the design working, not an interruption.

### Stop conditions — MUST

Stop the sequence and report which condition fired. Do not push through.

| condition | why |
|---|---|
| Gate is red and not fixable inside the round | Continuing builds on a broken base. |
| A round would require weakening a standing invariant | Never. Stop and report, even if the queue is full. |
| Queue is empty and the round generated no new items | There is nothing to do. Say so rather than inventing work. |
| Two consecutive rounds ended `blocked` | Everything left needs a human. |
| A round produced no commit | The sequence is spinning. |
| The same item has been attempted twice without shipping | It is mis-scoped. Split it in the queue and stop. |
| Round budget for the session is reached | Default 3. Raise deliberately, not by drift. |
| The working tree is dirty at a round boundary | Someone else is editing, or the previous round did not finish. |

### Unattended runs

When no human is watching — a scheduler, a cron trigger, CI — the additional rules
are absolute:

- **Never commit to the default branch.** Work on `loop/round-N` and open a pull
  request. A human merges.
- **Never force-push.** Never rewrite published history.
- **Never file, comment, or post outside the repository** except the §C proposal
  path.
- **Never spend money** — paid API calls, provisioning, anything metered — without
  an explicit prior approval recorded in the state file. Otherwise it is a NEEDS-MAX
  item.
- **Stop at the first stop condition.** An unattended sequence that pushes through
  a red gate produces a pull request nobody can review.
- Reduce the round budget to **1** unless configured otherwise. One reviewable pull
  request per firing beats a batch nobody reads.

**Optional stricter tier — declared auto-merge.** A project MAY declare, at the
top of its `LOOP_STATE.md`, an explicit opt-in to auto-merge `--admin` to the
default branch unattended — but only for a change that is mechanical *and*
clearly-correct, has passed maker/checker review, and passed the full local gate.
Anything that changed behavior in a judgment-y way, needed verification the run
couldn't do, or that a reviewer flagged still opens a PR under the default rule
above; anything subjective, credentialed, or destructive routes to NEEDS-MAX
regardless of this tier. Undeclared, the default rule (always PR) applies — this
tier is never silently assumed.

### Scheduling

The loop is stateless between firings — everything needed is in the state file — so
any scheduler works. Pick one:

| mechanism | fit |
|---|---|
| Claude Code `/loop` bundled skill | Interval runs inside a session. Good for supervised sequences. |
| Claude Code scheduled tasks | Recurring unattended runs on a repository. |
| GitHub Actions on a `schedule` trigger | Fully unattended, produces a pull request per round. Template: [`templates/loop-workflow.template.yml`](templates/loop-workflow.template.yml). |
| Manual re-invocation | The `loop-run` skill, or re-running the round prompt. |

Cadence should track how fast the project's ground truth changes. A benchmark whose
dataset moves weekly does not need hourly rounds; each firing costs a session and
produces a diff someone must read. Prefer fewer, larger-signal rounds.

### Reporting a sequence

At the end of a sequence, report: rounds completed, the ending state of each
(`shipped` / `refuted` / `blocked` / `rejected`), the stop condition that fired, and
anything added to NEEDS-MAX. One line per round. The state file holds the detail —
do not restate it.
