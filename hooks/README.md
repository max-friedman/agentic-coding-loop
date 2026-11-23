# Hooks

The Claude Code hooks that enforce the hard rules of the multi-agent project behind
[`LOOP.md`](../LOOP.md) §F, made generic. Stdlib Python, no project paths. This folder
is the only copy: `scripts/bootstrap_kit.py` installs every file here into a project's
`.claude/hooks/` (and `watchdog.py` into `scripts/`), and the kit's
[`settings.json`](../templates/project-kit/.claude/settings.json) wires them. Each hook
has a test (`test_<hook>.py`; the lane hooks share `test_hooks.py`). The tests stay here: this repo's gate runs
them, and `bootstrap_kit.py --test` runs them from here; the installer copies none into your project.

| hook | event | blocks or does | on its own error |
|---|---|---|---|
| [`admission_gate.py`](admission_gate.py) | PreToolUse Agent, Task | a spawn past the lane caps, onto a held hotspot, under the disk floor or over the swap ceiling. **Opt-in** (`finish_before_start.max_waiting_prs`): a feature spawn while too many PRs wait to land | fails **closed** |
| [`lane_ledger.py`](lane_ledger.py) | PostToolUse Agent, Task; SubagentStop | records a spawned lane in `.loop/lanes.json`, removes it when the subagent stops; entries past the TTL count as ended | fails open |
| [`spawn_gate.py`](spawn_gate.py) | PreToolUse Agent, Task, RemoteTrigger | opt-in: a spawn without a `model`, without the rules, a local writing helper without `Needs: local`, or a cloud lane without the no-notify line | fails open |
| [`git_rules.py`](git_rules.py) | PreToolUse Bash | a bare `git stash`, `pop`, `clear`, an `apply`/`drop` naming no entry; `git merge` chained with `add`/`commit`; a skipped gate (`--no-verify`, or a landing override flag from anyone but the coordinator); a helper's `git worktree add` outside the managed dirs. Warns on a gate-changing env prefix. A tagged `git stash push -m <tag>` is allowed | fails open |
| [`gh_rules.py`](gh_rules.py) | PreToolUse Bash | a PR based on a branch other than main. Warns on a PR body read from a shared scratch file. **Opt-in** (`gh_rules.block_pr_merge`): `gh pr merge` on this repo (land with `scripts/land.sh`) | fails open |
| [`wip_limit.py`](wip_limit.py) | PreToolUse Bash | `gh pr create` (not `--draft`) while `wip_limit.max_open_prs` open PRs already change product code | fails open |
| [`kill_rules.py`](kill_rules.py) | PreToolUse Bash | `pkill -f` and `killall <name>`; `kill <pid>` and an exact-name `pkill` are allowed | fails open |
| [`waiter_guard.py`](waiter_guard.py) | PreToolUse Bash | a wait loop whose `pgrep -f` pattern matches its own command line | fails open |
| [`live_checkout.py`](live_checkout.py) | PreToolUse Bash, Edit, Write | edits and git writes in `LOOP_LIVE_CHECKOUT`, the checkout a live service runs from (unset: nothing guarded) | fails **closed** |
| [`session_reminder.py`](session_reminder.py) | SessionStart compact, resume | prints the rebuild steps after a context loss | fails open |
| [`coordinator_digest.py`](coordinator_digest.py) | UserPromptSubmit | adds a few lines of facts to each coordinator turn: running lanes against the floor (from the ledger only), the heartbeat and the watchdog's open flags, the release pipeline (running or paused, the build users run), the open rows of the assumptions log | fails open |
| [`coordinator_stop.py`](coordinator_stop.py) | Stop | **opt-in** (`coordinator.require_checks`): the coordinator's turn ending with no quiet watch running or no recurring check-in (`coordinator_session.py register` marks the coordinator) | fails open |
| [`watchdog.py`](watchdog.py) | not a hook: the OS scheduler, every 15 min | flags low disk, a job that keeps failing to log in, a silent coordinator, its own missed runs, no lanes for 30 min, ready work or not, and `COORDINATOR STALLED` when the coordinator's last turn is that old too (`lanes_idle`), a private rule note newer than the written rules (`rule_drift`), a paused release pipeline (`release_paused`, then `release_stuck` to the human) and a build users run that lacks old shipped changes (`build_stale`); writes `.loop/watchdog_flags.json` | prints what it can |

