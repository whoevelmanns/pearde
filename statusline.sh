#!/bin/bash
# prd statusbar — ships with the skill; wire it as the global status line
# (see INSTALL.md beside this script) so every project gets it.
#
# Renders:  <dir> <branch> · <model>           — always
#           ▸prd <d>/<n> <p>% · open <o> <q>%  — only when a prds/ board is in scope
#
# The prd segment mirrors the progress line in README.md beside this script:
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
[ -n "$BRANCH" ] && [ "$BRANCH" != "HEAD" ] && OUT="$OUT \033[38;5;245m${BRANCH}\033[0m"
[ -n "$MODEL" ] && OUT="$OUT \033[38;5;240m·\033[0m \033[38;5;245m${MODEL}\033[0m"

# ── board segment ──────────────────────────────────────────────────────────────
BOARD=""
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
    END {
      n=0; done=0; open=0; known=0; ksum=0
      for (f in st) {
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
    OUT="$OUT \033[38;5;240m·\033[0m \033[38;5;108m▸prd\033[0m \033[38;5;252m${D}/${N}\033[0m \033[38;5;108m${P}%\033[0m"
    OUT="$OUT \033[38;5;240m·\033[0m \033[38;5;252mopen ${O}\033[0m \033[38;5;214m${Q}%\033[0m"
  fi
fi

printf '%b' "$OUT"
