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
   `## Current status` declares a `**Layers:**` beyond core, fetch that domain's
   `DOMAIN.md` (see §B step 2) and apply it for the rest of this round — the
   declaration was made once at bootstrap precisely so later rounds don't re-derive
   it.
2. Read the project rules (`CLAUDE.md` or `AGENTS.md`) if present.
3. If `docs/plans/LOOP_STATE.md` does not exist, run **§B Bootstrap** instead of a
   round, then stop.
4. If the working tree is dirty, STOP. Report it. A round must start from a clean
   tree or its diff cannot be attributed.
4a. Review and merge the previous round's pull request first — see §D *Reviewing
   the previous round*. You are the independent check on work you did not write;
   there is no other one.
5. Confirm the gate runs somewhere other than this machine. A gate only ever run
   where it was written is an unverifiable claim, not a check. If the project has
   no CI, adding it is a legitimate round. If CI genuinely cannot run here, record
   *why* in the state file rather than letting "the gate is green" quietly mean
   "green once, locally."
6. Check for a newer protocol release and take it before starting. Plugin users:
   `/plugin marketplace update agentic-coding-loop && /plugin update loop`. Others:
   compare against the upstream `CHANGELOG.md`. Skip and proceed if the check fails
   — a release you cannot reach is not a reason to skip the round.

The loop runs **repeatedly**. One round is the unit; §D governs the sequence.

---

## 1. Pick exactly one item

**Cut the round's branch before the first edit:** `git checkout -b loop/round-N`.
Do this now, not at the end. Shipping via pull request is unfollowable once the
work is already committed to the default branch — there is nothing left to open a
PR from, and the recovery is history surgery §D forbids.

Take the top queue item, unless the last round's finding makes another clearly more
urgent — then take that and record why.

MUST be exactly one. Three half-landed changes leave the next round unable to
attribute a regression to any of them.

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
regenerated files go in a separate commit that is explicitly behavior-free —
demonstrated by identical gate output before and after. Mixed into a logic change
they make the diff unreviewable, and they poison `git blame` for every line they
touch: the next agent tracing why a line exists lands on a whitespace pass instead
of the reasoning.

## 5. Verify wider than you changed

1. Run the project's gate command (tests + lint). Both green. No exceptions.
2. Inspect real output — failures, samples, rendered results. A metric can look
   reasonable while the thing underneath is visibly wrong.
3. Re-run measurements from **earlier** rounds that this change could have moved.
   Silent regressions live here.
4. Update every document quoting a number you changed. Find them by **searching the
   repo for the concept, not by recalling which files mention it** — more than one
   doc usually states the same contract, and the one you forget will be the
   canonical reference. Re-check the *previous* round's doc edits too, not only
   your own.

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
**Loop:** friction in the protocol itself this round, or `nothing`.
```

The **Loop** line is required and `nothing` is a valid, common answer. It exists so
that protocol friction is recorded while it is still concrete, rather than
reconstructed from memory five rounds later. §C turns accumulated lines into
proposals.

Then update, in place:

| section | contains |
|---|---|
| `## Current status` | round number, gate command + state, artifact + version, one-sentence headline |
| `## Coverage map` | table: area \| last touched \| probe/status. Write "unprobed" where true. |
| `## NEEDS-MAX` | blocked-on-human items, each with the exact unblocking command |
| `## Queue — next rounds` | ordered next increments, each phrased as a question |
| `## Standing invariants` | properties + the test enforcing each |
| `## Loop configuration` | human-set settings, read at §0. **Never written by a round.** See §E. |

Never edit a previous round's section to make the history look tidier.

Commit with a message naming the round's **finding**, not its task.

## 7. Decide whether to continue

Evaluate the stop conditions in **§D**. If none fire, start the next round at §0 —
re-reading the state file, not relying on what you remember. If one fires, stop and
report which.

The one exception is an empty queue when `roast-on-empty` is enabled: run **§E**
instead of stopping. Every other stop condition still halts the sequence.

---

## Hard rules

