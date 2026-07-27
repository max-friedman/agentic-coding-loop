# Principles

Eight rules. Each one names a specific failure it prevents. None of them are
abstract — they were paid for.

---

## 1. The state file is the memory

Read first, written last, every round. It holds current status, the round
history, a coverage map, blocked items, the queue, and the standing invariants.

The failure it prevents: **rediscovery**. Without it, round four spends its
session re-deriving what round two established, re-litigating a decision already
made, and re-proposing an idea already rejected for good reason. Progress looks
like motion and is not.

A corollary that is easy to miss: the state file must be honest about *bad*
outcomes, or it stops being memory and becomes marketing. A round history that
only records wins is a history that will let the same mistake happen twice.

## 2. A round asks a question

Not "add X" — "does X hold?" Every round names something that was actually
uncertain and states how a negative result would have looked.

The failure it prevents: **unfalsifiable progress**. An agent asked to improve
something will improve it and report success, every time, regardless of whether
the improvement mattered. The report is worthless because it was never in doubt.

## 3. Build the check before the thing, and run it before the change

The measurement lands first and produces a *before* number against existing code.

The failure it prevents: **the check that only ever passes**. Written afterward,
a check is unconsciously shaped to accept what was just built. Written first, it
is shaped by the question. And without a before number, "it improved" cannot be
falsified.

## 4. Invariants are encoded as tests, and may not be weakened

Every property the project depends on becomes an executable assertion, with a
written prohibition on relaxing it. When one fails, the code is wrong.

The failure it prevents: **the ratchet running backwards**. Relaxing an assertion
is always the locally cheapest way to make a round pass, and it is invisible in a
diff that also contains real work. This is the single highest-value rule in the
system, and the one most in need of being written down in the project rules
rather than assumed.

The strongest form pairs the invariant with a stated *reason* and, ideally, the
incident. "Heuristic lexicons stay single words, ≤ 20 entries" is a rule an agent
can rationalize around. The same rule plus "because the first draft scored a
perfect 1.000 by matching phrases copied out of the generator, and measured
nothing except that one person wrote both files" is not.

## 5. Blocked is not stopped

Anything needing a human — a credential, a spend approval, a decision that isn't
the agent's — goes on a NEEDS-MAX list with the exact command that unblocks it,
and the round redirects to what is buildable around the block.

The failure it prevents: **the halt**, and its worse sibling, **the guess**. An
agent that stops on a missing API key burns the round. An agent that reasons its
way to a plausible number instead has produced something actively harmful.

The discipline that makes this work: *no numbers may be published that were not
actually measured*. In the case study, an entire LLM-evaluation harness has been
built, tested, versioned, and cached across three rounds without ever executing,
because no key exists. Zero claims about its results appear anywhere in that repo.

## 6. Rejected ideas are recorded with reasons

A *Noted, not built* section for things examined and deliberately dropped.

The failure it prevents: **the loop**. Without it, a plausible-looking idea gets
rediscovered, rebuilt, and re-rejected every few rounds. The reasoning is the
payload, not the verdict.

## 7. Documentation is part of the change

Any number in a README, doc, or comment that a change could have moved gets
re-derived and updated in the same round.

The failure it prevents: **authoritative staleness**. A stale number is worse
than a missing one, because it carries the credibility of a measurement while
being a fossil. And in a project whose output *is* numbers, a stale table is
indistinguishable from a fabricated one.

Find the affected docs by **searching the repo for the concept, not by recalling
which files mention it**. More than one doc usually states the same contract, and
the one you forget will be the canonical reference. A round that shipped the most
decision-relevant metric in a project updated two docs from memory and missed the
metrics reference entirely — discovered rounds later, by audit rather than by use.
Each round should also re-check the *previous* round's doc edits, not only make
its own.

## 8. Scope stays honest in both directions

A capability shipped moves the corresponding limitation out of the limitations
list. A weakness discovered adds one.

The failure it prevents: **drift toward the flattering description**. Each
individual round has a small incentive to describe its own work generously.
Compounded over ten rounds, the project's self-description and the project stop
being the same thing — and the docs are the only thing a cold agent has to
navigate by.

## 9. The gate needs a home outside your machine

"The gate is green" is a claim, and if it can only be checked on one laptop it is
an unverifiable one. CI is where the gate lives. If a repo has none, adding it is
a legitimate round — and on public repos it is free. Where CI genuinely isn't
available, record *why* in the state file rather than letting the claim quietly
weaken.

The failure it prevents: **green on one machine**. A project ran five rounds
reporting a green suite, then added CI and watched it fail on the first run — the
dev tooling was declared as an extras group the runner never installed, so the
tests had never once executed in a clean checkout. Nothing had been dishonest.
The claim was simply never checkable, and so nobody checked it.

The corollary matters as much: **a gate that has never failed is not yet known to
be a gate.** When CI goes red on its first run, that is the system working.

## 10. Enforce structure where it becomes impossible to add later

Some rules can only be followed if they fire early. Put them at the point where
skipping them forecloses the option, not at the point where you'd like them to
exist.

The canonical case is the branch. A protocol that says "ship via a pull request"
at step seven is unfollowable if step five already committed to the default
branch — by then there is nothing left to open a PR *from*. The rule belongs at
step one.

The failure it prevents: **the well-stated, never-followed rule**. A project ran
four rounds committing straight to `main` while its own protocol said "open a PR"
the entire time. The rule was written, correct, and read. It was also placed
where it could no longer be acted on. **A rule stated only at the end of the loop
is a rule that gets skipped**, and the fix is never to restate it more loudly.

## 11. Never publish a number the round didn't produce

If an experiment was built but not run — no credential, no budget, no device —
say so in the docs and the PR, and publish nothing. Not a placeholder, not an
estimate presented as a result, not a figure carried over from a similar run.

The failure it prevents: **the unfalsifiable result**. Every other kind of error
in this list surfaces eventually: stale numbers get re-derived, weakened
invariants get caught by the next round, drifted docs get audited. A fabricated
measurement has no natural discovery path — it looks exactly like a real one, and
the only person who could ever detect it is the one who wrote it. Being blocked
is not embarrassing and is covered by principle 5. Papering over being blocked is
the one failure the loop cannot self-correct.

---

## What these have in common

Every one is a defense against the same underlying dynamic: **the locally optimal
move for a single session is worse for the project than the honest one.**

Relaxing the assertion, skipping the re-run, guessing the blocked number, tidying
the history, describing the work generously — each is cheap now and expensive
later, and each is invisible in the moment because the tests are green and the
round shipped.

An agent is not uniquely prone to this. It is just faster at it, and it will not
be around to feel the consequences. So the rules go in a file the agent must read
before it starts, with the scars attached.
