# The round protocol

A round is one unit of compounding progress: small enough to finish in a single
agent session, self-contained enough that stopping after it leaves the project
better than before, and *falsifiable* — it can come back with bad news.

## The seven steps

### 1. Read the state file, all of it

Not skimmed, not the first section. The standing invariants are at the bottom,
and an agent that skips them will weaken one within the hour. The queue's
ordering carries reasoning from a session that no longer exists.

### 2. Pick exactly one item

From the queue, unless the last round's finding makes something else clearly more
urgent — in which case take it and record why.

One item. The temptation is three, because each looks small. Three half-landed
changes leave the next round unable to attribute a regression to any of them,
and the writeup degrades into a changelog.

Then **cut the branch, before the first edit** — `git checkout -b <type>/<slug>`.
Shipping (§7, and §D for unattended runs) assumes the round's work sits on its own
branch, and that assumption is unfollowable if the work is already committed to
the default branch. See principle 10: this is placed here, rather than next to the
instruction it serves, precisely because here is the last moment it can still be
acted on.

### 3. Ask what would prove it wrong

This step is the difference between a loop and a task list.

> "Add three more scenario families" is a task. It will succeed. It teaches you
> nothing.
>
> "Six families is six effective degrees of freedom regardless of item count —
> does adding three change what the probe sees?" is a round. It can fail.

Write the question into the round section before building. If you cannot
construct an outcome that would count as bad news, reframe until you can.

### 4. Build the check first, and run it on the current code

The measurement lands before the change, and gets a **before** number from the
existing state. Two reasons:

- A check written afterward tends to be a check the new code already passes.
- Without a before number, "it improved" is unfalsifiable.

This is also where new work gets gated: if a scenario, module, or dataset family
is added later, it must be added to the check — never exempted from it.

### 5. Build it, keeping the repo shippable

Every commit leaves the gate green. A round that ends mid-refactor has produced
nothing, because the next session starts cold and cannot tell a deliberate
half-state from a broken one.

**Mechanical churn gets its own commit.** Formatting sweeps, renames, and
regenerated files go in a separate commit that is explicitly behavior-free —
demonstrated by running the gate before and after and confirming the numbers are
identical. Mixed into a logic change they make the diff unreviewable, and they
poison `git blame` for every line they touch: the next agent tracing why a line
exists lands on a whitespace pass instead of the reasoning.

### 6. Verify wider than you changed

Run the gate: tests and lint, both green. Then:

- Look at actual output — failures, samples, rendered results — not just the
  summary metric. A number can look reasonable while the thing underneath is
  wrong in a way that is obvious on sight.
- Re-run measurements from **earlier** rounds that this change could have moved.
  This is where silent regressions live.
- Update every document quoting a number you changed. Stale numbers are worse
  than no numbers: they carry the authority of a measurement without being one.

Two gate-mechanics failure modes are easy to miss because they don't show up in
the diff: a gate command and a merge command chained in one script block that
runs the merge even after the gate fails (check the exit status explicitly,
merge as a separate step), and a red result on code the round didn't touch,
which is a flake suspect, not a verdict, until it's been rerun 3× plus a clean
full suite.

### 7. Write the state file last, as the deliverable

Not a summary of the work — part of the work. Append the round section, rewrite
current status, update the coverage map, re-rank the queue against what you just
learned, record new invariants, add anything blocked to NEEDS-MAX.

Treat the writeup as being read by a stranger with no context, because it will
be. Then merge the round's branch — directly on local green if a human is
driving, or as a pull request under §D's unattended rules if not.

## How a round ends

Exactly one of these. Every one is a legitimate ending.

| ending | what it looks like |
|---|---|
| **Shipped** | The item landed, the gate is green, the docs match the numbers. |
| **Refuted** | The measurement said the plan was wrong. The plan is dead, the finding is recorded, the queue is re-ranked. This is the highest-value ending. |
| **Blocked** | It needs a human. It goes to NEEDS-MAX with the unblocking command, and the round redirects to something buildable around the block. |
| **Rejected** | Built enough to evaluate, then deliberately not kept. Goes in *Noted, not built* with the reasoning, so it is not rediscovered. |

There is no "partially done" ending. If the item is bigger than a round, that
finding is itself the round's output: split it in the queue and stop.

## Anti-patterns

**The green streak.** Several rounds in a row where everything passes and
everything ships. This usually means the checks stopped being adversarial. Run
the audit-only variant in [`../prompts/ROUND.md`](../prompts/ROUND.md).

**The tidy history.** Editing an old round section so the record reads better.
The wrong turn is the most valuable thing in the file — it is the only reason the
next agent won't take it.

**The assertion nudge.** A test fails, and the smallest change that makes it pass
is in the test. This is always locally cheapest and always wrong. If an invariant
is genuinely mis-stated, say so in the writeup and leave it failing.

**The unmeasured claim.** Publishing a number the round did not actually produce,
because the harness exists and the result seems obvious. If it did not run, it has
no number.

**The context-window bet.** Relying on the agent remembering something rather than
writing it down. It will not remember. That is the premise of the whole system.
