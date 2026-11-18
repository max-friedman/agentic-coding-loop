# One round, end to end

From a benchmark project that runs the single-agent loop. Its README claimed that
matched pairs of test scenarios stop a model from winning by keyword matching. That
had never been measured.

The state file's queue before round 1 (abridged):

```markdown
## Queue — next rounds
1. Does the matched-pair design actually prevent surface pattern matching,
   or is that just a claim in the README?
```

The round wrote down what would prove the claim wrong first: a bag-of-words probe
should score near the 50% floor. It built the probe and ran it on the unchanged code.
The state file after (abridged):

```markdown
## Round 1 — shortcut resistance
Finding: the claim was false. The probe hit 93.5% (floor 50%).
Each side of a pair had its own phrasing, so single words gave the answer away.
Fix: both sides share an identical body; one signal swaps roles. Probe: 57.5%.
Also found: one scenario variant had inverted labels since the first commit.
Ending state: shipped. Probe kept as a CLI command and five invariant tests.
```

The pull request carried the probe, the rebuilt generator, the corrected README, and
a reference heuristic whose score fell to chance: its old score had been leakage.

Every round of that project, with what each cost: [`CASE_STUDY.md`](CASE_STUDY.md).
The protocol the round followed: [`../LOOP.md`](../LOOP.md).
