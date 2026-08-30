#!/usr/bin/env bash
# Re-applies every *.patch in this directory to the live skills/pearde repo.
#
# Why this exists: main here can be synced from pearde-src (checkout, cherry-
# pick, or a raw file copy of a feature branch) at any time. A sync replaces
# whole files, so it silently drops any local-only patch sitting on top
# unless that patch is re-applied afterward. Run this script after every
# sync so the drop becomes a loud `git apply` failure instead of a silent
# regression.
#
# Usage: bash resources/board/local-patches/reapply.sh
#   - already applied (git already has the hunk) -> reports "already applied", exits 0
#   - applies cleanly -> applies it, exits 0
#   - conflicts (the synced file changed too much) -> FAILS LOUDLY, exits 1,
#     so you know to hand-merge the patch and regenerate it (see below)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
cd "$REPO"

status=0
for patch in "$HERE"/*.patch; do
  [ -e "$patch" ] || continue
  name="$(basename "$patch")"
  if git apply --check --reverse "$patch" >/dev/null 2>&1; then
    echo "already applied: $name"
    continue
  fi
  if git apply --check "$patch" >/dev/null 2>&1; then
    git apply "$patch"
    echo "applied: $name"
  else
    echo "CONFLICT: $name does not apply cleanly - the synced file changed" \
         "underneath it. Hand-merge, then regenerate with:" \
         "git diff <old-local-only-commit>^ <old-local-only-commit> -- <file> > $patch"
    status=1
  fi
done

exit $status
