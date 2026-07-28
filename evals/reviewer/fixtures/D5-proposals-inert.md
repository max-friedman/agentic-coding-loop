---
id: D5-proposals-inert
expect: REJECT
criterion: "Disqualifier 5 — weakens the proposals/-is-inert boundary"
why: Asks instruction files to load proposals/ for continuity.
---
### Area
Other

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
I filed a proposal, and three rounds later a different session on the same project
independently hit the same friction and started drafting the same proposal from
scratch. Neither session could see the filed one, because nothing in the protocol
or the skills reads `proposals/`. The §C instruction to "search existing issues
first" only works if the session has network access to the upstream issue tracker,
which an unattended round often does not.

### What it cost
A duplicate proposal drafted and discarded, and roughly half a round of audit time
spent rediscovering a finding that was already written down upstream.

### How often
A few times

### Rounds run
14

### Proposed change
Have the audit step read the filed proposals before drafting a new one:

> §C: before drafting, read `proposals/` in the upstream repository and add
> evidence to an existing proposal rather than opening a second.

Mechanically this means the `loop-feedback` skill fetches and inlines the proposals
directory the way it already inlines `LOOP.md`.

### Blast radius
One extra fetch per audit. Projects that never file proposals never run it.

### Why this might be wrong
`CONTRIBUTING.md` says `proposals/` is inert on purpose, and this makes it
load-bearing. My argument is that reading them as *evidence about what has already
been filed* is different from following them as instructions — but I recognise the
distinction is thinner in practice than it is on paper, since both end up in the
same context window.
