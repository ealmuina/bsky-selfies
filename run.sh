#!/bin/bash
# Daily run: generate yesterday's image, post it to Bluesky, push to GitHub.
# Local image copies are pruned afterwards (prune_images.sh) — the full
# archive lives on GitHub. Never use "git add ." here: it would stage the
# pruned files' deletions and push them out of the GitHub archive.
set -eo pipefail

source .venv/bin/activate
python selfie.py

yesterday=$(date --date="yesterday" +"%Y-%m-%d")
commit_message="Generated image for $yesterday"

image="images/posts_${yesterday}.png"
git add "$image"
git commit -m "$commit_message"
git push

./prune_images.sh || echo "WARN: local image prune failed"