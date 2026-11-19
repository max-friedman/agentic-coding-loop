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
| [`admission_gate.py`](admission_gate.py) | PreToolUse Agent, Task | a spawn past the lane caps, onto a held hotspot, under the disk floor or over the swap ceiling | fails **closed** |
| [`lane_ledger.py`](lane_ledger.py) | PostToolUse Agent, Task; SubagentStop | records a spawned lane in `.loop/lanes.json`, removes it when the subagent stops; entries past the TTL count as ended | fails open |
| [`spawn_gate.py`](spawn_gate.py) | PreToolUse Agent, Task, RemoteTrigger | opt-in: a spawn without a `model`, without the rules, or a cloud lane without the no-notify line | fails open |
| [`git_rules.py`](git_rules.py) | PreToolUse Bash | a bare `git stash`, `pop`, `clear`, an `apply`/`drop` naming no entry; `git merge` chained with `add`/`commit`. A tagged `git stash push -m <tag>` is allowed | fails open |
| [`gh_rules.py`](gh_rules.py) | PreToolUse Bash | a PR based on a branch other than main. **Opt-in** (`gh_rules.block_pr_merge`): `gh pr merge` on this repo (land with `scripts/land.sh`) | fails open |
| [`kill_rules.py`](kill_rules.py) | PreToolUse Bash | `pkill -f` and `killall <name>`; `kill <pid>` and an exact-name `pkill` are allowed | fails open |
| [`waiter_guard.py`](waiter_guard.py) | PreToolUse Bash | a wait loop whose `pgrep -f` pattern matches its own command line | fails open |
| [`live_checkout.py`](live_checkout.py) | PreToolUse Bash, Edit, Write | edits and git writes in `LOOP_LIVE_CHECKOUT`, the checkout a live service runs from (unset: nothing guarded) | fails **closed** |
| [`session_reminder.py`](session_reminder.py) | SessionStart compact, resume | prints the rebuild steps after a context loss | fails open |
| [`coordinator_stop.py`](coordinator_stop.py) | Stop | **opt-in** (`coordinator.require_checks`): the coordinator's turn ending with no event watcher running or no recurring check-in (`coordinator_session.py register` marks the coordinator) | fails open |
| [`watchdog.py`](watchdog.py) | not a hook: the OS scheduler, every 15 min | flags low disk, a job that keeps failing to log in, a silent coordinator, its own missed runs | prints what it can |

`_shell.py` (command parsing) and `_loop.py` (the knobs, the `Lane:` line, the ledger)
are shared helpers. Hooks follow Claude Code's contract: the call arrives as JSON on
stdin; exit 2 with a message on stderr blocks it, and the message says what to do
instead. Fail closed when the thing guarded can't be undone, open when it can.

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
| `resources.min_free_disk_gb` | 15 | block a spawn under this much free disk. `admission_gate` stays on by default; lower this if 15 GB is too much for your disk (a default is already cut to 10% of a small disk), or raise it for builds that need more |
| `resources.max_swap_used_gb` | 6 | block a spawn over this much swap in use |
| `resources.scale_to_machine` | true | lowers a default (not a value you set) on a smaller machine: disk floor to at most 10% of the disk, swap ceiling to at most 3/8 of RAM. The defaults come from a 16 GB laptop with a 228 GB disk, where nothing changes |
| `spawn_gate.require_model` | false | an Agent spawn must set `model` |
| `spawn_gate.require_rules` | false | a spawn prompt must carry one of `rules_markers` (read-only prompts and types are exempt) |
| `spawn_gate.rules_markers` | `[["helper-rules.md"], ["playbook", "prelanding"]]` | alternatives; each is a list of phrases that must all appear |
| `spawn_gate.require_no_notify` | false | a RemoteTrigger prompt must say it sends the owner no notifications |
| `coordinator.monitor_pattern` | `events\|watch` | a running background task matching it counts as the event watcher |
| `coordinator.checkin_pattern` | `check-?in\|checklist\|heartbeat` | a recurring session cron whose prompt matches counts as the check-in |
| `coordinator.monitor_command`, `checkin_command` | placeholders | the calls the Stop hook quotes when one is missing |
| `coordinator.cooldown_minutes` | 15 | each Stop condition blocks at most once per this many minutes |
| `gh_rules.block_pr_merge` | false | true: `gh_rules.py` blocks `gh pr merge` on this repo; PRs land with `scripts/land.sh`. A landing-process opinion, so off |
| `coordinator.require_checks` | false | true: `coordinator_stop.py` ends no coordinator turn without an event watcher and a recurring check-in. Assumes you run such a session, so off |
| `watchdog.min_free_disk_gb` | 12 | `watchdog.py` flags `disk_low` under this |

Environment: `LOOP_LIVE_CHECKOUT` (the guarded checkout), `LANE_LEDGER` (the ledger's
path, default `.loop/lanes.json`), `CLAUDE_PROJECT_DIR` (set by Claude Code; paths
are relative to it).

`bootstrap_kit.py` merges the kit's entries into an existing `.claude/settings.json` (never dropping yours; a backup is
kept) and refuses, naming why, one it can't merge.

A wrong block is fixed in the hook or the config, by pull request. An agent that routes
around a hook is the incident, not the hook.
