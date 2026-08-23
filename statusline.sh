#!/bin/bash
# pearde statusbar — ships with the skill; wire it as the global status line
# (see references/install.md beside this script) so every project gets it.
#
# Renders line 1:  <dir> <branch> <*dirty ↑ahead ↓behind> · <model>  — always
#         line 2:  ▸pearde <d>/<n> <p>% · open <o> <q>% · ▸board  — with a board
#
# The board gets its own line: it is the thing being read, and sharing a row
# with the path pushed it off the edge of a narrow terminal. No board, no
# second line — a blank row reads as a broken status line, not an empty board.
#
# `*N` is what `git status` reports — an untracked directory counts once, not
# per file inside it. `↑N`/`↓N` are commits against the upstream. No upstream
# says so: `↑0` would read as "everything is pushed" when there is nowhere to
# push to. `▸board` is an OSC-8 link to the board's Plane timeline, from the
# `gantt` key `sync.py plan` writes into .plane-map.json. PRD_STATUS_LINK=off
# renders the label without the escape, for a terminal that shows them raw.
#
# The pearde segment mirrors the progress line in README.md beside this script:
#   d/n = done PRDs / all PRDs, p% = est-weighted done share,
#   o   = PRDs in state `open`, q% = o/n by count (open PRDs have no est).
#
# It reads two frontmatter keys, `state` and `est`, and matches them by name at
# any indentation — nested under a parent map reads the same as top level. Every
# other key is a user extension: never anchor these patterns to column 0.
#
# Reads the status JSON on stdin, or $PRD_STATUS_JSON when composed.

JSON="${PRD_STATUS_JSON:-}"
[ -z "$JSON" ] && [ ! -t 0 ] && JSON=$(cat)

field() { printf '%s' "$JSON" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1; }

DIR=$(field current_dir); [ -z "$DIR" ] && DIR=$(field cwd); [ -z "$DIR" ] && DIR="$PWD"
MODEL=$(field display_name)

# ── base segment ───────────────────────────────────────────────────────────────
# full cwd, with $HOME collapsed to ~ and the last component brightened
SHORT="${DIR/#$HOME/~}"
PARENT="${SHORT%/*}"; LEAF="${SHORT##*/}"
if [ "$PARENT" = "$SHORT" ] || [ -z "$PARENT" ]; then
  OUT="\033[38;5;110m${SHORT}\033[0m"
else
  OUT="\033[38;5;244m${PARENT}/\033[0m\033[38;5;110m${LEAF}\033[0m"
fi

