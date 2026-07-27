# Adopting the loop in a project

Three ways in, depending on what you're running. All three produce the same
artifact: a `docs/plans/LOOP_STATE.md` your project owns.

---

## 1. Claude Code plugin (recommended)

```
/plugin marketplace add max-friedman/agentic-coding-loop
/plugin install loop@agentic-coding-loop
```

Then, in any project:

| command | what it does |
|---|---|
| `/loop-init` | Reads the project, drafts `docs/plans/LOOP_STATE.md`, adds the loop section to `CLAUDE.md`. Refuses to overwrite an existing state file. |
| `/loop-round` | Runs one round. Takes an optional item: `/loop-round tighten the retry test`. |
| `/loop-audit` | Ships nothing. Measures whether the project's strongest claim still holds. |
| `/loop-feedback` | Packages a learning about the loop as an upstream proposal. |

All four are `/`-invocable only — Claude won't start a round on its own, since a
round mutates the repo and costs a session.

**Updates.** The plugin is pinned to an explicit `version`, so pushes to `main`
don't reach you until a release. Pull one with:

```
/plugin marketplace update agentic-coding-loop
/plugin update loop
```

Pinning is deliberate. The loop's instructions execute inside your repo; you should
choose when they change. See [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## 2. Copy the templates

No plugin, no dependency, nothing to update. Good for a repo where you want the
loop's text under your own version control.

```bash
mkdir -p docs/plans
curl -o docs/plans/LOOP_STATE.md \
  https://raw.githubusercontent.com/max-friedman/agentic-coding-loop/main/templates/LOOP_STATE.template.md
```

Fill it in, add the pointer block to your `CLAUDE.md` / `AGENTS.md` (see
[`../templates/PROJECT_RULES.template.md`](../templates/PROJECT_RULES.template.md)),
and paste [`../prompts/ROUND.md`](../prompts/ROUND.md) to run a round.

The tradeoff: your copy diverges from upstream and you won't notice. Watch
`CHANGELOG.md` if you care.

---

## 3. Another agent or tool

The loop is plain markdown and assumes nothing about the harness. For Cursor,
Aider, Codex, a custom agent, or a CI job:

- **Persistent rules file** → the pointer block from
  [`../templates/PROJECT_RULES.template.md`](../templates/PROJECT_RULES.template.md),
  placed wherever that tool reads standing instructions.
- **Per-round prompt** → the body of
  [`../plugins/loop/skills/loop-round/SKILL.md`](../plugins/loop/skills/loop-round/SKILL.md),
  minus the YAML frontmatter. That file is the canonical round instructions; the
  Claude Code skill and the manual prompt are the same text.
- **Feedback** → open a Loop proposal issue by hand.

The only hard requirement is that the agent can read and write
`docs/plans/LOOP_STATE.md` in the same session.

---

## Pointing several projects at one loop

Each project keeps its **own** `LOOP_STATE.md`. Nothing is shared between them —
the state file is project memory, not global memory, and merging them would
produce a queue no single round can act on.

What is shared is the protocol. When a project learns something about the protocol
itself, that goes upstream via `/loop-feedback` and comes back to every project on
the next release. That is the only channel between them, and it runs through human
review by design.

---

## Verifying a change to the plugin

If you fork or edit the plugin:

```bash
claude plugin validate ./plugins/loop --strict
```

`--strict` turns unrecognized-field warnings into errors, which catches a
misspelled manifest key before it silently does nothing.
