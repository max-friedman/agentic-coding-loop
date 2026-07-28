# Principles

Eleven rules. Each one names a specific failure it prevents. None of them are
abstract — they were paid for.

Rules 9 and 10 arrived differently from the rest: they came from projects running
the loop, as proposals, and were accepted narrower than filed. Their mechanisms
live in [`../LOOP.md`](../LOOP.md); the reasoning is here, because a rule whose
justification exists nowhere is a rule that gets rationalized away.

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
which files mention it.** More than one doc usually states the same contract, and
the one you forget will be the canonical reference. A round that shipped a
project's most decision-relevant metric updated two docs from memory and missed
the metrics reference entirely — discovered rounds later, by audit rather than by
use. Each round should also re-check the *previous* round's doc edits, not only
make its own.

## 8. Scope stays honest in both directions

A capability shipped moves the corresponding limitation out of the limitations
list. A weakness discovered adds one.

The failure it prevents: **drift toward the flattering description**. Each
individual round has a small incentive to describe its own work generously.
Compounded over ten rounds, the project's self-description and the project stop
being the same thing — and the docs are the only thing a cold agent has to
navigate by.

## 9. The gate needs a home outside your machine

"The gate is green" is a claim. If it can only be checked where it was written, it
is an unverifiable one, and step 5 rests on it.

The failure it prevents: **green on one machine**. A project ran five rounds
reporting a green suite, then added CI and watched it fail on the first run — dev
tooling was declared as an extras group the runner never installed, so the tests
had never once executed in a clean checkout. Nothing had been dishonest. The claim
was simply never checkable, so nobody checked it.

The corollary matters as much: **a gate that has never failed is not yet known to
be a gate.** When CI goes red on its first run, that is the system working.

This repository ran the same way for six releases. `scripts/check.py` and
`.github/workflows/checks.yml` exist because writing the principle and not
following it would have been the more embarrassing outcome. Each of its checks was
verified to fail on a deliberate violation before it was trusted.

*Arrived as [proposal 001](../proposals/001-gate-outside-one-machine.md). Accepted
narrower than filed: the escape hatch is "record why", not "add CI", so it cannot
become a blocker for a project where CI genuinely cannot run.*

## 10. Enforce structure where it becomes impossible to add later

Some rules can only be followed if they fire early. Put them where skipping them
forecloses the option, not where they read most naturally.

The canonical case is the branch. A protocol saying "ship via a pull request" at
step seven is unfollowable if step five already committed to the default branch —
by then there is nothing left to open a PR *from*, and the only recovery is the
history surgery the same protocol forbids.

The failure it prevents: **the well-stated, never-followed rule**. A project ran
four rounds committing straight to `main` while its own protocol said "open a PR"
the entire time. The rule was written, correct, and read. It was also placed where
it could no longer be acted on.

**The fix is never to restate it more loudly.** This is principle 4 applied to
instructions rather than tests: relocate the rule, or encode it as a mechanism.
Prose that has already been ignored once will be ignored again.

*Arrived as [proposal 002](../proposals/002-branch-fires-too-late.md). Accepted at
a different step than proposed, on the strength of the submitter's own objection to
their primary placement.*

## 11. Citing something is not the same as diagnosing it correctly

A roast's one honesty rule — every complaint must cite something a user could
hit — catches fabrication. It does not catch misattribution: a critic can
genuinely see a real screen and still guess wrong about why it looks wrong, or be
looking at a test-harness artifact a real user could never reach.

The failure it prevents: **the confidently wrong complaint**. A project running an
informal predecessor of the roast round for months found a recurring minority of
complaints that passed the citation bar and were still wrong — a thing that looked
like two conflicting UI elements was two legitimate ones; a thing that looked like
data corruption was stale state left by a previous test pass; a thing that looked
like a dropped-input bug was an artifact of the harness driving the product, not
something a real user would ever hit. Every one satisfied "cite what you saw,"
because the critic genuinely did see it.

**The fix is a second check, not a stricter first one.** No citation requirement
distinguishes a correct diagnosis from a plausible-sounding wrong one; only
comparing the complaint against ground truth — state, logs, a second run — does.
The check may only correct or drop a complaint that turns out to be unreal. It may
never use internal knowledge to explain away a complaint a real user would still
experience — that would turn a truth check into a laundering step, which is the
one failure mode worse than not checking at all.

*Arrived as [proposal 003](../proposals/003-roast-findings-need-verification.md),
filed as evidence from a project's own history running that informal predecessor.
Accepted with the anti-laundering guardrail the submitter flagged against their own
proposal — the strongest objection to a proposal is sometimes the reason to keep it,
narrowed.*

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
