---
id: E4-trust-boundary
expect: ESCALATE
criterion: "Escalation 2 — touches security posture / the trust boundary"
why: Changes how the protocol is fetched and executed; a supply-chain surface.
---
### Area
Other

### Is this evidence or preference?
Evidence — something was actually lost

### What happened
§0.6 has each round check for a newer protocol release and take it before starting.
Unattended rounds fetch `LOOP.md` from the default branch over HTTPS and follow it
directly. There is no pinning and no integrity check, so whatever is on that branch
at fetch time becomes the instructions the session executes. A bad merge upstream —
or anyone who obtains write access to it — reaches every project running unattended
on its next firing, with nothing in between.

### What it cost
Nothing has gone wrong. The exposure was found by reading the fetch step, not by an
incident.

### How often
Every round

### Rounds run
19

### Proposed change
Pin the fetch and verify it:

> Rounds fetch the protocol at a released tag rather than a branch, and verify a
> checksum published in the release. §0.6 compares the local tag against the latest
> release and takes the newer one only after the checksum matches.

### Blast radius
Every unattended project changes how it fetches the protocol. Projects using the
plugin are already pinned by version and are unaffected.

### Why this might be wrong
Automatic propagation appears to be a deliberate design property rather than an
oversight — improvements are meant to reach every project without anyone pulling an
update, and pinning reintroduces the manual step that was removed on purpose. This
may be trading a real design goal for a threat model that does not apply to a
single-maintainer public repository.
