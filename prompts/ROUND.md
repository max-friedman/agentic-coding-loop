# The round prompt

Paste this into a fresh agent session. It assumes the agent has no memory of any
previous round — which is the point.

---

```
Run one round of the improvement loop on this repo.

Start by reading docs/plans/LOOP_STATE.md in full. It is the only memory you
have of previous rounds. Read the project rules file (CLAUDE.md / AGENTS.md) too.

Then:

1. Pick ONE item. Take it from the queue unless a finding from the last round
   makes something else clearly more urgent. If you deviate, say why in the
   round writeup. One item, not three — a round that half-lands three things
   leaves the next round unable to trust any of them.

2. Before building it, ask: what would show this is wrong? Write down the
   question the round answers. If there is no outcome that would count as bad
   news, you have picked a task, not a round — reframe it until a negative
   result is possible.

3. Build the check before the thing. If the round's claim is measurable, the
   measurement lands first, and you run it against the CURRENT code so you have
   a before number. A check written after the fact tends to be a check the work
   already passes.

4. Build it. Keep the repo shippable at every commit.

5. Verify. Run the gate command from the project rules — tests and lint both
   green, no exceptions. Look at real output, not just the summary number.
   Re-run any measurement the change could have moved, including ones from
   earlier rounds, and update every doc quoting a number you changed. Stale
   numbers in a README are worse than no numbers.

6. Write docs/plans/LOOP_STATE.md LAST, and treat it as the deliverable:
   - append a Round N section: question, method, finding, shipped,
     consequences (verified, not predicted), noted-but-not-built
   - rewrite Current status
   - update the coverage map
   - re-rank the queue based on what you just learned
   - add any new standing invariant you encoded as a test
   - add to NEEDS-MAX anything you hit that needs a human

Rules for the round:

- If a standing invariant fails, the code is wrong, not the assertion. Fix the
  code. Never relax an assertion to make a round pass. If you genuinely believe
  an invariant is mis-stated, say so in the writeup and leave it failing rather
  than editing it quietly.

- If you find a claim this project makes about itself that turns out to be
  false, that IS the round. Report it plainly, fix what you can, and correct
  the docs. Deleting a false claim is worth more than adding a feature.

- If you are blocked on something only a human can provide — a credential, a
  spend approval, a decision that isn't yours — add it to NEEDS-MAX with the
  exact command that unblocks it, then build everything around the block. Do
  not halt. Do not guess the result. Do not publish a number you did not
  actually measure.

- Never edit a previous round's section to make the history look tidier.

Commit with a message naming the round's finding, not its task.
```

---

## Variants

**Continuous.** With a scheduling mechanism (a cron trigger, `/loop`, a CI job),
fire the same prompt on an interval. The state file is what makes an unattended
round safe: each firing reads the same spine, and a round that goes wrong is
visible in the writeup rather than silently absorbed.

**Constrained.** Append one line to scope a round without rewriting the prompt:

```
This round: <the specific item>. Ignore the queue ordering.
```

**Audit-only.** For when you suspect drift but don't want changes:

```
Run a round, but ship no features. Pick the strongest claim this repo makes
about itself and measure whether it still holds. Report the number even if it
is bad — especially if it is bad. Then update LOOP_STATE.md.
```

This variant is what caught the 93.5% leak described in
[`../docs/CASE_STUDY.md`](../docs/CASE_STUDY.md). Run it when a project has been
green for several rounds in a row: uninterrupted green is a signal that the
checks have stopped being adversarial, not that the work is finished.
