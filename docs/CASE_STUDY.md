# Case study: seven rounds on TactBench

One project, reported as it happened — including the round that proved the
project's headline claim false, and the later round that turned on the loop itself
and found two failures the protocol had been carrying silently.

Rounds 1–4 are recorded from the project's own state file. Rounds 5–7 are
summarized from the proposals they produced ([#2](https://github.com/max-friedman/agentic-coding-loop/issues/2),
[#3](https://github.com/max-friedman/agentic-coding-loop/issues/3)) rather than from
the state file, and are flagged as such below.

[TactBench](https://github.com/max-friedman/tactbench) is a benchmark for whether
a proactive assistant should speak at all. It scores interruption timing rather
than answer quality. Its central design claim was that **matched pairs of
scenarios prevent a model from succeeding by keyword matching** — two moments
with the same content, opposite correct answers, so surface features can't
separate them.

That claim was in the README from the first commit. It had never been measured.

---

## Round 1 — shortcut resistance

**Question:** does the matched-pair design actually prevent surface pattern
matching, or is that just a claim in the README?

**Method:** a dependency-free bag-of-words probe over signal text only — no user
state, no do-not-disturb flag, no slice tags. Cross-validated with pairs kept
whole across folds, so neither half of a pair could leak into the fold that
scored the other. A design that works should push this probe to the 50% floor.

**Finding: the claim was false.** The probe hit **93.5%**.

Each scenario had one fixed phrasing per side, so tokens appearing on exactly one
side — `hallway`, `inflight`, `closes` — gave the answer away. The pairs were
matched by *family*, not by *structure*: each side had been written as a
different sentence about the same situation. That is not a permutation, and a
bag of words could see the difference immediately.

**Fix:** the generator was rebuilt around **role permutation**. Both sides now
share a byte-identical body and an identical user state; one signal differs by
swapping which noun plays which role, never by rewriting the sentence. The probe
fell to **57.5%**, with five of six families at the chance floor.

**Consequences, all verified:**

| effect | detail |
|---|---|
| The reference heuristic collapsed | precision 0.818 → 0.560, i.e. chance. Its old score had been leakage, not skill. |
| Nothing beat silence | with the shortcuts gone, every baseline scored worse than saying nothing at all. |
| A ceiling policy was added | to prove the task was still solvable and the benchmark not degenerate. |
| A label bug surfaced | one scenario variant had **inverted labels** — its "positive" case described a user who was already where the notification would have sent them. |

That last row is worth dwelling on. The inverted labels had been in the dataset
since the beginning, passing every test, contributing to every published number.
They were found only because rebuilding the pairs forced someone to look at both
sides of each one side by side.

**Shipped:** the probe as a first-class CLI command, a ceiling policy, a rebuilt
generator, five new invariant tests, and corrections to both the README and the
dataset documentation.

---

## Round 2 — build everything around the block

**Question:** with every shortcut removed and no baseline beating silence, the
question the project exists to answer is "can a frontier model beat saying
nothing?" It requires an API key. There isn't one.

**The wrong move** is to halt. The second-wrong move is to reason toward a
plausible number and publish it.

**What was built instead:** the entire harness. Provider-agnostic across three
APIs. One moment per call — never batched, because batching would leak the
dataset's 50/50 balance and let the model compare moments a deployed assistant
could never compare. The prompt kept verbatim in source and versioned.
Unparseable output scored as silence rather than dropped. Per-run caching so a
paid run is never accidentally repeated. Two prompt variants — one withholding
the cost structure, one disclosing it — so the gap between them would distinguish
*wrong disposition* from *missing judgment*.

Twenty-three tests, none of which need a key.

**A leak caught in passing:** the function that renders a moment for the model
deliberately omits the family name, the slice tags, and the moment ID. The slice
tags literally contain `near_miss` — shipping them would have handed the model
the label and silently invalidated every result the harness would ever produce.
Four tests now enforce the omission. Two of them failed on first run over
legitimate collisions: the activity value `driving` and the contact class
`family` both genuinely belong in the prompt. The assertions were narrowed to the
labelled-field form. **The code was not changed to satisfy the test.**

**Not done, deliberately:** no numbers. Nothing about LLM performance appears
anywhere in the repo, and nothing may until a run actually happens. The item sits
in NEEDS-MAX with the exact three commands that unblock it.

It is still sitting there. That is the rule working, not the rule failing.

---

## Round 3 — more degrees of freedom

**Question:** after round 1, the top remaining weakness was that six scenario
families is six effective degrees of freedom no matter how many items you
generate. Phrasing was no longer the weak point; scenario count was.

**Shipped:** three new families, each built as a role permutation from the start
rather than retrofitted — which prescription is still at the counter, which
parent is listed for pickup, which account autopay actually draws from. Dataset
240 → 360 items.

**Caught by the probe before it landed:** the health family scored **82.5%** on
first pass. The deciding signal ended `your prescription` on one side and `yours`
on the other. Different tokens, so the probe latched on instantly.

Nobody would have caught that by eye. It is a two-word difference in one of nine
families, in a sentence that reads naturally either way. Repeating the noun on
both sides made it a true permutation and it dropped to exactly 50.0%.

This is the payoff of principle 3 — the check existed *before* the work, so a
regression that no reviewer would have seen was caught before it entered the
dataset rather than three rounds later.

**Result:** eight of nine families at exactly 0.500. The remaining one is a
documented, named exception where the distinction genuinely isn't permutable, and
it is excluded from the per-family assertion **by name** — never by relaxing the
threshold.

---

## Round 4 — the base rate

**Question:** the balanced 50/50 split makes the contrast legible, but no
deployed assistant has ever seen a 1:1 prior. Every number in the repo was
implicitly claiming one.

**Shipped:** base-rate weighting throughout the scoring path, so each stay-quiet
item can stand in for the many real moments it represents.

**Result — the most decision-relevant number in the project:** at a realistic
100:1 ratio, precision collapses from 0.514 to **0.010**. Ninety-nine of every
hundred interruptions would be unwanted.

**Design calls recorded with the round:** hard violations are deliberately *not*
reweighted, because they count distinct moments in the benchmark rather than
estimated production volume, and conflating the two would make the number
meaningless.

**Noted, not built:** a "percent of achievable" column was proposed and rejected
— the existing normalized score already maps silence to 0 and a perfect score to
100, so the column already existed under a different name. Recorded with the
reasoning so round 7 doesn't propose it again.

---

## Rounds 5–7 — the loop turns on itself

*Summarized from the proposals these rounds produced, not from the project's state
file.*

A round added CI to a project that had reported a green suite for five consecutive
rounds. **It failed on its first run.** Dev tooling was declared as an
optional-dependencies extra rather than a dependency group, so the runner installed
neither the test runner nor the linter. The suite had never once executed in a
clean checkout.

Nothing had been dishonest. Every "60 tests pass" was true — and true only on the
one machine where the extra had been installed by hand. The claim was never
checkable, so nobody checked it.

Then a round took **the protocol itself** as its target rather than the product,
and found a second failure of the same shape. Rounds 1–4 had committed straight to
the default branch while the protocol said "ship via a pull request" the entire
time. The rule was written, correct, and read. It was also placed at step 7 — by
which point the commits already existed and there was nothing left to open a pull
request *from*.

Both failures were invisible from inside the rounds that created them. Neither
self-corrected. Both surfaced only when a round went looking at the process instead
of the product.

They became proposals [001](../proposals/001-gate-outside-one-machine.md) and
[002](../proposals/002-branch-fires-too-late.md), and both were accepted narrower
than filed — 002 landing at a different step than its author proposed, on the
strength of that author's own stated objection to their primary placement.

**The generalizable half:** a loop pointed only at the product will keep the
product honest and let the process rot. That is why auditing the loop is now part
of running it, on a cadence, rather than something that happens when a human
notices.

---

## What the loop actually bought

**Round 1 deleted a false claim that had been shipping since the first commit.**
Not a bug — a claim about the project's central design property, contradicted by
the first measurement anyone took of it. Everything downstream of it had been
measuring leakage.

**Round 3 caught a two-word regression that no human reviewer would have seen**,
because round 1 had left behind a check that ran automatically and round 3 was
required to add the new families to it rather than exempt them.

**Round 2 built a complete evaluation harness it was not allowed to run**, and
published nothing about it. Three rounds later there is still no number, and the
repo still says so.

**Round 4 produced the number that most changes what someone would do** — and it
was bad news for the thing being built.

**Rounds 5–7 found that two of the protocol's own guarantees were unenforceable**,
and routed the fixes back to every project running it.

Seven rounds. The most valuable outcomes were a refutation, a regression catch, an
unrun experiment that stayed unrun, and two findings against the process itself. A
loop that can only produce features would have produced none of them.
