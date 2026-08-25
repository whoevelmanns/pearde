#!/bin/bash
# pearde install — build one skill folder per file in skills/.
#
#   install.sh <skills-dir>           say what it would make
#   install.sh --apply <skills-dir>   make it
#   install.sh --remove <skills-dir>  take it back out
#
# `<skills-dir>` is wherever your agent discovers skills. This script does not
# guess it and knows no agent by name — @references/install.md is the whole
# explanation, and working out the directory is step one of it.
#
# A skill is a folder because a skill file says `Read @README.md`, relative to
# its own folder. Five links per skill and every `@<path>` in the repo
# resolves through the install exactly as it does here:
#
#   <skills-dir>/<name>/SKILL.md -> skills/<name>.md
#                       README.md · index.md · references · resources
#
# Links, never copies — one source of truth. A real file or directory already
# sitting where a link goes is reported and never replaced: it may hold your
# edits.
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
LINKS=(SKILL.md README.md index.md references resources)

MODE=report
case "${1:-}" in
  --apply)  MODE=apply;  shift ;;
  --remove) MODE=remove; shift ;;
  -h|--help|"") sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
esac
[ $# -ge 1 ] || { sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }
DEST="$1"

CHANGED=0; BLOCKED=0
say()  { printf '  %-14s %-8s %s\n' "$1" "$2" "$3"; }
did()  { printf '  %-14s %-8s ✓ %s\n' "" "" "$1"; CHANGED=1; }
stop() { printf '  %-14s %-8s ! %s\n' "" "" "$1"; BLOCKED=1; }

# The source each link points at. SKILL.md is the skill's own file; the rest
# are the repo's, shared by every skill.
source_of() {
  case "$2" in
    SKILL.md) printf '%s/skills/%s.md' "$ROOT" "$1" ;;
    *)        printf '%s/%s' "$ROOT" "$2" ;;
  esac
}

echo "pearde install — $ROOT → $DEST"
echo

# This repo may itself be sitting in the skills directory, under the name of
# one of its skills. That slot is already correct — the agent reading @SKILL.md
# found it that way — and building a folder over it would replace the repo
# with a link into itself. Step 1 of @references/install.md, enforced.
SELF="$(basename "$ROOT")"

for f in "$ROOT"/skills/*.md; do
  [ -e "$f" ] || continue
  name="$(basename "$f" .md)"
  at="$DEST/$name"

  if [ "$name" = "$SELF" ] && [ "$(cd "$DEST" 2>/dev/null && pwd -P)" = "$(dirname "$ROOT")" ]; then
    say "$name" self "this repo is already $at — nothing to build"
    continue
  fi

  # A folder we built is one whose SKILL.md resolves to this repo's skill file.
  want="$(source_of "$name" SKILL.md)"
  have=""
  [ -e "$at/SKILL.md" ] && have="$(cd "$(dirname "$at/SKILL.md")" 2>/dev/null && pwd -P)/$(basename "$at/SKILL.md")"
  if [ -e "$at" ] && [ ! -L "$at/SKILL.md" ] && [ -e "$at/SKILL.md" ]; then
    say "$name" copy "$at holds a real SKILL.md, not a link"
    stop "reconcile it yourself, then re-run — it may hold your edits"
    continue
  fi

  if [ "$MODE" = remove ]; then
    if [ -d "$at" ] && [ -L "$at/SKILL.md" ] && [ "$(readlink "$at/SKILL.md")" = "$want" ]; then
      for l in "${LINKS[@]}"; do rm -f "$at/$l"; done
      rmdir "$at" 2>/dev/null
      did "removed $at"
    else
      say "$name" —  "$at is not one of ours"
    fi
    continue
  fi

  missing=0
  for l in "${LINKS[@]}"; do
    [ -L "$at/$l" ] && [ "$(readlink "$at/$l")" = "$(source_of "$name" "$l")" ] || missing=$((missing + 1))
  done

  if [ "$missing" -eq 0 ]; then
    say "$name" ok "$at"
  elif [ "$MODE" = apply ]; then
    mkdir -p "$at" || { stop "could not make $at"; continue; }
    for l in "${LINKS[@]}"; do
      ln -sfn "$(source_of "$name" "$l")" "$at/$l" || stop "could not link $at/$l"
    done
    did "built $at"
  else
    say "$name" missing "$at — $missing of ${#LINKS[@]} links"
  fi
done

echo
[ "$BLOCKED" = 1 ] && { echo "pearde install: something is in the way — see the ! lines."; exit 1; }
case "$MODE" in
  apply)  [ "$CHANGED" = 1 ] && echo "pearde install: built." || echo "pearde install: already built — nothing to do." ;;
  remove) [ "$CHANGED" = 1 ] && echo "pearde install: removed. prds/ is your data and was not touched." || echo "pearde install: nothing of ours was there." ;;
  *)      echo "pearde install: report only — pass --apply to build it." ;;
esac
exit 0