BRANCH=$(git -C "$DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ -n "$BRANCH" ] && [ "$BRANCH" != "HEAD" ]; then
  OUT="$OUT \033[38;5;245m${BRANCH}\033[0m"
  GIT=$(git -C "$DIR" status --porcelain=v2 --branch 2>/dev/null)
  if [ -n "$GIT" ]; then
    DIRTY=$(printf '%s\n' "$GIT" | awk '!/^#/ {n++} END {print n+0}')
    AB=$(printf '%s\n' "$GIT" | sed -n 's/^# branch\.ab //p')
    [ "$DIRTY" -gt 0 ] 2>/dev/null && OUT="$OUT \033[38;5;214m*${DIRTY}\033[0m"
    if [ -n "$AB" ]; then
      AHEAD=${AB%% *}; BEHIND=${AB##* }
      AHEAD=${AHEAD#+}; BEHIND=${BEHIND#-}
      [ "${AHEAD:-0}" -gt 0 ] 2>/dev/null && OUT="$OUT \033[38;5;214m↑${AHEAD}\033[0m"
      [ "${BEHIND:-0}" -gt 0 ] 2>/dev/null && OUT="$OUT \033[38;5;110m↓${BEHIND}\033[0m"
    else
      OUT="$OUT \033[38;5;203mno-upstream\033[0m"
    fi
  fi
fi
[ -n "$MODEL" ] && OUT="$OUT \033[38;5;240m·\033[0m \033[38;5;245m${MODEL}\033[0m"

# ── board segment — its own line ──────────────────────────────────────────────────────────────
BOARD=""; BOARD_OUT=""
d="$DIR"
while [ -n "$d" ] && [ "$d" != "/" ]; do
  if [ -d "$d/prds" ]; then BOARD="$d/prds"; break; fi
  d=$(dirname "$d")
done

if [ -n "$BOARD" ]; then
  STATS=$(find "$BOARD" -type f -name prd.md -print0 2>/dev/null | xargs -0 awk '
    FNR==1 { ph[FILENAME]=0; st[FILENAME]="?"; es[FILENAME]="" }
    {
      if (ph[FILENAME]>=2) next
      if ($0 ~ /^---[ \t]*$/) { ph[FILENAME]++; next }
      if (ph[FILENAME]==1) {
        if ($1=="state:") { s=$2; sub(/#.*/,"",s); st[FILENAME]=s }
        else if ($1=="est:") { e=$2; sub(/#.*/,"",e); es[FILENAME]=e }
      }
    }
    function hrs(v) {
      if (v=="") return -1
      if (v ~ /m$/) return (v+0)/60
      if (v ~ /d$/) return (v+0)*8
      return v+0
    }
    function live(s) {
      # the states the loop works, plus done. A PRD parked in a state of the
      # user'"'"'s own is not board progress and not board backlog: it leaves the
      # counts entirely, the same way the wave planner skips it.
      return (s=="open" || s=="analyzing" || s=="refine" || s=="question" \
           || s=="specced" || s=="claimed" || s=="failed" || s=="done")
    }
    END {
      n=0; done=0; open=0; known=0; ksum=0
      for (f in st) {
        if (!live(st[f])) { delete st[f]; continue }
        n++
        if (st[f]=="done") done++
        if (st[f]=="open") open++
        h=hrs(es[f]); if (h>=0) { known++; ksum+=h }
      }
      if (n==0) { print "0 0 0 0 0"; exit }
      avg = (known>0) ? ksum/known : 4
      tot=0; dtot=0
      for (f in st) {
        h=hrs(es[f]); if (h<0) h=avg
        tot+=h
        if (st[f]=="done") dtot+=h
      }
      p = (tot>0) ? int(dtot*100/tot + 0.5) : 0
      q = int(open*100/n + 0.5)
      printf "%d %d %d %d %d\n", n, done, p, open, q
    }
  ' 2>/dev/null)

  set -- $STATS
  N=${1:-0}; D=${2:-0}; P=${3:-0}; O=${4:-0}; Q=${5:-0}
  if [ "$N" -gt 0 ] 2>/dev/null; then
    BOARD_OUT="\033[38;5;108m▸pearde\033[0m \033[38;5;252m${D}/${N}\033[0m \033[38;5;108m${P}%\033[0m"
    BOARD_OUT="$BOARD_OUT \033[38;5;240m·\033[0m \033[38;5;252mopen ${O}\033[0m \033[38;5;214m${Q}%\033[0m"
  fi

  # the link goes last: a terminal that mis-measures an OSC-8 sequence then has
  # nothing left to misplace
  LINK=$(sed -n 's/.*"gantt"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
         "$BOARD/.plane-map.json" 2>/dev/null | head -1)
  if [ -n "$LINK" ]; then
    [ -n "$BOARD_OUT" ] && BOARD_OUT="$BOARD_OUT \033[38;5;240m·\033[0m "
    if [ "${PRD_STATUS_LINK:-on}" = "off" ]; then
      BOARD_OUT="$BOARD_OUT\033[38;5;110m▸board\033[0m"
    else
      BOARD_OUT="$BOARD_OUT\033[38;5;110m\033]8;;${LINK}\033\\\\▸board\033]8;;\033\\\\\033[0m"
    fi
  fi
fi

# Two lines when there is a board, one when there is none: an empty second line
# is a blank row in the terminal, not an absence.
if [ -n "$BOARD_OUT" ]; then
  printf '%b\n%b' "$OUT" "$BOARD_OUT"
else
  printf '%b' "$OUT"
fi
