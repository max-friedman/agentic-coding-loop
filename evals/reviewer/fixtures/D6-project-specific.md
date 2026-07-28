---
id: D6-project-specific
expect: REJECT
criterion: "Disqualifier 6 — project-specific workflow"
why: A monorepo-shaped gate matrix that only helps repos laid out like the submitter's.
---
### Area
Round protocol (the seven steps)

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
§5.1 says to run the project's gate command. In a monorepo with eleven packages
there is no single gate command — there is a per-package matrix, and running all of
it takes 40 minutes. Rounds either ran everything (slow) or ran the package they
touched (and missed cross-package regressions twice).

### What it cost
Two cross-package regressions shipped and were caught by a downstream consumer
rather than by the round. Roughly six rounds paid the 40-minute penalty
unnecessarily.

### How often
Every round

### Rounds run
16

### Proposed change
Replace §5.1 with matrix-aware guidance:

> Run the gate for every package whose dependency graph includes a changed file.
> Determine the set with `turbo run test --filter=...[HEAD^1]` or the equivalent for
> your workspace tool. Record the affected package set in the round writeup.

### Blast radius
Single-package projects read the first clause and run their one gate. Monorepos
get the behavior they need.

### Why this might be wrong
The rule names a specific tool, and a protocol that mentions `turbo` will be stale
in two years. A tool-agnostic wording would be weaker but would age better. I chose
the specific version because the vague one is what §5.1 already says and it did not
work.
