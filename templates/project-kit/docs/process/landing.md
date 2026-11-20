# Landing

One way onto main, so every change passes the same checks.

## Prelanding

`python3 scripts/prelanding.py` merges `origin/main` into the branch in a scratch worktree, runs the checks in
`PRELANDING_CHECKS` or `prelanding.checks` in `.loop/config.json` (no default: with none set it fails rather than pass on nothing; list your project's fast checks, separated by
`;`), and records the pass for the branch's head commit in `.loop/prelanding/`. Hand back only after it passes.

Before the checks it refuses two things (knobs under `prelanding` in `.loop/config.json`):

- **A gate changed together with product code** (exit 11), unless the PR body says `Gate change: reviewed by
  <reviewer>` with someone independent: a fresh reviewer agent or the owner, never the author or the coordinator. A
  gate is any file that decides what runs, what is skipped or what passes (`prelanding.gate_paths`); product code is
  `prelanding.code_paths` (set it to turn the rule on). Reviewed together, the check and the code it checks can be
  loosened in one step and nobody sees it. Split the gate change into its own PR.
- **A stale merge** (exit 12, `scripts/stale_revert.py`): the branch removes lines that main added since it forked,
  usually a merge resolved to the old copy. Merge main again keeping both sides; if removing them is the point, say
  `Intentional revert: <what and why>` in the PR body.

## Never skip a gate

No `--no-verify`, no stub, no env var that turns a check off on the command line (`git_rules.py` blocks or warns). An
override flag on the landing scripts exists for the coordinator only (`git_rules.coordinator_only_flags`), and each use
should be logged where the owner reviews it. A wrong gate is fixed in the gate, in its own pull request.

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
3. Batch: when several are queued, test them merged together once; on a failure, split and retest.
4. Red main holds features: while main fails a check, refuse pull requests that could affect the failing area unless
   the branch is a fix. Only failures main doesn't already have block a landing.
5. After the merge, short checks run in the background and revert only a culprit; the full suite runs nightly.
