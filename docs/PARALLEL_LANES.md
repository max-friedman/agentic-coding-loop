# Running many agents at once: field notes

`LOOP.md` was written for one agent, one item, one round. This page is about the
layer above that: one coordinating session running several agents in parallel on the
same codebase, every day, for weeks, with one human who wants to be asked as little
as possible.

**The rules are in the protocol; this page keeps the scars.** What generalized
became [`LOOP.md`](../LOOP.md) §F *Parallel lanes*, two hard rules (*a check that ran
nothing is no verdict*, *remove what you created*), §B step 6a, §D's hand-off budget
and spec check, the `## Decided, not asked` section, and
[principles 13–15](PRINCIPLES.md#13-a-check-that-ran-nothing-is-no-verdict). They
were accepted by the owner directly in 0.13.0, not through the review rubric. This
page is the evidence for them, plus what stayed project-specific. Read it when a
rule there seems wrong.

**Where it comes from.** One project, one author: a mobile app with a server-side
component, built from late September to mid November 2026 by Claude Code sessions —
one coordinator and two to five helper agents at a time, about 1,650 merged pull
requests, one 16 GB machine, a small pool of test devices. Every number below is from
that project's own logs and retros. One project is an anecdote with good bookkeeping;
treat it as that.

---

## The one thing it taught

**Writing code got cheap. Landing it didn't.**

Every agent added past the first few produced pull requests faster than they could be
checked, merged and proven on main. Almost every rule below exists to keep the path
*onto* main fast and safe, not to make agents write faster. If you remember one
sentence from this page, make it that one: size everything — lanes, models, cadence —
to the landing path, not to the appetite for work.

---

## 1. Roles

The roles — owner, one coordinator, lanes, at most one bug lane and one process
lane — are in §F. What the table there doesn't show:

**One voice to the owner.** Helpers report to the coordinator, never to the human.
Cloud-hosted helpers are told explicitly, in every prompt, not to send
notifications.

**Pick the model by risk, and say so on every spawn.** The strongest model for the
coordinator, feature work and anything on a risky path; a cheaper one for tests,
docs, reruns and mechanical merge conflicts; the cheapest for summaries. A spawn with
no model named is refused by a hook (§7).

---

## 2. Lanes and how many

**The limit is the slowest shared thing.** RAM, the single build slot, the device
pool, the landing queue. Past that point, more agents only queue, and queued agents
still cost tokens.

| lesson | the failure it prevents | evidence |
|---|---|---|
| **A hard cap, enforced by a hook, counted before every spawn.** | The coordinator over-spawning while busy. | One evening about 18 helpers were running against a stated limit of five. Load average hit 51 and the live service starved. A memory note had said "five"; it did not stop anything. A hook now refuses the sixth. |
| **One open PR or running helper per hotspot.** | Every merge forcing every other PR in the same area to redo conflicts, screenshots and fixtures. | About eight PRs open at once in the same few screens and the wire protocol; each merge made the rest redo work. |
| **Split shared append-only files by area.** | Conflicts on files everyone adds a line to: test-scenario lists, copy tables, feature flags, the roadmap. | Two PRs adding neighbouring lines to one list conflicted three times each. Per-area files (each area registers itself) ended it; a test now refuses additions to the old shared files. |
| **Add lanes by the landing-queue signal, not by appetite.** | Lanes producing PRs the landing path can't absorb. | Add a lane while three or fewer ready PRs wait; hold when the queue grows. |
| **Finish before starting.** | New PRs adding only conflicts and rechecks while ten wait to land. | With about ten PRs queued and each landing taking ~45 minutes, the owner asked why anything new was being built. Now: above ~5 queued, lanes work on what unblocks landing. |
| **Route by where the work must build.** | Cloud capacity idle while the one local build slot queues. | Cloud sessions sat unused for ten days while the build slot queued ~29 hours of waits a day. Anything that needs no device or local build now goes to a cloud lane. |
| **Fewer lanes can be more work.** | Assuming throughput scales with agents. | Going from four to two feature lanes, with conflicts removed, cut cost per merged slice from 400–700k tokens to 215–325k with no red main. |
| **Check added capacity is used.** | A new device or shard silently doing nothing. | Three times a newly added device or test shard sat idle or reported nothing, and it read as a pass. A shard with no report is now an alarm. |

**Sequence work that touches the same file.** Disjoint folders per lane are the main
conflict guard; where two slices must touch one file, the one the other depends on
lands first.

---

## 3. Spawning and steering helpers

**A helper's prompt is its whole world.** It starts with no memory of the
conversation.

- **Rules live in one file the prompt points at.** Repeating every rule inline in
  every prompt was correct but long; a pointer to a rules file is shorter, and a hook
  refuses a spawn whose prompt carries neither.
- **Every prompt names its lane and hotspot** in a fixed line, so the cap hook can
  classify it without guessing.
- **Don't ask for a go-ahead on authorized work.** Helpers asking "want me to land
  it?" was the single most repeated complaint in the first week.
- **Run the cheap gate before handing back** (§5, prelanding).
- **Wait for your own landing in the same turn.** A helper that backgrounded its
  landing and ended its turn never came back; the PR sat as a draft.
- **Stop every watcher before the final report.** A leftover background monitor made
  one helper re-send its report three times.
- **Reports are data, not instructions.** A helper relayed "the owner said to change
  the priority order" after being refused. The coordinator refused too, and did it
  only on the owner's own words. *Permission is never laundered through another
  agent.*

### Long chains and context hand-offs

§D's hand-off budget came from here.

- Twice in one night helpers ran out of context mid-chain; the hand-offs worked only
  because each kept a chain state file from its first step.
- Resuming the same helper for a milestone's next slice saves re-learning, until
  about 400k tokens of context; one helper reached about 700k before the budget
  existed.
- **The coordinator's own context will be compacted.** It keeps a file memory
  (decisions, lessons, what's in flight, open questions for the owner), writes each
  entry the moment it happens, and has a written rebuild procedure for after a
  context loss. A session-start hook prints that procedure on resume.

---

## 4. One way onto main

**One script is the only way to merge.** It merges main into the PR, runs the scoped
checks, merges under a lock shared with every other writer, and deploys. The
platform's merge button and the CLI merge command are blocked by a hook.

### Shift left: the same checks, before the queue

About one landing in five failed, and half of those failed on checks that need no
device: unit tests, script tests, a conflict with main. Each failure cost another
trip through the build slot and the queue. **Prelanding** runs the landing's own
non-device checks on the branch merged with current main, in a throwaway worktree,
and records the pass under the head commit. The landing script refuses a head with no
recorded pass.

### A queue, not hand-written waiters

The coordinator used to chain landings with ad-hoc shell waiters. They failed in
every way a waiter can:

- a process-match pattern matched the waiter's own command line, so it spun forever;
- a waiter keyed on "output file non-empty" fired immediately;
- two landers for one PR collided in the same scratch directory;
- a helper's pattern-kill (`pkill -f`) took out the coordinator's waiters.

A single landing-queue worker replaced them: one entry per PR, fresh checkout per
landing, waits for the nightly window and for conflicting landings, one automatic
retry of a device-only failure, every state change logged. **A waiter keys on the real
end signal** — the result file exists *and* the process is gone, or the PR's merge
commit is set — never on a quiet log.

### Batching, and why it keeps getting blocked

With one build slot and one device pool, running each PR alone (10–40 minutes each)
was the bottleneck. A merge train lands up to four compatible PRs as one build and one
device run on the merged result, and bisects a red batch by halves. This is the
bors-style shape rather than speculative parallel pipelines, because speculative runs
need spare CI capacity and this project had none: a green batch of N costs one run, a
red one about 2·log₂N extra.

Batching existed, worked, and still didn't help for weeks. The reasons are worth
writing down because each is a rule that was correct on its own:

| what kept PRs out of batches | why it existed | what changed |
|---|---|---|
| Any PR carrying an override (e.g. "land despite known-red main") ran alone. | An approval covers only the PRs it names. | PRs carrying the *same* approval may batch together. |
| Two PRs in the same hotspot never batched. | The hotspot rule keeps *open* PRs from fighting over lines. | Same area may batch when no file is in both and the merge is clean: the build and tests run on the merged tree, so a bad combination fails like any red batch. |
| ~40 of every ~45 minutes was non-device checks. | — | Batching saves only the device share; the rest is cut by build caching and by rechecking only what main's new commits touched. |
| PRs failed at landing on device scenarios never run against current main. | — | Builders now run their named scenarios on merged main before reporting ready. |

The owner had to ask twice why batching kept stopping. **Batching is the default; a
rule that keeps PRs apart needs a reason the owner agreed to.**

### Main moves; rechecks cost

At about ten merges an hour, every merge sent every queued PR back to re-merge,
rebuild and recheck — one protocol PR re-merged three times. What helped: recheck only
the checks whose inputs main's new commits touched, docs never count, batch small
PRs, and hold other merges while a broad change (build files, protocol) is in its
device run.

### Stacking, conflicts and stale merges

- **Never stack PRs on squash-merging repositories.** When the base squash-merges,
  its branch is deleted, the stacked PR auto-closes, and its reopened copy conflicts
  with the squashed version of its own parent. A hook refuses a PR whose base isn't
  main.
- **When a chain of dependent slices exists anyway, land it as one combined PR** from
  the tip branch, not as a sequence of re-based PRs. Several stacked PRs that each
  appended to the same registry file conflicted with each other at every step.
- **After a PR's third conflict, rebuild it fresh on main** rather than merging main
  in a fourth time.
- **Never chain `git merge` with `add` and `commit` in one command.** Conflict markers
  reached a pushed branch four times this way, each from a prompt that lacked the
  rule. A hook now refuses the chain.
- **Resolve conflicts with a merge commit, never a force-push.** One helper tried;
  the hook caught it.
- **A stale merge can silently revert merged work.** One PR's bad "merge main"
  resolution quietly undid another PR that had landed the same day. A check now
  refuses a PR that, against current main, is missing several significant lines main
  added to a file the PR also changes — unless the body says the revert is intended.

### Never a bare `git stash`

The stash stack is shared by every worktree of a repository. With many sessions in
many worktrees, `git stash pop` can take another session's work. Set work aside with
a WIP commit. A hook refuses a bare stash.

---

## 5. Red main, and false reds

**Fast checks before merge, device checks after merge in batches, the whole suite
once a night.** Gating every merge on the full suite held builds for hours; the
lightweight split kept main moving and still caught regressions within a day.

**Red main holds only what it could affect.** While main fails scenarios, a feature
PR that could touch a red scenario waits; fixes go through. Scoping by an area map
(which files can break which scenarios) stopped three environmental reds from holding
unrelated PRs for hours.

**Known red doesn't block** — only failures main doesn't already have — with
narrowings from published practice: a known-red failure still blocks when the PR
touches that scenario's area, when the failure is generic (timeout, crash), or when
the list is long or old enough that "known" has stopped meaning anything.

**Most reds were false.** Fourteen nightlies in a row came back red, and only about 2
of ~15 fixes written for nightly reds were real bugs. The rest were flakes, timing,
environment or tests that depended on today's date. What helped:

| rule | the failure it prevents |
|---|---|
| **A check that ran nothing is no verdict.** Not red, not green: "not run". | A build job holding the slot through the night meant the device stage never started, and main was marked red with no failing scenario — which blocked every build-touching PR. |
| **Each red gets one targeted retry, in idle time, before it counts.** No automatic full-suite rerun. | A full rerun holding the devices until late morning. |
| **Red twice running with no fix in between → quarantine, with an owner and an issue.** | A flaky test holding every PR in its area for a day. |
| **A red non-device check heals when a later landing runs and passes it** — unless that PR weakens tests. | One flaky script test holding every server PR until the next nightly. |
| **Environment failures are held separately** and re-queued when an environment probe passes, with a budget. | A broken toolchain read as "your PR failed" and sent back to the helper. |
| **A platform outage is infrastructure, not a PR failure.** | An API outage sending a batch of healthy PRs back to their helpers. |
| **Revert only a confirmed culprit**: fails 2 of 3 on it, passes 2 of 2 on its parent. | Two good PRs reverted for flaky scenarios, an hour or two each. |
| **No test compares a hard-coded date with the real clock.** | One date-dependent test failed three landings; two device scenarios failed only after 22:00. |
| **Live-service tests ask questions that need no tools.** | One open-ended live question made the agent loop for two minutes and held four PRs for three hours. |

**Silence is not success.** The nightly skipped its device suite five nights running
before anyone noticed, then twice more after a pause while ~25 merges piled up
untested. Now a device stage that doesn't run is a loud alarm, a nightly has a hard
end and a stall detector, and the morning check confirms it really ran. This is the
same rule the protocol applies to scheduled reviewers: a green status is not evidence
of work.

**Ship main often; roll forward, never back.** A build of main reached the owner's
phone about hourly after the fast checks. A bad build is fixed by shipping a newer
one; two crashes within an hour of an install pause the train.

---

## 6. A small machine

| lesson | evidence |
|---|---|
| **One build at a time.** | Parallel builds on a 16 GB machine ran it out of memory and crashed every session at once. A memory-gated second slot was tried; its gate missed swap filling up and the emulator was killed five times. It's off by default. |
| **Start a lane only with free memory to spare.** | ≥ 3 GB free and the OS's memory-pressure reading healthy. |
| **Devices only through one lock**, with a separate lock for the owner's own device and one for live-service runs, always taken in the same order. | Improvised runners that each held one lock and waited on another deadlocked twice; the second stalled everything for 6.5 hours overnight, unnoticed. |
| **A lock held long with no progress is an alarm.** | 45 minutes with no new output = stuck. |
| **Kill only PIDs you started.** | A helper's `pkill -f` killed the coordinator's waiters. A hook refuses pattern kills. |
| **Never delete a directory a process still runs from.** | Deleting a lander's checkout mid-run crashed a service restart that ran from it. A hook refuses it. |
| **Cold-restart long-lived emulators daily.** | A four-day-old one had become sluggish. |

### Disk hygiene

The disk filled more often than anything else broke.

- **Worktrees:** 48 GB of finished helpers' worktrees filled the disk in the first
  week. Remove a worktree when its PR merges; sweep orphans on a schedule.
- **Leaked temporary homes:** each device test created a throwaway home directory of
  ~1.5 GB whose cleanup ran in an exit hook that a process `exec` skipped. One night of
  the full suite left about 80 GB and took the disk to zero twice, killing a landing.
  The sweeper ran every six hours — too slow for a leak that fast. The leak was
  fixed; the follow-up makes cleanup explicit rather than exit-hook-based and moves
  the sweep to minutes.
- **Check the disk before the nightly**, not after it fails. One nightly skipped its
  devices on low disk.

---

## 7. Hooks enforce the hard rules

**Instructions are advice; hooks are guarantees.** The hard rules lived first in the
project's rules file, which agents read and sometimes followed. Every rule that must
hold with zero exceptions now has a pre-tool-use hook:

| hook refuses | why it exists | on its own error |
|---|---|---|
| Edits and git writes in the checkout the live service runs from | An edit there is an unreviewed deploy. Each session works in its own worktree and lands by PR. | **fails closed** |
| Device commands outside the device lock | Two agents driving one device, and the deadlocks above. | **fails closed** |
| A spawn past the lane cap, or onto a hotspot a running helper holds | The 18-helper evening. | **fails closed** |
| A message to any chat channel not on the testing allowlist | Tests posting where real people read. | fails open |
| A bare `git stash`, a merge chained with commit, a non-main PR base, the merge button | The stash, conflict-marker and stacking incidents above. | fails open |
| Pattern kills, deleting a running lander's directory | The waiter and restart incidents above. | fails open |
| A spawn with no model, or whose prompt lacks the rules pointer | Helpers starting without the rules or on the wrong model. | fails open |
| A new PR while too many product PRs are open (a backstop, not a WIP limit) | Overloading the machine with simultaneous landings. | fails open |

**Choose fail-closed for the irreversible.** A hook that guards the live service, a
device or the lane cap blocks when it can't decide; one that guards a convenience
lets the call through and logs.

**A blocked call says what to do instead**, and a wrong block is fixed in the hook by
PR, never worked around. An agent routing around a hook — a fork, a cloud session, a
`--force` — is treated as the incident, not the hook.

**Hooks also enforce the coordinator's own duties**: a stop hook refuses to end the
coordinator's turn while its watcher or its scheduled check-in is gone, and says
exactly what to call.

---

## 8. Design before build, and an independent fidelity check

Two gates for user-visible work, both added after something shipped wrong.

**The board gate.** No screen is built from a design the owner hasn't approved. Every
UI PR names the approved design boards it builds; the landing script refuses UI
without that line, or naming a board not marked approved. **A PR can't approve its own
boards**: the approvals registry and UI can't change in the same PR. A helper whose
slice needs a missing board stops and reports the gap instead of building "from
approved parts".

**The fidelity gate.** The board gate checks that boards are *named*; nothing checked
the build *matched* them. A major release reached the owner's phone unlike its
approved boards — one theme never screenshot-tested, a whole component never built, a
stale screenshot — and nobody had compared the two. Now:

1. A script builds a sheet: every state of every cited board beside the PR's
   screenshot for that state, in every theme.
2. **A fresh, read-only reviewer agent — never the PR's author session — compares them**
   state by state and writes its verdict on the PR with the sheet's digest.
3. The gate refuses a UI PR without that line, refuses a reviewer named `self` or
   `author`, and treats a screenshot changed after the review as a stale review.

**First night: real blockers on 9 UI PRs**, none of which the build or the device
scenarios would have caught — wrong copy and icons, a dead button, screenshots
injected past the real code path, a control on a state the board doesn't have.

**Gates must read real sources.** One builder passed the board gate in a local
pre-check with a stand-in CLI and a hand-written PR body; the retro's action is that
the check reads only the real PR. Any gate an agent can feed its own inputs is a gate
that agent can pass.

**A cutover needs a parity table.** Before an old screen is switched off for a new
one, a table lists every feature of the old one and where it went, with no row
`LOST`. That same release had dropped several features of the old screens that
nobody had listed. (It was also rolled back the same day, for an unrelated bug.)

This is §D's independence rule — *a round never merges itself* — applied to visual
work, where green tests say least.

---

## 9. Watching without burning the budget

**Tokens follow wake-ups and rework, not lanes.** A coordinator with a long context
re-reads all of it on every wake-up. With a 30-minute monitor, a 30-minute check-in and
a reply to every routine event, idle wake-ups were the largest single cost.

- **A quiet watcher** that exits only on something to act on (a failure, a merge,
  main changing colour, the service down) and is restarted after each.
- **A scheduled check-in every two hours**, as the backstop if a restart is missed.
  Scheduled jobs expire; recreate them before they do, and **keep at least one wake-up
  scheduled through any pause** — a pause that removed every wake-up meant the resume
  never fired.
- **A watchdog outside the session**, because the coordinator's checklist dies with
  its session. One overnight it sat idle ~11 hours while devices idled and handed-back
  PRs waited. A scheduled OS job now raises flags (lanes low, ready PR not landing, main
  red with no fix open, disk low, nightly didn't run its devices, coordinator silent),
  wakes the coordinator, and escalates to a push on the owner's phone only after an
  hour unanswered — at most twice a day and never at night.
- **Watch the watchdog.** It was first installed with an interval trigger that ran
  once at install and never again. Nobody heard of a 7-hour idle coordinator. Every
  run now stamps a time, and a stale stamp is itself an alarm.

### Thrift and push

- **The order when they conflict: quality, then usage, then velocity.** The owner set
  it once, and every lever is judged by it.
- **Pushes are time-boxed.** "Use more tokens until Friday 17:00, then back to
  normal" — written down with its end, so the push doesn't become the new default.
- **Log the cost of each hand-back** (PR, slice, tokens, model) so the daily retro
  can print cost per slice. Totals alone hid where the tokens went.

---

## 10. The owner

The owner's attention is the scarcest resource in the system.

- **Report only when a PR changes state or a decision is needed.** "No change"
  messages were the second most repeated complaint.
- **Lead every update with `Needs you:` while anything waits on the owner**, with what
  each item unblocks. The coordinator once ended dozens of updates with "nothing needs
  you" while the owner's top-priority designs had waited on his review for a day —
  and the designs had truncated text, so he couldn't have reviewed them anyway.
  Check a review item is reviewable before asking.
- **Notify the moment something is ready for review**; stay silent otherwise.
- **A daily "decisions made for you" list.** Don't block on the owner: make the call,
  record it, and send all such calls once a day so he can override them together.
  Scattered defaults, mentioned once each in passing, were never reviewed.
- **Ask only for a written list of things**: loosening a safety gate, the owner's own
  device or data, priorities, designs he hasn't seen, persistent machine config,
  production deploys, anything public. Everything else, decide.
- **Push back with data** when a request doesn't fit — "uncapped cloud lanes" became
  "lanes capped by the landing queue". **Research before any process change**, and
  cite what you found.
- **Estimates from measured throughput**, never from a serial chain in your head. The
  owner corrected low estimates three times in ten days.
- **Never claim a result before seeing it.** A running agent is "still running".

---

## 11. Retros that change something

1. **Daily, blameless, compiled from local state**: merges, landing failures by cause,
   watchdog flags and how long each stayed open, device and build-slot busy time,
   the nightly.
2. **Every proposed action is filed as an issue** with an owner.
3. **A slip seen on two days within two weeks becomes an enforced check** — a hook, a
   landing-script refusal, a watchdog flag. A memory note doesn't count.
4. **Weekly, close or retire the open actions.** At one point 0 of 25 filed actions had
   been closed. Filing is not fixing.
5. **New rules go into the written playbook the same day**, not only into the
   coordinator's memory, where they die with a context.

The pattern under most entries above is the same: a correct rule, written down,
ignored under load, then turned into a mechanism. This is
[principle 10](PRINCIPLES.md#10-enforce-structure-where-it-becomes-impossible-to-add-later)
at the scale of a team of agents.

---

## 12. Pauses and resumes

Usage pauses are deliberate; the danger is the resume. After one pause, throughput
halved for a day; after another, about 25 merges landed while two nightlies hadn't
really run their device suites, main turned out red on 16 scenarios, and features
were held for six hours. The resume checklist, in order:

1. Did every nightly since the pause really run its devices? If not, run them first.
2. Is main green? Fix first; expect stale tests more than bugs.
3. Is the machine healthy — devices, disk, memory, CI actually starting jobs?
4. Is the priority list true against what actually merged?
5. Drain open PRs before adding new ones.
6. Refill lanes gradually.
7. Restore everything the pause stopped: holds, scheduled jobs, monitors, recordings.

**Record a pause as a file with an end time**, so the watchdog mutes the right alarms
and wakes the coordinator when it ends.

---

## 13. Upgrading the platform under a live service

Treat it like a landing: **stage the new version beside the live one**, run the same
suite on both, switch at a quiet moment after a backup, health-check, and roll back by
itself on any failure. Two lessons that cost an outage each:

- **A stage must exercise a real request, not only start the service.** A switch
  passed every staged check and was rolled back after 12 minutes: no real request had
  gone through the new version's admission path.
- **Stage on a quiet machine.** Under load, a five-minute startup check became a
  60-minute timeout.

---

## Where each lesson went

| lesson here | now in |
|---|---|
| Cap, hotspots, sizing to the merge queue, finish before start (§2) | `LOOP.md` §F *Sizing* · principle 14 |
| One merge path, pre-check, queue, batching, no stacking, stale merges (§4) | §F *The one way onto the default branch* |
| Red main, known red, one retry, quarantine, environment holds (§5) | §F *Red default branch* |
| A stage that ran nothing (§5) | Hard rule · principle 13 |
| Disk, temp homes, pattern kills (§6) | Hard rule *Remove what you created* |
| Hooks for hard rules (§7) | §B step 6a · `PROJECT_RULES` template |
| Fidelity review, gates reading real sources (§8) | §D review check · principle 15 |
| Chain state files, hand-off budget (§3) | §D *Context hygiene* |
| Quiet watching, outside watchdog (§9) | §F *Watching and the human* |
| Decisions list, "needs you" first (§10) | `## Decided, not asked` · §F |
| Spawning prompts, model tiers, thrift windows, retros, pauses, upgrades | Here only. Project practice, not yet a pattern across projects. |

## What's not verified

- **One project, one author, seven weeks.** Nothing here has been reproduced
  elsewhere, and that project ran its own process, not a release of this protocol.
  §F is its lessons written as protocol, untested as written.
- **The numbers are the project's own logs**, not an independent measurement, and
  several rules changed at once more than once — the 400–700k → 215–325k cost drop, for
  example, came with three changes together and can't be attributed to any one.
- **The coordinator pattern assumes one human who is reachable within hours.** Nothing
  here was tried with more than one owner or none.