| rule | why |
|---|---|
| **A failing invariant means the code is wrong, not the assertion.** Never relax an assertion to make a round pass. If an invariant is genuinely mis-stated, say so in the writeup and leave it failing. | Relaxing is always the locally cheapest fix and is invisible in a diff containing real work. |
| **A false claim found is the round.** Report it, fix what you can, correct the docs. | Deleting a false claim beats adding a feature. |
| **Blocked is not stopped.** Needs a human? Add to NEEDS-MAX with the exact unblocking command, then build around the block. | Halting burns the round. |
| **Never publish a number you did not measure.** No estimating a blocked result, however obvious. | A guessed number is worse than a missing one. |
| **A gate that has never failed is not yet known to be a gate.** | Until it fails once, "green" is untested tooling, not evidence. A red first CI run is the system working. |
| **Never edit past round sections.** | The wrong turn is the only reason the next agent won't take it. |
| **Record rejected ideas** in *Noted, not built*, with reasoning. | Otherwise the same dead end is rediscovered every few rounds. |

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
   choice as a `**Layers:**` line in `## Current status` — never guess silently and
   never force a fit. A domain is additive to the steps above; it never replaces one.
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

## §C Auditing the loop, and proposing changes

Auditing the protocol is part of running it, not a favour to its maintainer. A
project running the loop is the only thing that ever observes the loop under load.

### Cadence

Run a loop audit when **any** of these is true:

- Every **fifth** round.
- A round hit a §D stop condition.
- A round's **Loop:** line was non-`nothing` twice in a row — the same friction
  recurring is the signal that distinguishes a pattern from an incident.

The audit costs a few minutes inside an ordinary round. It is not its own round.

### What to examine

Read the **Loop:** lines from every round since the last audit, then check:

| question | what a bad answer looks like |
|---|---|
| Which step consumed effort disproportionate to what it produced? | A step that is always performed and never changes an outcome. |
| Which step was skipped, and was that skipping *possible* or *tempting*? | A rule placed where it can no longer be acted on. Rules must fire while the option they govern still exists. |
| Which section of the state file is never read on the next round? | A section written every round and used by none. |
| Did any round end in a state §D does not name? | A missing ending state, or one being forced into the wrong bucket. |
| Did a stop condition fire late, or fail to fire when it should have? | Continuing past a condition, or halting on something not listed. |
| Was any instruction ambiguous enough that two rounds read it differently? | Divergent behavior on identical input. |

Record the answers on the **Loop:** line. Most audits find nothing, and finding
nothing is a result — record it as one rather than manufacturing a proposal.

### Filing

Only file when there is a **pattern with a cost**. A single awkward round is not a
proposal.

File an issue at `max-friedman/agentic-coding-loop` using the *Loop proposal* form.

- MUST NOT edit this protocol locally to compensate. A local fork is invisible to
  every other project running the loop and is overwritten on the next update.
- MUST NOT open a pull request. Proposals are issues; the reviewer writes the
  change itself, in the protocol's voice. Your text is evidence, not copy.
- MUST redact repository names, paths, code, credentials, and business specifics.
  The upstream repository is public.
- MUST search existing issues first. Add evidence to an existing proposal rather
  than opening a second one — two thin proposals lose where one well-evidenced
  proposal wins.
- If a human is present, show the full text and get approval before filing.

Required: what happened and which step, what it cost, how often and across how many
rounds, the narrowest change that would have prevented it, blast radius on projects
that never had the problem, and the strongest argument against your own proposal.

### What happens next

