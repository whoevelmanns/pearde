#!/bin/bash
# pearde statusbar. Wire it as the global status line — @references/install.md.
#
# Renders line 1:  <dir> <branch> <*dirty ↑ahead ↓behind> · <model>  — always
#         line 2:  ▸pearde<⊞b> <rd>/<rn> <rp>% · +<dr>d · open <o> <q>% · <persona> · ▸board
#
# Every term on line 2 is defined in @references/parts/progress.md. `⊞b` is the
# board count, on a master board only — the board plus its members.
#
# The board owns line 2 — sharing a row with the path pushes it off a narrow
# terminal. No board, no second line.
#
# `*N` is what `git status` reports — an untracked directory counts once, not
# per file inside it. `↑N`/`↓N` are commits against the upstream. No upstream
# says so: `↑0` would read as "everything is pushed" when there is nowhere to
# push to. `▸board` is an OSC-8 link to the board's view at
# 127.0.0.1:8443/board/<name>, matched on the daemon's registered path, and
# absent when no daemon is running. PRD_STATUS_LINK=off renders the label
# without the escape, for a terminal that shows them raw.
#
# It reads four frontmatter keys — `state`, `complexity`, `origin`, and `est`
# as the weight's last fallback — and matches them
# by name at any indentation. Nested under a parent map reads the same as top
# level. Every other key is a user extension: never anchor these patterns to
# column 0.
#
# Reads the status JSON on stdin, or $PRD_STATUS_JSON when composed. Three
# fields are used: `current_dir` (or `cwd`) locates the board, `display_name`
# is the model, and `transcript_path` is where `<persona>` comes from — the
# only session state on this line, and the only one not read from a file the
# board owns.

JSON="${PRD_STATUS_JSON:-}"
[ -z "$JSON" ] && [ ! -t 0 ] && JSON=$(cat)

field() { printf '%s' "$JSON" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1; }

DIR=$(field current_dir); [ -z "$DIR" ] && DIR=$(field cwd); [ -z "$DIR" ] && DIR="$PWD"
# Windows: the status JSON carries `C:\Users\...` with JSON-doubled backslashes,
# and field() extracts them raw — a form no path test downstream accepts. tr
# collapses both the raw and the doubled backslash; sed folds the // the
# doubling leaves behind. A POSIX path has no backslash and is untouched.
BS=$(printf '\134')
case "$DIR" in *"$BS"*) DIR=$(printf '%s' "$DIR" | tr "$BS" '/' | sed 's|//*|/|g');; esac
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
  # dirname's fixpoint is not always `/` — on a Windows drive path it is `C:`,
  # and without this guard the loop never exits. A no-op on POSIX.
  p=$(dirname "$d"); [ "$p" = "$d" ] && break; d="$p"
done