`_shell.py` (command parsing) and `_loop.py` (the knobs, the `Lane:` line, the ledger)
are shared helpers. Hooks follow Claude Code's contract: the call arrives as JSON on
stdin; exit 2 with a message on stderr blocks it, and the message says what it
blocked, why the rule exists, and what to do instead, so the agent can tell a
deliberate block from an obstacle to work around. Fail closed when the thing
guarded can't be undone, open when it can.

## The lane ledger

A spawn prompt names its lane in one line: `Lane: feature; Hotspot: checkout,api`.
`admission_gate.py` counts the running lanes in `.loop/lanes.json` before a spawn;
`lane_ledger.py` writes that file. PostToolUse on the Agent tool adds the lane (a
background spawn returns at once; a foreground one has already finished and isn't
added). SubagentStop removes it by the agent's id, or, when the spawn's response
carried no id, the oldest id-less lane of the same session. A lane whose stop never
arrives (a crash, a killed session) counts as ended after `lanes.stale_hours`.
`python3 .claude/hooks/lane_ledger.py list` shows the ledger; `end <id>` and `clear`
fix it by hand.

## Knobs: `.loop/config.json`

Every knob has a default, so a project with no config file gets working gates;
`bootstrap_kit.py` writes the file with the defaults. Set only what you change: the
file is laid over the defaults (`_loop.DEFAULTS`). `.loop/` is git-ignored, so the
values are per machine. `LOOP_CONFIG` points at another file.

