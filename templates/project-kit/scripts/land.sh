#!/usr/bin/env bash
# The one way onto main (.claude/hooks/gh_rules.py blocks the others): scripts/land.sh <PR>
# Refuses a PR whose head has no recorded prelanding pass (scripts/prelanding.py), then squash-merges it under the
# merge lock, pinned to the head that passed (--match-head-commit), so a later push can't slip in unchecked.
set -euo pipefail
pr="${1:?usage: scripts/land.sh <PR>}"
root="$(cd "$(dirname "$0")/.." && pwd)"
common="$(cd "$root" && cd "$(git rev-parse --git-common-dir)" && pwd)"
head="$(gh pr view "$pr" --json headRefOid -q .headRefOid)"
if [ ! -e "$(dirname "$common")/.loop/prelanding/$head" ]; then
  echo "land.sh: #$pr's head ${head:0:9} has no prelanding pass: run python3 scripts/prelanding.py on that branch" >&2
  exit 1
fi
python3 "$root/scripts/repo_lock.py" merge -- gh pr merge "$pr" --squash --delete-branch --match-head-commit "$head"
echo "land.sh: #$pr merged"
