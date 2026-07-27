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

## 8. Scope stays honest in both directions

A capability shipped moves the corresponding limitation out of the limitations
list. A weakness discovered adds one.

The failure it prevents: **drift toward the flattering description**. Each
individual round has a small incentive to describe its own work generously.
Compounded over ten rounds, the project's self-description and the project stop
being the same thing — and the docs are the only thing a cold agent has to
navigate by.

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
