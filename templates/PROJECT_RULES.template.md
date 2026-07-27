# Contributor & agent guide

> Template for your project's `CLAUDE.md` / `AGENTS.md`. The pointer at the top
> and the two closing sections are the loop's machinery; everything between them
> is yours. Delete this blockquote.

**Working the improvement loop? Read [`docs/plans/LOOP_STATE.md`](docs/plans/LOOP_STATE.md)
first and write it last.** It holds the queue, the coverage map, the NEEDS-MAX list,
and the standing invariants. Context is lost between rounds; that file is not.

Read this before changing anything. _<One or two sentences on how this project
fails — the specific way it could stop doing its job while every surface signal
still looks healthy. Most of the rules below exist to prevent that.>_

## Layout

```
src/...        <what lives where, one line each>
docs/...       <the docs an agent must not contradict>
```

## Rules that protect the project's meaning

<!-- Numbered, each with a name that states the rule, a paragraph on why, and
     wherever possible the incident that motivated it. A rule with a scar attached
     survives contact with an agent under time pressure; an abstract one does not.
     Name the test that enforces each rule. -->

**1. <Rule stated as an imperative.>**

_<Why. What breaks without it.>_

_<The incident, if there was one. "This is not hypothetical" is the most load-
bearing phrase you can write here — it tells a future agent the rule was paid for
in real debugging time, not invented.>_ `<TestName>` enforces this. Do not weaken it.

**2. <Next rule.>**

...

## Working on this

```bash
<test command>          # must be green before any commit
<lint command>
<the command that shows you real output, not just a number>
```

_<What to re-run and which docs to update after touching each subsystem. Be
specific: "after changing costs, the generator, or the heuristic, re-run eval and
update the results table in README.md. A README quoting stale numbers is worse
than one quoting none.">_

## Priorities

In order. Each is a self-contained increment.

<!-- Mirrors the queue in LOOP_STATE.md but from the maintainer's point of view.
     State which one is the result the project exists to produce, and say
     explicitly that it gets reported honestly whichever way it lands. -->

1. _<the increment that matters most, and why>_
2. _<next>_

## Tone

_<What honesty means for this project specifically. If the work's credibility
rests on a limitations section, say so, and require that adding a capability moves
the corresponding limitation out of the list — and that finding a new weakness adds
one. Overclaiming is the fastest way to make the work worthless.>_