The proposal is audited against
[`docs/REVIEW_RUBRIC.md`](https://github.com/max-friedman/agentic-coding-loop/blob/main/docs/REVIEW_RUBRIC.md),
whose posture is **reject by default**. Expect rejection; it costs one round trip
and is recoverable by resubmitting with better evidence.

Rejections name the criterion that failed and what would change the answer. Read
the criterion — the most common failures are *no evidence* (a preference in
evidence's clothing), *growth without deletion*, and proposing prose where a
mechanism was available.

Nothing filed takes effect until it is accepted, written, released as a version
bump, and pulled by each project.

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
| Queue is empty and the round generated no new items | There is nothing to do. Say so rather than inventing work. Deferred once — and only once — if `roast-on-empty` is enabled: run §E, then re-evaluate. |
| A roast produced no complaint not already in the roast log | §E is exhausted. The product has stopped teaching you anything, and further roasts are churn. Fires even under `indefinite`. |
| Two consecutive rounds ended `blocked` | Everything left needs a human. |
| A round produced no commit | The sequence is spinning. |
| The same item has been attempted twice without shipping | It is mis-scoped. Split it in the queue and stop. |
| Round budget for the session is reached | Default 3. Raise deliberately, not by drift. |
| The working tree is dirty at a round boundary | Someone else is editing, or the previous round did not finish. |

### Unattended runs

When no human is watching — a scheduler, a cron trigger, CI — the additional rules
are absolute:

- **Never commit to the default branch.** Work on `loop/round-N` and open a pull
  request. You never merge your own round — the next round reviews and merges it,
  per *Reviewing the previous round* below.
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
- **Never weaken your own limits.** An unattended sequence may not edit the project
  rules, the standing invariants, the stop conditions, `## Loop configuration`, or
  this protocol to make its own work easier. Propose the change through §C and keep
  running under the current rules until it lands. An agent that can rewrite its own
  constraints has none. `indefinite` is the setting most worth enabling and the one
  a round must never enable for itself.
- **Fail loudly.** If you cannot complete the round, say so and stop. A silent
  no-op is indistinguishable from a healthy quiet day, and nobody is watching.

### Reviewing the previous round

A round never merges itself. The **next** round's session reviews and merges it —
a fresh session that did not write the work and cannot be attached to it. Do this
before picking up the new item, at the top of §0.

Green CI is not a review. It proves the code runs, not that the round did what its
writeup says.

Read the diff against the round's own claims:

| check | what fails it |
|---|---|
| The finding is supported | The writeup claims a result the diff does not show, or claims a measurement with no measurement in the diff. |
| A before-number exists | §3 required one and there is none, so "it improved" is unfalsifiable. |
| One item | The diff sprawls across unrelated concerns — a regression in it cannot be attributed. |
| Nothing was weakened | An assertion relaxed, a threshold lowered, a test skipped, a new component exempted from an existing check. **Hard stop, regardless of green CI.** |
| Numbers match | A doc still quotes a figure this diff moved. |
| The state file is honest | The `## Round N` entry describes what actually shipped, names an ending state, and carries its `Loop:` line. |

Three outcomes, and only the first merges:

- **Merge.** Every check passes. Say in the merge which checks were closest to
  failing — that is the signal the next reviewer needs.
- **Request changes.** Comment naming the failed check and what would fix it, and
  leave the PR open. Add it to the queue as the next round's item, **naming this
  PR's number in the queue entry** — the fix is a separate round on a separate
  branch, so without that number nothing connects the two and this PR is orphaned.
- **Close.** The round was wrong-headed, not merely incomplete. Record why in the
  state file under *Noted, not built*, so it is not re-attempted.

**Then close what the sequence has outgrown.** After handling the previous round's
PR, check every older open round PR: if its queued fix has since merged, the PR is
superseded — close it, referencing the round that replaced it.

This is not tidying. A request-changes PR is never revisited by the review step
above, which only ever looks at the *previous* round. Left alone it stays open
forever and permanently consumes one of the three slots the backlog rule allows.
Two of them and the loop halts for good, with no failing check to explain why.

**Do not fix the PR yourself.** Repairing it collapses reviewer and author back
into one agent and destroys the only independent check in the sequence. Comment,
leave it, move on — the fix is a round, with its own before and after.

If more than **two** round PRs are open *after* closing superseded ones, stop and
start no new round. Report that
rounds are outpacing review. A stream of unread diffs is worse than no diffs, and
nothing else in the system is positioned to notice.

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

---

## §E Roast round (opt-in, refills an empty queue)

An empty queue is normally a correct stop. This section is the deliberate,
human-enabled exception: instead of halting, meet the product as a **first-time
user with no goodwill** and let the complaints become the next rounds.

Ship no features. Like §A, the deliverable is a finding — here, a critique.

**The failure this must not become:** work invention. A queue refilled with
plausible-sounding tasks is worse than an empty one, because the empty queue was
telling you something true. Every mechanism below exists to keep that from
happening, and a roast that finds nothing is a success.

### Configuration

Read from `## Loop configuration` in the state file at §0. All settings default
**off**, so a project that never opts in behaves exactly as before.

| setting | default | meaning |
|---|---|---|
| `roast-on-empty` | `off` | When the queue empties, run §E instead of stopping. |
| `indefinite` | `off` | After a roast refills the queue, keep running rounds. Requires `roast-on-empty`. |
| `roast-budget` | `1` | Consecutive roasts allowed before stopping regardless of what they find. |

`indefinite` lifts **only** the empty-queue stop condition. A red gate, a
would-be-weakened invariant, two consecutive `blocked` rounds, a round with no
commit, an item attempted twice, a dirty tree, and more than two open round PRs all
still halt the sequence. There is no setting that lifts those, and adding one is a
§C proposal that the rubric rejects on sight.

### 1. Roast blind

Approach the artifact the way a user meets it: from its entry point, with no
knowledge of how it was built or what it claims about itself.

The mechanism that enforces this — **every complaint MUST cite something a user
could hit.** A command you actually ran and its actual output, a page a user lands
on, a screen they see, a step they must perform. A complaint whose only support is
the round history, the coverage map, or an internal design doc is struck before it
reaches the table. You are not permitted to roast the code; you are roasting the
product.

Prefer, in order: run the thing end to end as a new user would; follow the install
or quickstart path literally, doing exactly what it says and nothing it assumes;
read only the docs a user would actually find.

Where the roast and the project's own docs disagree, the roast is the evidence —
the docs were written by whoever built the thing.

### 2. Verify against ground truth

Every complaint that survived step 1's citation requirement still gets checked
against what the blind pass didn't have — application state, logs, or a second
independent run — and tagged one of three ways:

- **Real.** The cause is correctly attributed, and a user could genuinely
  encounter it.
- **Critic-mistake.** Something was seen, but the roast misattributed the cause.
- **Environment-artifact.** The cause is real but a user would never hit it — a
  test-harness quirk, leftover state from a previous pass, tooling noise. Not
  something this product does to a user; something this *check* did to itself.

Citing something you saw is not the same as diagnosing it correctly. A critic can
genuinely observe a real screen and still guess wrong about why it looks wrong —
step 1's bar catches fabrication, not misattribution.

**The guardrail this step must not become:** ground-truth access explaining away a
complaint a real user would still experience, just because the internal cause
differs from what the critic guessed. Only *environment-artifact* — a cause a user
could never reach — drops a complaint. A *critic-mistake* keeps the observation
and corrects the cause; it does not disappear.

Only **real** complaints proceed to step 3's verdict and step 5's queue.
Critic-mistakes and environment-artifacts are recorded in the roast log with their
disposition, so the same false alarm is not re-diagnosed from scratch next time.

### 3. Write the verdict before the fixes

One honest paragraph in the user's voice, built from the **real** complaints only:
what this is, whether it did the job, and what you would say about it to someone
considering it. Write it before proposing a single improvement — a verdict written
afterward is shaped to justify the fixes already in mind.

Be specific and unkind. "The quickstart is confusing" is not a complaint. "The
quickstart's first command fails because it assumes a config file that step 4
creates" is.

### 4. Deduplicate against the roast log

Read `docs/plans/ROAST_LOG.md`. A complaint already recorded there and deliberately
not queued MUST NOT be re-queued without **new** evidence — say what changed.

Without this, an indefinite loop cycles on the same three complaints forever and
reports motion.

### 5. Convert only what is falsifiable

Each surviving **real** complaint faces one test: **can it be phrased as a
question with a measurement that could come back bad?**

- Passes → queue it, in §2's form: the question, and what a negative result looks
  like. It is now an ordinary queue item and the next round is an ordinary round.
- Fails → record under *Noted, not queued* with the reason. Preserved so the next
  roast does not re-raise it, and so a later round with better tooling can.

A complaint that cannot be made falsifiable is not thereby wrong. It is not yet a
round.

### 6. Write the roast log

Append to `docs/plans/ROAST_LOG.md` — create it from
[`templates/ROAST_LOG.template.md`](templates/ROAST_LOG.template.md) if absent.
This is the roast's changelog: one entry per roast, newest at the bottom, never
edited afterward.

```markdown
## Roast N — <date> — <one-line verdict>

**Ran as:** the journey actually performed — commands, entry points, what a user was assumed to want.
**Verdict:** the honest paragraph from step 3, built from real complaints only.
**Complaints:** table of complaint | evidence cited | verified (real / critic-mistake / environment-artifact) | falsifiable | disposition.
**Queued:** items added, each as a question.
**Noted, not queued:** complaints that could not be made falsifiable, or that verification found was a critic-mistake or environment-artifact, with why.
**New this roast:** how many complaints do not already appear above. Zero means stop.
```

Then update `## Queue — next rounds` in the state file and record the roast on the
current round's **Loop:** line. Never write `## Loop configuration`.

### 7. Decide whether to continue

| condition | action |
|---|---|
| Complaints queued, `indefinite` on | Resume at §0 with the refilled queue. |
| Complaints queued, `indefinite` off | Stop. Report the queue for a human to approve. |
| **New this roast is zero** | Stop, whatever `indefinite` says. The roast is exhausted. |
| `roast-budget` consecutive roasts have run | Stop. Say how many rounds each roast bought. |

A roast counts against the session's round budget. It is a round that ships
nothing, not a free action appended to one.

### The honest limitation

A roast is a model's impression of a user, not a user. It reliably finds broken
quickstarts, unexplained errors, and undocumented assumptions, because those are
visible from the artifact. It does not find what users actually want, because it
has never wanted anything. Treat a queue of roast-derived items as maintenance
work with evidence behind it — never as a product roadmap, and never as a
substitute for asking someone.
