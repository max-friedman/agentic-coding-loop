# Helper rules

A helper starts with no memory of the conversation, so this file is its rulebook. The spawn prompt carries the task,
the model and `Lane: <kind>; Hotspot: <area>`, and tells the helper to read this file.

Every rule here says why it exists. A rule with its reason can be applied to a case it doesn't name; a bare rule gets
followed to the letter or argued away. Keep the reason when you add a rule.

## Where and what

- One task per helper, in its own worktree, on its own branch from `origin/main`. Never stack pull requests: a
  squash merge of the base orphans the PR stacked on it. After a PR's third conflict, rebuild it fresh on main.
- **Your worktree goes in a managed dir** (`git_rules.worktree_dirs`: `.claude/worktrees/` or `../<repo>-worktrees/`),
  never anywhere else, and you remove it (`git worktree remove <path>`) once your PR is queued. Worktrees elsewhere are
  forgotten and fill the disk. `git_rules.py` blocks a helper's `git worktree add` outside them;
  `scripts/worktree_gc.py` removes finished ones anywhere.
- **Declare what only this machine can do.** When `spawn_gate.require_local_need` is on, a local helper that writes
  carries a line of its own, `Needs: local (<why>)`: a build, a device, a local service. Docs, scripts, tests and
  research run in cloud lanes instead, so the machine's one build slot serves only what needs it (queued helpers each
  wait a whole build behind the others). Add `, no build` when the helper won't use the build slot;
  `lanes.max_build_helpers` counts the ones that do.
- Never edit the live checkout: the running service loads it, so a stray edit is an unreviewed deploy. Set work aside
  with a WIP commit, not `git stash`: the stash stack is shared by every worktree, so a pop can take another session's
  changes (a tagged `git stash push -m <tag>`, restored by sha, is the only stash the hook allows).
- Never chain `git merge` with `add` and `commit`; check the merge result first: chained commands have pushed
  conflict markers.
- Kill only PIDs you started; never `pkill -f <pattern>`: a pattern also matches other sessions' processes.
- No secrets or personal values (ids, hostnames, emails, home paths) in code or docs: the repo may go public, and a
  secret in history stays there.
- **Never skip, stub or loosen a gate**: no `--no-verify`, no wrapper that fakes a pass, no env var that turns a check
  off on the command line, no landing override flag (those are the coordinator's, and logged). A skipped gate lets a
  broken build reach the people who use it, and the bypass looks exactly like a pass. `git_rules.py` blocks the
  common forms. If a gate is wrong, hand back with its output; the gate gets fixed in its own pull request.
- **A gate change is its own pull request.** A branch that changes a gate (a file that decides what runs, what is
  skipped or what passes: the landing scripts, the hooks, their settings, CI) together with product code is refused by
  `prelanding.py` unless its body says `Gate change: reviewed by <reviewer>`, naming a fresh reviewer agent or the owner,
  never you and never the coordinator. Split it out when you can.
- **Write each PR body to its own file** (`body<PR>.md` in your worktree, or `$TMPDIR/<PR>/body.md`), never a shared
  `pr_body.md`: two PRs sharing one once got each other's body. `gh_rules.py` warns on a shared path.
- **A check that picks where something runs fails closed.** When the list that says "this needs the strict target"
  can't be read, send everything to the strict target; never treat an unreadable list as empty, or the checks it
  names get skipped and read as passed.
- <Your project's own rules: design gates, devices, channels, shared files. Give each its reason.>

## The pull request and landing

- Run `python3 scripts/prelanding.py --body-only` as soon as the PR body is written: it checks the body's lines (gate
  change, review lines, `Intentional revert:`) in seconds, so a typo doesn't cost a whole run.
- Run `python3 scripts/prelanding.py` on your final head before handing back. A stale or badly resolved merge that
  undoes lines main gained is refused there; merge main again keeping both sides (or say `Intentional revert: <why>`).
- Your own work is never reviewed by you: user-visible results and gate changes get a fresh reviewer that did not
  write or steer the work.
- Land only through `scripts/land.sh <PR>` (or the queue that runs it); never `gh pr merge`: a second merge path skips
  the checks the first one runs.
- **No go-ahead needed** for this work; do it and report it: merge `origin/main` into your own branch; run prelanding
  and your named checks; regenerate your own fixtures and golden files; rerun a flaky check once; open a ready PR;
  queue it after prelanding passed; remove your own worktree and build output (the disk is the first thing a pile of
  helpers runs out of); start your own read-only reviewer.
  Hand back to the coordinator only for what this file reserves (an independent review line, a gate-change review)
  and <your project's reserved items: the owner's own device, a missing design>. Asking for a go-ahead on listed work
  idles the lane until someone answers.
- Stop every Monitor and background task you started (a leftover one wakes you again and re-sends your report), then
  send one report per PR: what changed, tests run, the pull request, what the coordinator must decide; no narrative.

## Finishing work

Adapted from Anthropic's
[prompting guide for Claude Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

- Don't stop while you still owe work: the task isn't done until its PR is queued (or you hand back for one of the
  reasons above).
- Work through ordinary obstacles yourself: an error, a timeout, a locked file, an empty result or a flaky tool means
  wait and retry, fix the request, or try another route.
- A deliberate blocker is different: a hook block, a file marked don't-touch, a safety rule. Leave it alone, say plainly
  what it blocked and why, and route around it safely (the block message says how), or hand back.
- None of this overrides asking before a risky or irreversible action (the Safety rules in the
  [PLAYBOOK](PLAYBOOK.md#coordinator-checklist)).

## Communicating clearly

Adapted from the same guide. Hand-backs and PR bodies are read by someone with none of your context, so:

- Key point first: the PR number, whether it's queued, and what the coordinator must decide.
- Self-contained: name the files, commands and results; don't refer to "the issue above" or your own earlier steps.
- Plain words. Don't invent terms or labels; use the names the code and docs already use.
- Write for a capable reader who wasn't there: short, specific, no narrative.
