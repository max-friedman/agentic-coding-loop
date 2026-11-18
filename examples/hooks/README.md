# Example hooks and watchdog

Trimmed, generic versions of mechanisms from the project behind
[`LOOP.md`](../../LOOP.md) §F ([`docs/PARALLEL_LANES.md`](../../docs/PARALLEL_LANES.md)).
They are starting points, not a package: stdlib Python, no project paths, and every
threshold is a constant to change. Each file's docstring says which rule it enforces
and the incident behind it.

| file | kind | enforces | on its own error |
|---|---|---|---|
| [`admission_gate.py`](admission_gate.py) | PreToolUse hook on agent spawns | the lane cap, one lane per hotspot, disk and swap floors (§F *Sizing* 1, 2, 5) | fails **closed** |
| [`waiter_guard.py`](waiter_guard.py) | PreToolUse hook on shell commands | no wait loop whose `pgrep -f` pattern matches itself (§F *Sizing* 6) | fails open |
| [`watchdog.py`](watchdog.py) | scheduled OS job, outside any session | flags for low disk, an unattended job that keeps failing to log in, a silent coordinator, and the watchdog's own missed runs (§F *Watching*) | prints what it can |

The hooks follow Claude Code's hook contract: the tool call arrives as JSON on
stdin, and exit code 2 with a message on stderr blocks it. A blocked call always says
what to do instead. A wrong block is fixed in the hook, by pull request; an agent that
routes around a hook is the incident, not the hook (§F stop conditions).

What isn't here: the ledger writer for `admission_gate.py` (PostToolUse and
SubagentStop hooks that add and remove lanes), the merge queue, and the notification
wiring for `watchdog.py`. Those depend on the project's own merge script and
channels.
