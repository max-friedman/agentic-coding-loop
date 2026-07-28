# Roast log

The changelog of roast rounds. **Append only.** One entry per roast, newest at the
bottom, never edited after it is written.

> Copy this file to `docs/plans/ROAST_LOG.md` in your project and delete this
> blockquote. It is created on the first roast — see `LOOP.md` §E.

This file exists so an indefinite loop cannot cycle. Every roast reads it first: a
complaint already recorded here and deliberately not queued may not be re-queued
without new evidence, and a roast that produces nothing not already here stops the
loop regardless of configuration.

---

## Roast N — YYYY-MM-DD — <one-line verdict>

**Ran as:** _the journey actually performed. Which entry point, which commands,
what a user was assumed to be trying to do. Be concrete enough that someone else
could repeat it._

**Verdict:** _one honest paragraph in the user's voice, written before any fixes
were considered. What this is, whether it did the job, what you would tell someone
considering it._

### Complaints

<!-- Every row must cite something a user could hit: a command and its real
     output, a page they land on, a step they must perform. A complaint supported
     only by the round history or an internal doc is struck before it gets here.
     Every row must also be checked against ground truth (§E step 2) — real,
     critic-mistake, or environment-artifact. Only "real" rows proceed to the
     falsifiability test. -->

| # | complaint, in the user's voice | evidence cited | verified | falsifiable? | disposition |
|---|---|---|---|---|---|
| 1 | _"..."_ | _`the command you ran` → what happened_ | real | yes | queued as Q3 |
| 2 | _"..."_ | _the page a user lands on_ | real | no | noted, not queued |
| 3 | _"..."_ | _what the critic saw_ | critic-mistake — _actual cause_ | — | noted, not queued |
| 4 | _"..."_ | _what the critic saw_ | environment-artifact — _what actually happened_ | — | noted, not queued |

**Queued:** _items added to the state file, each phrased as a question with what a
negative result would look like._

**Noted, not queued:** _complaints that could not be made falsifiable, and why.
Preserved so the next roast does not re-raise them, and so a later round with
better tooling can pick them up._

**New this roast:** _how many complaints do not already appear in an earlier entry.
**Zero means the roast is exhausted and the loop stops**, whatever `indefinite`
says._
