#!/bin/bash
# pearde statusbar — ships with the skill; wire it as the global status line
# (see references/install.md beside this script) so every project gets it.
#
# Renders line 1:  <dir> <branch> <*dirty ↑ahead ↓behind> · <model>  — always
#         line 2:  ▸pearde<⊞b> <ad>/<an> <ap>% · +<dn>d · open <o> <q>% · ▸board
#
# The board gets its own line: it is the thing being read, and sharing a row
# with the path pushed it off the edge of a narrow terminal. No board, no
# second line — a blank row reads as a broken status line, not an empty board.
#
# `▸board` links to the board's live view, when the service is up. See below.
#
# `*N` is what `git status` reports — an untracked directory counts once, not
# per file inside it. `↑N`/`↓N` are commits against the upstream. No upstream
# says so: `↑0` would read as "everything is pushed" when there is nowhere to
# push to. `▸board` is an OSC-8 link to the board's view at
# 127.0.0.1:8443/board/<name>, matched on the daemon's registered path, and
# absent when no daemon is running. PRD_STATUS_LINK=off renders the label
# without the escape, for a terminal that shows them raw.
#
# The pearde segment mirrors the progress line in README.md beside this script:
#   ad/an = done / all REQUESTED PRDs, ap% = their est-weighted done share,
#   +dn   = derived PRD count (origin: derived), suppressed at zero,
#   o     = PRDs in state `open`, q% = o/n by count (open PRDs have no est),
#   ⊞b    = boards counted, on a master board only — the board plus its members.
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

# A master board counts its members too: `members:` in settings.md names the
# boards it merges, and the numbers a master shows are the group's numbers —
# that is the whole reason it exists. `⊞N` says how many boards are in them.
SCAN=(); NB=0
if [ -n "$BOARD" ]; then
  SCAN=("$BOARD"); NB=1
  if [ -f "$BOARD/settings.md" ]; then
    while IFS= read -r m; do
      [ -n "$m" ] || continue
      m="${m#*: }"                     # `- <name>: <path>` → the path
      m="${m/#\~/$HOME}"
      case "$m" in /*) p="$m" ;; *) p="$BOARD/$m" ;; esac
      [ -d "$p/prds" ] && p="$p/prds"  # an entry pointing at a repo root
      if [ -d "$p" ]; then SCAN+=("$p"); NB=$((NB + 1)); fi
    done <<< "$(awk 'f && $1=="-" {v=$0; sub(/^[ \t]*-[ \t]*/,"",v); sub(/[ \t]*#.*/,"",v); print v; next} f {exit} /^[ \t]*members:/ {f=1}' "$BOARD/settings.md")"
  fi
fi

if [ -n "$BOARD" ]; then
  STATS=$(find "${SCAN[@]}" -type f -name prd.md -print0 2>/dev/null | xargs -0 awk '
    FNR==1 { ph[FILENAME]=0; st[FILENAME]="?"; es[FILENAME]=""; og[FILENAME]="requested" }
    {
      if (ph[FILENAME]>=2) next
      if ($0 ~ /^---[ \t]*$/) { ph[FILENAME]++; next }
      if (ph[FILENAME]==1) {
        if ($1=="state:") { s=$2; sub(/#.*/,"",s); st[FILENAME]=s }
        else if ($1=="est:") { e=$2; sub(/#.*/,"",e); es[FILENAME]=e }
        else if ($1=="origin:") { o=$2; sub(/#.*/,"",o); og[FILENAME]=o }
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
           || s=="specced" || s=="claimed" || s=="blocked" || s=="failed" \
           || s=="done")
    }
    END {
      # an+ad are the DELIVERABLE — origin: requested. dn is the derived count,
      # reported beside it and never folded in: a derived PRD enlarges the
      # denominator with work the user never asked for, so one combined
      # percentage cannot answer "how far along are we". See README,
      # Derived work.
      n=0; open=0; known=0; ksum=0; an=0; ad=0; dn=0
      for (f in st) {
        if (!live(st[f])) { delete st[f]; continue }
        n++
        if (st[f]=="open") open++
        if (og[f]=="derived") dn++
        else { an++; if (st[f]=="done") ad++ }
        h=hrs(es[f]); if (h>=0) { known++; ksum+=h }
      }
      if (n==0) { print "0 0 0 0 0 0" ; exit }
      avg = (known>0) ? ksum/known : 4
      atot=0; adtot=0
      for (f in st) {
        if (og[f]=="derived") continue
        h=hrs(es[f]); if (h<0) h=avg
        atot+=h
        if (st[f]=="done") adtot+=h
      }
      ap = (atot>0) ? int(adtot*100/atot + 0.5) : 0
      q = int(open*100/n + 0.5)
      printf "%d %d %d %d %d %d\n", an, ad, ap, open, q, dn
    }
  ' 2>/dev/null)

  set -- $STATS
  N=${1:-0}; D=${2:-0}; P=${3:-0}; O=${4:-0}; Q=${5:-0}; DN=${6:-0}
  if [ "$N" -gt 0 ] 2>/dev/null; then
    BOARD_OUT="\033[38;5;108m▸pearde\033[0m"
    # attached to the label, not appended to the row: it qualifies what the
    # numbers are counted over, and a master with no marker reads as one board
    [ "$NB" -gt 1 ] 2>/dev/null && \
      BOARD_OUT="$BOARD_OUT\033[38;5;108m⊞${NB}\033[0m"
    BOARD_OUT="$BOARD_OUT \033[38;5;252m${D}/${N}\033[0m \033[38;5;108m${P}%\033[0m"
    # suppressed at zero: a board with nothing derived should not carry the
    # vocabulary, and an always-present +0d teaches the eye to skip it.
    [ "$DN" -gt 0 ] 2>/dev/null && \
      BOARD_OUT="$BOARD_OUT \033[38;5;240m·\033[0m \033[38;5;209m+${DN}d\033[0m"
    BOARD_OUT="$BOARD_OUT \033[38;5;240m·\033[0m \033[38;5;252mopen ${O}\033[0m \033[38;5;214m${Q}%\033[0m"
  fi

  # the link goes last: a terminal that mis-measures an OSC-8 sequence then has
  # nothing left to misplace.
  #
  # Matched on the daemon's registered PATH, never the directory name: a
  # board keys in the service by its declared name, and grepping the directory
  # would report a watched board as unwatched.
  SRV_PORT="${PEARDE_PORT:-8443}"
  LINK=""
  SRV=$(curl -fsS -m 1 "http://127.0.0.1:$SRV_PORT/status" 2>/dev/null)
  if [ -n "$SRV" ]; then
    BNAME=$(printf '%s' "$SRV" | tr '{' '\n' \
            | grep -F "\"path\": \"$BOARD\"" \
            | sed -n 's/.*"name": "\([^"]*\)".*/\1/p' | head -1)
    [ -n "$BNAME" ] && LINK="http://127.0.0.1:$SRV_PORT/board/$BNAME"
  fi

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
