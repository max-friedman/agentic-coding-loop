# Landing

One way onto main, so every change passes the same checks.

## Prelanding

`python3 scripts/prelanding.py` merges `origin/main` into the branch in a scratch worktree, runs the checks in
`PRELANDING_CHECKS` or `prelanding.checks` in `.loop/config.json` (no default: with none set it fails rather than pass on nothing; list your project's fast checks, separated by
`;`), and records the pass for the branch's head commit in `.loop/prelanding/`. Hand back only after it passes.

**Fail fast.** Everything readable from the PR body and the file list is checked before the scratch worktree or any
check, all at once, each with its fix: a gate change without its review line, a review line that is there but names
the author or the coordinator, an `Intentional revert:` line that is bulleted, quoted or bold (the stale-merge guard
reads only a plain line). A typo then costs seconds instead of a whole run. `prelanding.py --body-only [--pr N] [--body
FILE]` runs just these. A *missing* review line is not among them: it is added after an independent review, so the checks
still run first and its refusal (exit 13) comes after them.

**Disk.** The scratch worktree lives under `.loop/throwaways/` and is made only once the run holds one of
`prelanding.max_throwaways` (2) places (`scripts/throwaway_worktrees.py`), so queued runs don't each hold a full
checkout while they wait for the build slot. It is removed however the run ends, SIGTERM and SIGHUP included, and a
stale one a kill left (idle 2 h, owner gone) is swept at the start of the next run.

Before the checks it refuses two things (knobs under `prelanding` in `.loop/config.json`):

- **A gate changed together with product code** (exit 11), unless the PR body says `Gate change: reviewed by
  <reviewer>` with someone independent: a fresh reviewer agent or the owner, never the author or the coordinator. A
  gate is any file that decides what runs, what is skipped or what passes (`prelanding.gate_paths`); product code is
  `prelanding.code_paths` (set it to turn the rule on). Reviewed together, the check and the code it checks can be
  loosened in one step and nobody sees it. Split the gate change into its own PR. The line is an honour check:
  anyone can type it, so it means something only when the coordinator really had an independent reviewer read the diff.
- **A stale merge** (exit 12, `scripts/stale_revert.py`): the branch removes lines that main added since it forked,
  usually a merge resolved to the old copy. Merge main again keeping both sides; if removing them is the point, say
  `Intentional revert: <what and why>` in the PR body.

After the checks pass, one more refusal (exit 13, no pass recorded):

- **A required review line is missing.** `prelanding.review_lines` lists rules such as `{"name": "Fidelity",
  "when_body": "^Cutover:", "when_paths": ["ui/"]}`: a PR whose body declares a cutover, or that changes `ui/`, needs
  `Fidelity: OK (<reviewer>, ...)` from someone independent. Declare whatever your reviews cover (user-visible work, a
  cutover, a migration). A cutover once recorded a prelanding pass with no review line at all, because the rule only
  looked at changed paths and a cutover can be a one-line config change. Anything that queues PRs by itself calls
  `prelanding.missing_review_lines()` and skips a PR that lacks a line: an auto-queue once queued a PR before its
  review came back.

## A cutover checks the build users run, not only the config

A cutover switches features on for users. One once did it while the release pipeline sat paused for days and users
still ran an old build: the config said "on", nothing changed for them, and nobody checked. `scripts/cutover_gate.py`
runs from prelanding for every branch (a branch that isn't a cutover passes at once; a cutover: exit 14, after the
other checks) and prints the pipeline's state. A PR is a cutover when its body matches `cutover.when_body`
(`Cutover: <what it switches on>`) or it changes `cutover.when_paths`. It refuses when:

1. **the release pipeline is paused** (`release.paused_file`): land the fix, let it pass its checks, resume the
   pipeline (`release.resume_command`), wait for its build;
2. **the build users run lacks the switched code**: a cutover that changes no shipped code (a config switch) needs the
   published build (`release.published_file`) to contain every shipped change up to the cutover's base, where the
   branch meets main. A cutover that changes shipped code ships in the next build, which check 1 keeps possible;
3. **no recent whole-suite pass**: a run in `cutover.passes_file` within 24 h, on a commit containing the base, with no
   failure or only known-red ones. Run the whole suite before the cutover, not after.

The checklist, in order: the pipeline running → the build users run has main's shipped changes → a whole-suite pass
in 24 h → the review line → land. After it lands, check that what users actually run is the published build.

## Landing a reviewed PR: `scripts/review_land.py`

