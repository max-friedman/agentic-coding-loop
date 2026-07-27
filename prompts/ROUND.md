# The round prompt

**The canonical round instructions live in
[`../plugins/loop/skills/loop-round/SKILL.md`](../plugins/loop/skills/loop-round/SKILL.md).**

There is one copy on purpose. The Claude Code skill and the paste-it-yourself
prompt are the same text, so they cannot drift apart — which is principle 7 applied
to this repo rather than just described by it.

## Using it without Claude Code

Paste the body of that file into a fresh agent session, dropping the YAML
frontmatter between the `---` markers and the `$ARGUMENTS` line.

It assumes the agent has no memory of any previous round. That is the design, not a
limitation: everything the round needs is in `docs/plans/LOOP_STATE.md`, and a round
that only works with a warm context is a round that will fail the first time it runs
cold.

## Using it with Claude Code

```
/plugin marketplace add max-friedman/agentic-coding-loop
/plugin install loop@agentic-coding-loop
```

Then `/loop-round`, or `/loop-round <specific item>` to override the queue ordering.
See [`../docs/ADOPTING.md`](../docs/ADOPTING.md).

## Variants

**Constrained.** Scope a round without rewriting anything — pass the item as an
argument, or append one line to the pasted prompt:

```
This round: <the specific item>. Ignore the queue ordering.
```

**Audit-only.** Ship no features; measure whether a claim still holds. This is
`/loop-audit`, or
[`../plugins/loop/skills/loop-audit/SKILL.md`](../plugins/loop/skills/loop-audit/SKILL.md)
pasted the same way.

Run it when a project has been green for several rounds. Uninterrupted green is a
signal that the checks have stopped being adversarial, not that the work is
finished. This variant is what caught the 93.5% leak in
[`../docs/CASE_STUDY.md`](../docs/CASE_STUDY.md).

**Continuous.** With a scheduler — a cron trigger, `/loop`, a CI job — fire the same
prompt on an interval. The state file is what makes an unattended round safe: each
firing reads the same spine, and a round that goes wrong shows up in the writeup
instead of being silently absorbed.
