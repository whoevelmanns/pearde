#!/bin/bash
# pearde install — put every skill in this repo where each agent finds it.
#
#   install.sh [dir]           say what is missing and what would change
#   install.sh --apply [dir]   make the links, write the blocks
#   install.sh --remove [dir]  unlink the links, strip the blocks
#
# The bootstrap. It is a shell command and not a skill on purpose: it has to
# run on a machine where no agent has been told about this repo yet.
#
# What it knows about any agent comes from the table in
# @references/targets.md, read by @resources/targets.py. Nothing here names
# one. A skill folder is linked into an agent's skills directory; an agent
# with no such directory gets the block from @references/system.md appended
# to the instructions file it does read, between markers.
#
# `dir` is the project the per-project rows resolve against — the repo you
# want the board in. Defaults to the current directory.
#
# It never replaces a real directory: a folder sitting where a link belongs
# may hold someone's edits, and telling the two apart is the user's call.
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
MODE=report
case "${1:-}" in
  --apply)  MODE=apply;  shift ;;
  --remove) MODE=remove; shift ;;
  -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
esac
START="$(cd "${1:-$PWD}" 2>/dev/null && pwd)" || START="$PWD"

command -v python3 >/dev/null 2>&1 || {
  echo "pearde install: needs python3 — it is the only reader of references/targets.md" >&2
  exit 1
}

CHANGED=0
BLOCKED=0
# Two agents can read the same instructions file — AGENTS.md is a convention,
# not one agent's. The block is written once; the second row says so rather
# than reporting a write that did not happen.
SEEN=""
say()  { printf '  %-9s %-8s %s\n' "$1" "$2" "$3"; }
did()  { printf '  %-9s %-8s ✓ %s\n' "" "" "$1"; CHANGED=1; }
stop() { printf '  %-9s %-8s ! %s\n' "" "" "$1"; BLOCKED=1; }

echo "pearde install — $ROOT → $START"
echo

# ── the block, written between its markers and nowhere else ──────────────────
# An instructions file belongs to the user. The block is replaced in place
# when it is already there and appended when it is not; everything outside
# the two markers is never read back out.
write_block() {
  local file="$1"
  python3 - "$file" "$ROOT/references/system.md" <<'PY'
import os, sys
path, src = sys.argv[1], sys.argv[2]
block = open(src, encoding="utf-8").read().strip()
begin, end = "<!-- pearde:begin", "<!-- pearde:end -->"
old = ""
if os.path.isfile(path):
    old = open(path, encoding="utf-8", errors="replace").read()
if begin in old and end in old:
    head, rest = old.split(begin, 1)
    new = head + block + rest.split(end, 1)[1]
else:
    new = (old.rstrip() + "\n\n" if old.strip() else "") + block + "\n"
os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
open(path, "w", encoding="utf-8").write(new)
PY
}

strip_block() {
  python3 - "$1" <<'PY'
import os, sys
path = sys.argv[1]
begin, end = "<!-- pearde:begin", "<!-- pearde:end -->"
if not os.path.isfile(path):
    sys.exit(0)
text = open(path, encoding="utf-8", errors="replace").read()
if begin not in text or end not in text:
    sys.exit(0)
head, rest = text.split(begin, 1)
new = (head.rstrip() + "\n" + rest.split(end, 1)[1].lstrip("\n")).strip()
open(path, "w", encoding="utf-8").write(new + "\n" if new else "")
PY
}

# ── one line per wireable thing, from the registry ───────────────────────────
while IFS=$'\t' read -r agent kind state path want; do
  [ -n "$agent" ] || continue
  case "$kind" in
    agent)
      say "$agent" "$state" "not on this machine — nothing to wire"
      ;;
    context)
      case " $SEEN " in
        *" $path "*)
          say "$agent" "$state" "$path — the same file as an earlier agent"
          continue ;;
      esac
      SEEN="$SEEN $path"
      case "$state:$MODE" in
        ok:remove)      strip_block "$path" && did "stripped the block from $path" ;;
        ok:*)           say "$agent" ok "$path — block current" ;;
        *:remove)       say "$agent" "$state" "$path — no block to strip" ;;
        *:apply)        write_block "$path" && did "wrote the block into $path" ;;
        missing:*)      say "$agent" missing "$path"
                        say "" "" "fix: install.sh --apply $START" ;;
        stale:*)        say "$agent" stale "$path — block differs from references/system.md"
                        say "" "" "fix: install.sh --apply $START" ;;
      esac
      ;;
    *)
      case "$state:$MODE" in
        ok:remove)      rm -f "$path" && did "unlinked $path" ;;
        ok:*)           say "$agent" ok "$kind → $path" ;;
        copy:*)         say "$agent" copy "$path is a directory, not a link to $want"
                        stop "reconcile it yourself, then: ln -sfn $want $path" ;;
        *:remove)       say "$agent" "$state" "$kind — nothing of ours to remove" ;;
        *:apply)        mkdir -p "$(dirname "$path")"
                        if ln -sfn "$want" "$path"; then did "linked $path"
                        else stop "could not link $path"; fi ;;
        missing:*)      say "$agent" missing "$kind — /$kind does not exist here"
                        say "" "" "fix: install.sh --apply $START" ;;
        stale:*)        say "$agent" stale "$path → $(readlink "$path" 2>/dev/null) · not $want"
                        say "" "" "fix: install.sh --apply $START" ;;
      esac
      ;;
  esac
done < <(python3 "$DIR/targets.py" status "$START")

# ── no target at all is an answer, not a failure ─────────────────────────────
# Every skill folder reads where it lies. An agent this repo has never heard
# of is pointed at the path and is done.
if ! python3 "$DIR/targets.py" status "$START" | grep -qv $'\tagent\tabsent'; then
  echo
  echo "  No agent from references/targets.md is on this machine."
  echo "  Every skill reads where it lies — point yours at:"
  python3 "$DIR/targets.py" skills | while IFS=$'\t' read -r n p; do
    echo "    $n  $p/SKILL.md"
  done
fi

echo
[ "$BLOCKED" = 1 ] && { echo "pearde install: something is in the way — see the ! lines above."; exit 1; }
case "$MODE" in
  apply)  [ "$CHANGED" = 1 ] && echo "pearde install: wired." || echo "pearde install: already wired — nothing to do." ;;
  remove) [ "$CHANGED" = 1 ] && echo "pearde install: removed. prds/ is your data and was not touched." || echo "pearde install: nothing of ours was installed." ;;
  *)      echo "pearde install: report only — run with --apply to wire it." ;;
esac
exit 0