`python3 scripts/review_land.py <PR> --line "Fidelity: OK (<reviewer>, <what they checked>)"` does the steps between a
review and the landing, in order, and stops at the first one it can't do safely: it checks out the PR's exact head
branch (reusing a clean worktree that has it, fast-forwarding a stale local branch, refusing one with commits the PR
lacks, never the live checkout), merges main in when the branch is behind and pushes (a conflict stops with the
files), writes the line into the body through a per-PR body file, runs prelanding there, and then runs
`review_land.after` (`scripts/land.sh {pr}`, or your queue's add command). `--dry-run` says what it would do. Doing
these steps by hand broke again and again on branch names: a stale local branch with the PR's name, the branch
checked out in another worktree, a worktree made on the wrong branch. It writes only the line it is given; the review
is still the reviewer's, and prelanding still judges the line.

## Never skip a gate

No `--no-verify`, no stub, no env var that turns a check off on the command line (`git_rules.py` blocks or warns). An
override flag on the landing scripts exists for the coordinator only (`git_rules.coordinator_only_flags`), and each use
should be logged where the owner reviews it. A wrong gate is fixed in the gate, in its own pull request.

## Batch prelanding

`python3 scripts/prelanding.py --batch 12 15 19` checks several PRs in one run, because one run per PR delivers PRs to
the queue one at a time and a batch of landings rarely forms. It merges `origin/main` and the PRs, in order, into one
scratch worktree and runs the checks once. Green records a pass for each head (the record says which PRs it was checked
with). Red is bisected by halves, each half its own run, so the innocent PRs still get passes and only the culprit
fails, with its own output. The per-PR rules above run first, per PR, with their usual exit codes (the outcome is
`refused`). A PR that changes a gate or a path in `prelanding.alone_paths` (a protocol, a migration: whatever lands by
itself), or that conflicts with an earlier PR in the batch, runs on its own. At most `prelanding.batch_max` (6) PRs
share a run. A failure whose output contains `prelanding.env_marker` ("ENVIRONMENT, not your PR") is the machine's,
so it blames nobody and isn't bisected. `--plan` says which runs it would make without running them; `--json FILE`
writes each PR's outcome; the exit is 0 only if every PR passed. Bigger batches save more when green and cost more
when red: one culprit among six costs 1 + 2 + 2 (+ 2) runs against six alone.

## land.sh

A starter version of the landing pattern, not the queue the source project runs. `scripts/land.sh <PR>` refuses a pull request whose head has no recorded prelanding pass, takes the merge lock
(`scripts/repo_lock.py merge`), and squash-merges with `--match-head-commit`, so a push after the checks can't slip in.
With `gh_rules.block_pr_merge` on in `.loop/config.json`, `.claude/hooks/gh_rules.py` blocks every other way to merge.

## A queue, when lanes land faster than one at a time

Not shipped: the source project grew `land.sh` into a queue that is specific to its builds, devices and deploy. The
recipe, if you need it:

1. A queue file (`.loop/land_queue.json`) of pull requests whose prelanding passed; `add <PR>` appends.
2. One worker takes the head of the queue, merges main into it, reruns the checks, merges under the merge lock, and
   deploys main to the live checkout.
3. Batch: when several are queued, test them merged together once (up to six; `prelanding.py --batch` does the
   checking, see above); on a failure, split and retest. Let the queue's worker run the batch prelanding for entries
   added as "needs prelanding" (one job at a time, not while a nightly or a pause holds the queue), and never stale-block
   an entry that waits for that job.
4. Red main holds features: while main fails a check, refuse pull requests that could affect the failing area unless
   the branch is a fix. Only failures main doesn't already have block a landing.
5. After the merge, short checks run in the background and revert only a culprit; the full suite runs nightly.
6. A held state: `hold <PR> --why "<reason>"` keeps a PR out of the queue (it removes the PR's entry unless it is
   landing, and records the hold with its reason and time). `add` refuses a held PR, naming the reason, until
   `add <PR> --unhold`, which releases the hold and queues it; `status` lists the holds with their reasons; anything
   that queues PRs by itself (a watchdog's auto-queue of ready PRs) skips held ones. Dropping a PR isn't enough: a PR
   dropped twice to land only after a release was queued again by the auto-queue and landed.
7. The auto-queue also skips a PR missing a review line prelanding requires (`missing_review_lines()`): a review
   can't be bypassed by queueing before it returns.
8. After a PR merges, its helper's worktree goes with it: removed when clean and idle, or else only its build output.
   A finished lane that kept a full checkout was most of a 33 GB worktrees directory.
