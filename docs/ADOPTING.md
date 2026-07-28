# Adopting the loop in a project

Three ways in. All produce the same artifact: a `docs/plans/LOOP_STATE.md` the
target project owns.

---

## 1. Any agent, any harness — read one file

The loop assumes nothing about the harness. Point the agent at:

```
https://raw.githubusercontent.com/max-friedman/agentic-coding-loop/main/LOOP.md
```

`LOOP.md` is self-contained: round steps, hard rules, ending states, the audit
round, bootstrap, feedback, and continuous operation. Nothing else needs fetching.

Two placements, and both matter:

- **Standing rules** (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`, whatever the tool
  reads every session) → the pointer block from
  [`../templates/PROJECT_RULES.template.md`](../templates/PROJECT_RULES.template.md).
  This is what makes a cold agent find the state file at all.
- **Per-round prompt** → "Fetch `LOOP.md` and run §1–§7. Round budget: N."

The only hard requirement is that the agent can read and write
`docs/plans/LOOP_STATE.md` in the same session.

---

## 2. Claude Code plugin

```
/plugin marketplace add max-friedman/agentic-coding-loop
/plugin install loop@agentic-coding-loop
```

| skill | what it does |
|---|---|
| `loop-init` | Bootstraps the state file from the real project. Refuses to overwrite. |
| `loop-run` | Repeated rounds until a stop condition fires. Optional budget: `loop-run 5`. |
| `loop-round` | Exactly one round. Optional item: `loop-round tighten the retry test`. |
| `loop-audit` | Ships nothing. Measures whether a claim still holds. |
| `loop-feedback` | Files a proposal upstream about the protocol. |

Each skill inlines `LOOP.md` at load time via
`` !`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"` ``, so the protocol has exactly one copy
and a skill cannot drift from it.

All five carry `when_to_use` triggers and are model-invocable — an agent picks the
right one from intent ("run the loop", "does that claim still hold") without a human
typing a slash command.

**Domain plugins are separate, optional installs** — layers on top of these same
five skills, for projects that fit a specific domain. Currently:

```
/plugin install loop-ux-roast@agentic-coding-loop
```

| skill | what it does |
|---|---|
| `loop-init-ux` | Bootstraps the state file with `Layers: core + ux-roast` declared, CUJ-framed queue, coverage map by surface. |
| `loop-round-ux` | One round using the blind-critic/context-aware-verifier split, maker+checker worktree fixes, and tiered ship policy from `domains/ux-roast/DOMAIN.md`. |

Install this only if the target project is a user-facing product where
"improvement" means UX quality — see the Domains table in [`../llms.txt`](../llms.txt)
for the fit criteria. A domain's skills inline both `LOOP.md` and its own
`DOMAIN.md`, so core and domain stay separately versioned and neither can drift
from the other.

**Updates** are pinned to an explicit `version` per plugin, so pushes to `main` do
not reach you until a release:

```
/plugin marketplace update agentic-coding-loop
/plugin update loop
/plugin update loop-ux-roast
```

Pinning is deliberate. These instructions execute inside your repo; you choose when
they change. See [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## 3. Copy the templates

No dependency, nothing to update, the text under your own version control.

```bash
mkdir -p docs/plans
curl -o docs/plans/LOOP_STATE.md \
  https://raw.githubusercontent.com/max-friedman/agentic-coding-loop/main/templates/LOOP_STATE.template.md
curl -o LOOP.md \
  https://raw.githubusercontent.com/max-friedman/agentic-coding-loop/main/LOOP.md
```

The tradeoff: your copy diverges from upstream and you will not notice. Watch
`CHANGELOG.md` if that matters.

---

## Running rounds repeatedly

A round is the unit of work, not the job. `LOOP.md` §D defines the round boundary,
the context-hygiene rule between rounds, the stop conditions, and the extra
constraints for unattended runs.

| mechanism | fit |
|---|---|
| `loop-run` skill | Repeated rounds in one session, with a budget. Supervised. |
| Claude Code `/loop` bundled skill | Interval runs inside a session. |
| Claude Code scheduled tasks | Recurring unattended runs on a repository. |
| GitHub Actions `schedule` | Fully unattended, one pull request per firing. Template: [`../templates/loop-workflow.template.yml`](../templates/loop-workflow.template.yml). |

Cadence should track how fast the project's ground truth changes. Each firing costs
a session and produces a diff someone must read — prefer fewer, larger-signal
rounds.

---

## Pointing several projects at one loop

Each project keeps its **own** `LOOP_STATE.md`. Nothing is shared between them —
the state file is project memory, not global memory, and merging them would produce
a queue no single round can act on.

What is shared is the protocol. When a project learns something about the protocol
itself, that goes upstream via `loop-feedback` and returns to every project on the
next release. That is the only channel between them, and it runs through human
review by design.

---

## Verifying a change to the plugin

```bash
claude plugin validate . --strict
```

`--strict` turns unrecognized-field warnings into errors, catching a misspelled
manifest key before it silently does nothing. To check discovery end to end, install
from a local path and confirm all five skills appear:

```bash
claude plugin marketplace add /absolute/path/to/agentic-coding-loop
claude plugin install loop@agentic-coding-loop
claude plugin list
```