| knob | default | what it does |
|---|---|---|
| `lanes.total` | 5 | running lanes at most, every kind together |
| `lanes.caps` | feature 4, bug 1, process 1 | per kind; a kind not listed has cap 0 |
| `lanes.default_kind` | `feature` | the kind of a spawn whose prompt has no `Lane:` line |
| `lanes.require_lane_line` | false | true: a spawn with no `Lane:` line is blocked, not defaulted with a warning |
| `lanes.stale_hours` | 6 | a ledger entry this old counts as ended |
| `lanes.read_only_types` | Explore, Plan, claude-code-guide, web-fetch | agent types never counted or gated |
| `lanes.max_build_helpers` | 0 (off) | above 0: a spawn whose prompt has `Needs: local` without `no build` is refused while this many running lanes already use the build slot (the ledger's `build` flag); more only queue behind one build |
| `lanes.override_file`, `override_ceiling` | `.loop/lane_override.json`; 4 | an owner-approved, expiring raise of one kind's cap: `{"kind": "bug", "max": 3, "until": <epoch>, "why": "..."}` lifts that kind's cap to `max` (at most the ceiling) until it expires. A missing, unreadable or expired file means the normal cap; `lanes.total` still holds. Only the owner writes it |
| `resources.min_free_disk_gb` | 15 | block a spawn under this much free disk. `admission_gate` stays on by default; lower this if 15 GB is too much for your disk (a default is already cut to 10% of a small disk), or raise it for builds that need more |
| `resources.max_swap_used_gb` | 6 | block a spawn over this much swap in use |
| `resources.scale_to_machine` | true | lowers a default (not a value you set) on a smaller machine: disk floor to at most 10% of the disk, swap ceiling to at most 3/8 of RAM. The defaults come from a 16 GB laptop with a 228 GB disk, where nothing changes |
| `spawn_gate.require_model` | false | an Agent spawn must set `model` |
| `spawn_gate.require_rules` | false | a spawn prompt must carry one of `rules_markers` (read-only prompts and types are exempt) |
| `spawn_gate.rules_markers` | `[["helper-rules.md"], ["playbook", "prelanding"]]` | alternatives; each is a list of phrases that must all appear |
| `spawn_gate.require_no_notify` | false | a RemoteTrigger prompt must say it sends the owner no notifications |
| `spawn_gate.require_local_need` | false | cloud first: a local Agent spawn that writes must carry a line of its own `Needs: local (<why>)`, else it is refused with `spawn_gate.cloud_hint` (read-only prompts and types, forks, `isolation: remote` and spawns from a cloud session are exempt) |
| `spawn_gate.local_exempt_env` | `["CLAUDE_CODE_REMOTE"]` | env vars that, truthy, mean the spawn is already in the cloud |
| `coordinator.monitor_pattern` | `events\|watch` | a running background task matching it counts as the quiet watch |
| `coordinator.checkin_pattern` | `check-?in\|checklist\|heartbeat` | a recurring session cron whose prompt matches counts as the check-in |
| `coordinator.monitor_command`, `checkin_command` | placeholders | the calls the Stop hook quotes when one is missing |
| `coordinator.cooldown_minutes` | 15 | each Stop condition blocks at most once per this many minutes |
| `gh_rules.block_pr_merge` | false | true: `gh_rules.py` blocks `gh pr merge` on this repo; PRs land with `scripts/land.sh`. A landing-process opinion, so off |
| `coordinator.require_checks` | false | true: `coordinator_stop.py` ends no coordinator turn without a quiet watch and a recurring check-in. Assumes you run such a session, so off |
| `watchdog.min_free_disk_gb` | 12 | `watchdog.py` flags `disk_low` under this |
| `watchdog.cleanup_command`, `auto_cleanup_gb` | empty (off); 15 | the command the watchdog runs itself, once per low-disk episode, when free disk falls under `auto_cleanup_gb` (your spawn floor); `disk_low` opens only if the disk is still under its floor after it. A run made between the floor and that level is followed by one more if the disk then falls under the floor |
| `watchdog.lanes_idle_minutes` | 30 | `lanes_idle`: no lane in the ledger this long, ready work or not; `COORDINATOR STALLED` when the coordinator's last turn (`.loop/coordinator_stop.json`) is this old too |
| `watchdog.ready_file`, `ready_pattern` | `docs/ROADMAP.md`, a table cell `Ready` | where ready work is listed, and the line that is one item; `lanes_idle`'s detail counts them, or says the statuses are stale when there are none |
| `release.paused_file`, `published_file` | empty (off) | the release pipeline's files: `{"at", "why"}` while it is paused, and `{"commit", "published", "version"}` naming the build users run. For an app, say, the store or sideload build; for a service, the deployed one |
| `release.good_ref`, `shipped_paths`, `not_shipped_pattern` | `origin/main`; every path; tests | what the next build is cut from, and which changed files reach users through it |
| `release.resume_command` | empty | the command that resumes the pipeline, quoted in the flag and the digest |
| `release.stuck_hours`, `stale_days` | 24; 2 | `release_paused` this long is `release_stuck` (the human at once); `build_stale` when a shipped change this old is missing from the published build |
| `watchdog.rule_notes_dir` | empty (off) | the coordinator's private notes (its memory directory); `rule_drift` flags a note matching `rule_note_pattern` (`type: feedback`) changed within `rule_drift_hours` (24) after the last commit to `rule_docs` (`docs/process`, `CLAUDE.md`) |
| `git_rules.block_no_verify` | true | block `git commit --no-verify`/`-n` and `git push --no-verify`: never skip a gate; fix it, or fix the gate in its own PR |
| `git_rules.landers`, `coordinator_only_flags` | `land.sh`, `prelanding.py`; `--no-prelanding`, `--skip-checks` | override flags of the landing scripts that only the registered coordinator may pass |
| `git_rules.gate_env` | `PRELANDING_CHECKS`, `WIP_LIMIT` | env vars that change a gate: a command prefixed with one (or with SKIP/NO_VERIFY/BYPASS in a name) warns |
| `git_rules.worktree_dirs` | `.claude/worktrees`, `../{repo}-worktrees` | where worktrees go (relative to the project; `{repo}` is its folder name). Empty turns the rule off |
| `git_rules.block_stray_worktree` | true | a helper's `git worktree add` outside them (and `$TMPDIR`) is blocked; anyone else's warns |
| `gh_rules.warn_shared_body_file` | true | warn on `--body-file` from a shared path; use `body<PR>.md` in your worktree or `$TMPDIR/<PR>/body.md` |
| `wip_limit.max_open_prs` | 7 | `gh pr create` blocked at this many open, non-draft product PRs; 0 is off. `WIP_LIMIT` overrides it on one machine |
| `wip_limit.product_paths`, `exempt_paths`, `exempt_branches` | all paths; `docs/`, `tests/`, `test/` and `*.md`; `revert-` | what counts as product code, and what never counts |
| `finish_before_start.max_waiting_prs` | 0 (off) | above 0: a feature spawn is refused while more open, non-draft PRs wait; bug and process lanes pass |
| `digest.assumptions_log` | `docs/process/assumptions-log.md` | the digest counts its rows whose last cell starts with `open` |
| `digest.min_lanes` | 2 | the digest says "under the floor" below this many running lanes |
| `prelanding.checks` | none | the commands `scripts/prelanding.py` runs; it fails when none is set |
| `prelanding.gate_paths`, `code_paths` | the landing scripts, hooks, settings, git hooks, CI; empty (off) | a branch changing a gate and product code needs `Gate change: reviewed by <reviewer>` naming someone independent |
| `prelanding.not_independent` | coordinator, author, self, me, myself | reviewer names that don't count |
| `prelanding.stale_revert` | true | refuse a branch that undoes lines main gained since it forked (`scripts/stale_revert.py`) |
| `prelanding.review_lines` | none | rules `{"name", "when_body", "when_paths"}`: a PR whose body matches `when_body` or that changes `when_paths` needs `<name>: OK (<reviewer>, ...)` from someone independent (exit 13); an auto-queue skips it until then |
| `prelanding.max_throwaways` | 2 | scratch worktrees prelanding may hold at once (`scripts/throwaway_worktrees.py`); a run waits for a place before it makes its checkout |
| `prelanding.batch_max`, `alone_paths`, `env_marker` | 6; none; `ENVIRONMENT, not your PR` | `prelanding.py --batch`: PRs per run; paths whose PRs always run alone (a gate always does); a string a check prints when the failure is the machine's, which blames nobody and isn't bisected |
| `worktree_gc.recreatable_prefixes`, `recreatable_idle_minutes` | none; 10 | a detached, clean worktree whose directory starts with one of these goes after this many idle minutes: its owner made it for a waiting work item and makes it again when the item builds |
| `cutover.when_body`, `when_paths` | `^\W*Cutover:` (on by default); none | what makes a PR a cutover for `scripts/cutover_gate.py` (prelanding exit 14): refused while the pipeline is paused, when a cutover that changes no shipped code would switch on code the build users run lacks, and without a recent whole-suite pass |
| `cutover.passes_file`, `pass_max_age_hours`, `known_red_file`, `suite_command` | none; 24; none; none | the whole-suite runs your runner appends (`{"at", "commit", "full", "failed", "failures"}`), how recent a pass on the cutover's base must be, failures that don't count, and the command the refusal quotes. No passes file: a cutover is refused |
| `review_land.worktree_dir`, `after` | `../{repo}-worktrees`; `scripts/land.sh {pr}` | where `scripts/review_land.py` makes its `review-<PR>` worktree, and what it runs once prelanding passes (your queue's add command, if you run one) |
| `worktree_gc.idle_hours` | 6 | `scripts/worktree_gc.py` removes a clean, finished worktree idle this long, wherever it lives |
| `waiter_reaper.max_age_hours`, `protected` | 6; none | `scripts/waiter_reaper.py` kills a Claude Code waiter shell older than this, except commands naming a protected string |

Example: an app whose pipeline builds main about hourly and publishes the build its users install. The pipeline
writes `.loop/release/paused.json` when a crash check stops it and `.loop/release/latest.json` each time it
publishes; the suite runner appends its runs to `.loop/suite_runs.jsonl`; `config/features.json` switches features on.

```json
{
  "release": {"paused_file": ".loop/release/paused.json", "published_file": ".loop/release/latest.json",
              "shipped_paths": ["app/", "shared/"], "resume_command": "scripts/release.py --resume"},
  "cutover": {"when_paths": ["config/features.json"], "passes_file": ".loop/suite_runs.jsonl",
              "suite_command": "scripts/suite.sh --full"},
  "prelanding": {"review_lines": [{"name": "Fidelity", "when_body": "^Cutover:", "when_paths": ["app/ui/"]}]}
}
```

Environment: `LOOP_LIVE_CHECKOUT` (the guarded checkout), `LANE_LEDGER` (the ledger's
path, default `.loop/lanes.json`), `CLAUDE_PROJECT_DIR` (set by Claude Code; paths
are relative to it), `LOOP_GH_BIN` (the `gh` the hooks call; tests point it at a fake).

`bootstrap_kit.py` merges the kit's entries into an existing `.claude/settings.json` (never dropping yours; a backup is
kept) and refuses, naming why, one it can't merge.

A wrong block is fixed in the hook or the config, by pull request. An agent that routes
around a hook is the incident, not the hook.
