# Landing

One way onto main, so every change passes the same checks.

## Prelanding

`python3 scripts/prelanding.py` merges `origin/main` into the branch in a scratch worktree, runs the checks in
`PRELANDING_CHECKS` (default: every `.claude/hooks/test_*.py`; set it to your project's fast checks, separated by
`;`), and records the pass for the branch's head commit in `.loop/prelanding/`. Hand back only after it passes.

## land.sh

A starter version of the landing pattern, not the queue the source project runs. `scripts/land.sh <PR>` refuses a pull request whose head has no recorded prelanding pass, takes the merge lock
(`scripts/repo_lock.py merge`), and squash-merges with `--match-head-commit`, so a push after the checks can't slip in.
`.claude/hooks/gh_rules.py` blocks every other way to merge.

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
