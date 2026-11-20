# Assumptions log: decisions made without the owner

The coordinator never waits on the owner. When a call is theirs to make and they aren't there, pick your
recommendation, act on it, and add a row here the same hour. The owner reviews the open rows when they have time; a
reversal becomes normal work.

What still waits for the owner: anything that can't be undone (permanent deletes, money, accounts, messages sent as
them, anything live users see that can't be rolled back) and approval of a new design direction.

**Format.** One row per decision, newest first. `Status` is `open` until the owner answers, then `confirmed <date>` or
`reversed <date> (<PR>)`; keep answered rows for a week, then delete them (git keeps the history).
`.claude/hooks/coordinator_digest.py` shows `Assumed, unreviewed: N` from the `open` rows.

| Date | Decision | Why | How to revisit | Status |
|---|---|---|---|---|
