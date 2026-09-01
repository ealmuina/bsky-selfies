#!/bin/bash
# Delete local copies of generated images, keeping only the newest $KEEP
# (default 7). The files stay in git history and on GitHub.
#
# The skip-worktree bit makes git treat the missing files as unmodified, so
# their deletion can never be committed or pushed (even by a stray
# "git add ."). Restore a pruned file with:
#   git update-index --no-skip-worktree <file> && git checkout -- <file>
set -eo pipefail
KEEP="${PRUNE_KEEP:-7}"
cd "$(dirname "$0")"

mapfile -t files < <(ls images/posts_*.png 2>/dev/null | sort)
count=${#files[@]}
if (( count <= KEEP )); then
    exit 0
fi
for f in "${files[@]:0:count-KEEP}"; do
    git update-index --skip-worktree "$f" || true
    rm -f "$f"
done
echo "Pruned $((count - KEEP)) local image(s); kept the newest $KEEP."