# A master counts its members too — `members:` in settings.md names the boards
# it merges, and the numbers a master shows are the group's.
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
  # `weight-default` from settings.md — the average when no PRD is scored
  WD=$(awk 'p>=2{exit} /^---[ \t]*$/{p++; next} p==1 && $1=="weight-default:" {v=$2; sub(/#.*/,"",v); print v+0; exit}' "$BOARD/settings.md" 2>/dev/null)
  STATS=$(find "${SCAN[@]}" -type f \( -name prd.md -o -path '*/specs/*.md' \) -print0 2>/dev/null | xargs -0 awk -v WD="${WD:-0}" '
    FNR==1 { ph[FILENAME]=0; spec=(FILENAME ~ /\/specs\/[^\/]*\.md$/)
             if (!spec) { st[FILENAME]="?"; cx[FILENAME]=0; es[FILENAME]=""; og[FILENAME]="requested" } }
    {
      if (ph[FILENAME]>=2) next
      if ($0 ~ /^---[ \t]*$/) { ph[FILENAME]++; next }
      if (ph[FILENAME]==1) {
        if ($1=="complexity:") { c=$2; sub(/#.*/,"",c); c=c+0
          if (spec) { d=FILENAME; sub(/\/specs\/[^\/]*\.md$/,"/prd.md",d); sp[d]+=c }
          else cx[FILENAME]=c }
        else if (spec) next
        else if ($1=="state:") { s=$2; sub(/#.*/,"",s); st[FILENAME]=s }
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
      # user'"'"'s own leaves the counts entirely — it is neither progress nor
      # backlog, and the planner skips it too.
      return (s=="open" || s=="analyzing" || s=="refine" || s=="question" \
           || s=="specced" || s=="claimed" || s=="blocked" || s=="failed" \
           || s=="done")
    }
    # one weight, the one plan.py weight_of uses: `complexity`, else the
    # specs'"'"' sum, else `est`, else the average of every scored PRD —
    # `weight-default` when none is scored. @references/parts/progress.md
    function weight(f,  h) {
      if (cx[f]>0) return cx[f]
      if (sp[f]>0) return sp[f]
      h=hrs(es[f]); if (h>0) return h
      return avg
    }
    END {
      # an+ad are the DELIVERABLE — origin: requested. dr is reported beside
      # it and never folded in: one combined percentage cannot answer "how far
      # along are we". See @references/parts/derived.md.
      #
      # dr counts the derived PRDs that are NOT done — the backlog, not the
      # tree. It was the whole tree until 2026-08-30, which made it a number
      # that could only ever go up: a board with 95 of 99 derived PRDs closed
      # rendered `+99d`, read as 99 things outstanding, and the one question
      # this term exists to answer — is a derived tree growing unseen — cannot
      # be answered by a total that never comes down. Both halves are on the
      # progress line as `derived <dd>/<dn>`; the status line has room for one
      # and takes the one that moves.
      n=0; open=0; scored=0; csum=0; an=0; ad=0; dr=0
      for (f in st) if (cx[f]>0) { scored++; csum+=cx[f] }
      avg = (scored>0) ? csum/scored : ((WD>0) ? WD : 50)
      for (f in st) {
        if (!live(st[f])) { delete st[f]; continue }
        n++
        if (st[f]=="open") open++
        if (og[f]=="derived") { if (st[f]!="done") dr++ }
        else { an++; if (st[f]=="done") ad++ }
      }
      if (n==0) { print "0 0 0 0 0 0" ; exit }
      atot=0; adtot=0
      for (f in st) {
        if (og[f]=="derived") continue
        h=weight(f)
        atot+=h
        if (st[f]=="done") adtot+=h
      }
      ap = (atot>0) ? int(adtot*100/atot + 0.5) : 0
      q = int(open*100/n + 0.5)
      printf "%d %d %d %d %d %d\n", an, ad, ap, open, q, dr
    }
  ' 2>/dev/null)

  set -- $STATS
  N=${1:-0}; D=${2:-0}; P=${3:-0}; O=${4:-0}; Q=${5:-0}; DR=${6:-0}
  if [ "$N" -gt 0 ] 2>/dev/null; then
    BOARD_OUT="\033[38;5;108m▸pearde\033[0m"
    # attached to the label, not appended to the row — it qualifies what the
    # numbers count over
    [ "$NB" -gt 1 ] 2>/dev/null && \
      BOARD_OUT="$BOARD_OUT\033[38;5;108m⊞${NB}\033[0m"
    BOARD_OUT="$BOARD_OUT \033[38;5;252m${D}/${N}\033[0m \033[38;5;108m${P}%\033[0m"
    # suppressed at zero, which now means the derived backlog is drained
    # rather than merely absent — the one state worth rendering nothing for
    [ "$DR" -gt 0 ] 2>/dev/null && \
      BOARD_OUT="$BOARD_OUT \033[38;5;240m·\033[0m \033[38;5;209m+${DR}d\033[0m"
    BOARD_OUT="$BOARD_OUT \033[38;5;240m·\033[0m \033[38;5;252mopen ${O}\033[0m \033[38;5;214m${Q}%\033[0m"
  fi

  # who is working, from the session's own transcript. A persona is session
  # state and is stored nowhere — the transcript IS the session, so the last
  # `· as <id>` the board printed is the active one. Every round's line
  # carries it, per @references/parts/progress.md.
  #
  # Anchored on `▸`, the line's own sigil: `· as` alone turns up in prose,
  # `▸…· as` does not. The tail is bounded because this runs on every render
  # and a long session's transcript is tens of megabytes — the id is
  # re-stated each round, so the last 512K always holds the current one.
  # Before the first round there is nothing to read and the segment is
  # absent, which is correct: an unstated persona is `engineer` by default,
  # and rendering a default nobody chose reads as an answer.
  #
  # Sanitised, not trusted — this is model output, and an id reaching the
  # terminal unfiltered could carry an escape sequence. Lowercased, non-id
  # characters dropped, capped: what survives is renderable or nothing.
  PERSONA=""
  TP=$(field transcript_path)
  if [ -n "$TP" ] && [ -f "$TP" ]; then
    PERSONA=$(tail -c 524288 "$TP" 2>/dev/null \
      | grep -o '▸[^"]*· as [a-z][a-z0-9-]\{1,15\}' \
      | tail -1 | sed 's/.*· as //' \
      | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9-' | cut -c1-16)
  fi
  if [ -n "$PERSONA" ]; then
    [ -n "$BOARD_OUT" ] && BOARD_OUT="$BOARD_OUT \033[38;5;240m·\033[0m "
    BOARD_OUT="$BOARD_OUT\033[38;5;140m${PERSONA}\033[0m"
  fi

  # the link goes last — a terminal that mis-measures an OSC-8 sequence then
  # has nothing left to misplace. Matched on the daemon's registered PATH,
  # never the directory name: a board keys in the service by its declared name,
  # and grepping the directory would report a watched board as unwatched.
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

# Two lines when there is a board, one when there is none — an empty second
# line reads as a blank row, not an absence.
if [ -n "$BOARD_OUT" ]; then
  printf '%b\n%b' "$OUT" "$BOARD_OUT"
else
  printf '%b' "$OUT"
fi
