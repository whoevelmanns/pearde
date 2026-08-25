#!/bin/bash
# pearde doctor — is the skill installed, wired, and serving this board?
#
#   doctor.sh [board]        report every part, exit 1 when one is broken
#   doctor.sh --fix [board]  report, then repair what is unambiguous
#
# One part per line: `ok`, `off` (installed nowhere, nothing to repair), or
# `broken` (installed and not working — the failure that otherwise runs
# straight past). A broken part carries its exact fix on the next line.
# `wired`, `index`, `statusline` and `board` always report. `memos`, `view`
# and `plan` need a board in scope, `origin` needs PRDs in it, and `members`
# only exists on a master board.
#
# No agent is named in this script. `wired` and `statusline` read
# @references/targets.md through @resources/targets.py — a row per agent,
# holding where its skills go, which instructions file it reads, and where a
# continuous line is configured. An agent is added by editing that table.
#
# `--fix` repairs three things and only three: the links and blocks that
# @resources/install.sh owns, a dead status-line symlink, and a view service
# that is down or not watching this board. A status line absent from an
# agent's settings is printed, never written — that file is the user's. After
# repairing, doctor re-checks itself once, so the report and the exit code
# describe the state the repairs left behind.
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIX=0
[ "${1:-}" = "--fix" ] && { FIX=1; shift; }
START="${1:-$PWD}"

BROKEN=0
REPAIRED=0
UNWIRED=0
note() { printf '  %-11s %-7s %s\n' "" "" "$1"; }
row() { printf '  %-11s %-7s %s\n' "$1" "$2" "$3"; [ "$2" = broken ] && BROKEN=1; return 0; }
fix() { printf '  %-11s %-7s fix: %s\n' "" "" "$1"; }
did() { printf '  %-11s %-7s ✓ %s\n' "" "" "$1"; REPAIRED=1; }

echo "pearde doctor — $START"
python3 "$DIR/targets.py" agents "$START" 2>/dev/null \
  | awk -F'\t' '$2 != "" { printf "  %-10s %s\n", $1, $2 }' \
  | sed '1s/^/  agents found\n/'
echo

# ── wired: every skill, in every agent that takes one ────────────────────────
# What "installed" means, per @references/targets.md: a skill folder linked
# into an agent's skills directory, or the block from @references/system.md
# in the instructions file an agent reads instead. Absent agents are not
# damage and report nothing. A machine with no agent at all still gets the
# paths — every skill folder reads where it lies.
if ! command -v python3 >/dev/null 2>&1; then
  row wired broken "no python3 to read references/targets.md"
  fix "install python3 — targets.py is the only reader of that format"
else
  WIRED=$(python3 "$DIR/targets.py" status "$START" 2>/dev/null)
  HERE=$(printf '%s\n' "$WIRED" | awk -F'\t' '$3 != "absent"')
  BAD=$(printf '%s\n' "$HERE" | awk -F'\t' '$3 != "ok" && $1 != ""')
  NOK=$(printf '%s\n' "$HERE" | awk -F'\t' '$3 == "ok"' | grep -c . )
  NAG=$(printf '%s\n' "$HERE" | awk -F'\t' '$1 != "" {print $1}' | sort -u | tr '\n' ' ')
  if [ -z "$(printf '%s' "$HERE" | tr -d '[:space:]')" ]; then
    UNWIRED=1
    row wired off "no agent from references/targets.md is on this machine"
    fix "point yours at these directly, or add a row to @references/targets.md:"
    python3 "$DIR/targets.py" skills 2>/dev/null | while IFS=$'\t' read -r n p; do
      note "$n  $p/SKILL.md"
    done
  elif [ -z "$(printf '%s' "$BAD" | tr -d '[:space:]')" ]; then
    row wired ok "$NOK link$([ "$NOK" = 1 ] || echo s) · $NAG"
  else
    NB=$(printf '%s\n' "$BAD" | grep -c . )
    # nothing wired anywhere and nothing in the way is a fresh clone, not
    # damage: `off`, and one command away. `broken` is reserved for an
    # install that exists and does not work — half-wired, or something
    # pointing at the wrong place.
    ODD=$(printf '%s\n' "$BAD" | awk -F'\t' '$3 != "missing"' | grep -c . )
    if [ "$NOK" -eq 0 ] 2>/dev/null && [ "$ODD" -eq 0 ] 2>/dev/null; then
      UNWIRED=1
      row wired off "not wired anywhere yet · $NAG"
      fix "bash $DIR/install.sh --apply $START"
      if [ "$FIX" = 1 ] && bash "$DIR/install.sh" --apply "$START" >/dev/null 2>&1; then
        did "wired $NB link$([ "$NB" = 1 ] || echo s)/block$([ "$NB" = 1 ] || echo s)"
      fi
      NB=0
    fi
    [ "$NB" -gt 0 ] 2>/dev/null || BAD=""
  fi
  if [ -n "$(printf '%s' "$BAD" | tr -d '[:space:]')" ]; then
    # a copy is never repaired: `ln -s` without symlink rights silently
    # copies, and a diverged copy may hold the user's edits
    COPIES=$(printf '%s\n' "$BAD" | awk -F'\t' '$3 == "copy"' | grep -c . )
    row wired broken "$NB of $((NOK + NB)) not wired · $NAG"
    printf '%s\n' "$BAD" | while IFS=$'\t' read -r a k s p _w; do
      [ -n "$a" ] && note "$a $k $s ${p}"
    done
    if [ "$COPIES" -gt 0 ] 2>/dev/null; then
      fix "reconcile the copies by hand — they may hold your edits — then: bash $DIR/install.sh --apply $START"
    else
      fix "bash $DIR/install.sh --apply $START"
      if [ "$FIX" = 1 ] && bash "$DIR/install.sh" --apply "$START" >/dev/null 2>&1; then
        did "wired $NB missing link$([ "$NB" = 1 ] || echo s)/block$([ "$NB" = 1 ] || echo s)"
      fi
    fi
  fi
fi

# ── index: does the map still match the tree? ─────────────────────────────────
# index.md is what `@<path>` and `@@<keyword>` resolve against. A map that has
# drifted answers confidently and wrongly, and nothing else in this repo
# notices — every other check reads a path someone already typed correctly.
if ! command -v python3 >/dev/null 2>&1; then
  row index broken "index.md present, no python3 to read it"
  fix "install python3 — index.py is the only reader of the format"
else
  IPROBLEMS=$(python3 "$DIR/index.py" check 2>&1)
  if [ -z "$IPROBLEMS" ]; then
    NF=$(python3 "$DIR/index.py" files 2>/dev/null | wc -l | tr -d ' ')
    NK=$(python3 "$DIR/index.py" keywords 2>/dev/null | wc -l | tr -d ' ')
    row index ok "$NF files · $NK keywords · every anchor resolves"
  else
    NI=$(echo "$IPROBLEMS" | wc -l | tr -d ' ')
    row index broken "$NI problem$([ "$NI" = 1 ] || echo s)"
    echo "$IPROBLEMS" | while IFS= read -r l; do
      [ -n "$l" ] && printf '  %-11s %-7s %s\n' "" "" "$l"
    done
    fix "edit index.md — a row per file, and every @@ keyword defined there"
  fi
fi

# ── status line: configured, and its command resolves ────────────────────────
# Which agents render one, and which file each reads it from, is the `status`
# column of @references/targets.md — several spellings in the order the agent
# itself reads them. A machine can hold several profiles of the same agent,
# and a line configured in one nothing loads is correct and inert: the false
# green this whole check exists to catch. targets.py reports the file in
# force, never the first that happens to exist.
SL_ROWS=$(python3 "$DIR/targets.py" statusline "$START" 2>/dev/null)
if [ -z "$(printf '%s' "$SL_ROWS" | tr -d '[:space:]')" ]; then
  row statusline off "no agent here renders one — the board does not need it"
  fix "the same numbers, on demand: bash $DIR/statusline.sh <<< '{}'"
else
  while IFS=$'\t' read -r SL_AGENT SL_FILE SL_KEY SL_CMD; do
    [ -n "$SL_AGENT" ] || continue
    if [ -z "$SL_CMD" ]; then
      row statusline off "$SL_AGENT · no $SL_KEY in $SL_FILE — the board numbers show nowhere"
      fix "set $SL_KEY in $SL_FILE to: bash $DIR/statusline.sh"
      continue
    fi
    # the command's script path: the token that IS the script, quotes dropped.
    # Word-splitting first would turn a quoted interpreter path with a space
    # ("C:/Program Files/...") into fragments and report the first fragment as
    # a missing file — a working status line read as broken.
    SL_PATH=$(printf '%s\n' $SL_CMD | tr -d '"' | grep -E '\.sh$' | head -1)
    [ -z "$SL_PATH" ] && SL_PATH=$(printf '%s\n' $SL_CMD | tr -d '"' | grep -E '/' | head -1)
    if [ -n "$SL_PATH" ] && [ ! -e "$SL_PATH" ]; then
      if [ -L "$SL_PATH" ]; then
        row statusline broken "$SL_AGENT · $SL_PATH -> $(readlink "$SL_PATH") · dead symlink"
        fix "ln -sfn $DIR/statusline.sh $SL_PATH"
        [ "$FIX" = 1 ] && ln -sfn "$DIR/statusline.sh" "$SL_PATH" && did "repointed $SL_PATH"
      else
        row statusline broken "$SL_AGENT · $SL_PATH does not exist · configured in $SL_FILE"
        fix "point $SL_KEY at: bash $DIR/statusline.sh"
      fi
      continue
    fi
    out=$(PRD_STATUS_JSON="{\"current_dir\":\"$START\"}" bash "${SL_PATH:-$DIR/statusline.sh}" 2>/dev/null)
    if [ -z "$out" ]; then
      row statusline broken "$SL_AGENT · $SL_PATH renders nothing for $START"
      fix "bash $DIR/statusline.sh — compare, per @references/install.md"
      continue
    fi
    # strip colours AND the OSC-8 hyperlink, or the preview prints the URL
    # sequence raw and reads as garbage
    clean=$(printf '%s' "$out" | perl -pe 's/\e\]8;;[^\e]*\e\\//g; s/\e\[[0-9;]*m//g' 2>/dev/null \
            || printf '%s' "$out" | sed 's/\x1b\[[0-9;]*m//g')
    # the preview keeps the status line's two rows, so what doctor shows is
    # shaped like what the terminal shows
    row statusline ok "$SL_AGENT · $(printf '%s' "$clean" | head -1)"
    # `|| [ -n "$l" ]`: the last line carries no newline, and a bare `read`
    # returns false on it and drops it
    printf '%s' "$clean" | tail -n +2 | while IFS= read -r l || [ -n "$l" ]; do
      [ -n "$l" ] && note "$l"
    done
  done <<< "$SL_ROWS"
fi

# ── board: on the contract path, with settings ────────────────────────────────
BOARD=""; d="$START"
while [ -n "$d" ] && [ "$d" != "/" ]; do
  [ -d "$d/prds" ] && { BOARD="$d/prds"; break; }
  # dirname's fixpoint is not always `/` — on a Windows drive path it is `C:`,
  # and without this guard the loop never exits. A no-op on POSIX.
  p=$(dirname "$d"); [ "$p" = "$d" ] && break; d="$p"
done
if [ -z "$BOARD" ]; then
  # a board off the contract path is found, not skipped: three levels down,
  # dot-dirs too
  OFF=$(find "$START" -maxdepth 3 -type d -name prds 2>/dev/null | head -3)
  if [ -n "$OFF" ]; then
    row board broken "no prds/ at the repo root · found $(echo "$OFF" | tr '\n' ' ')"
    fix "git mv $(echo "$OFF" | head -1) $START/prds — the board path is the contract"
  else
    row board off "no board — the first run creates prds/"
  fi
else
  ROOT=$(git -C "$BOARD" rev-parse --show-toplevel 2>/dev/null)
  N=$(find "$BOARD" -type f -name prd.md 2>/dev/null | wc -l | tr -d ' ')
  # compare physical paths — /tmp vs /private/tmp is a spelling, not a move
  PBOARD=$(cd "$BOARD" 2>/dev/null && pwd -P)
  if [ -n "$ROOT" ] && [ "$PBOARD" != "$ROOT/prds" ]; then
    row board broken "$BOARD is not $ROOT/prds"
    fix "git mv $BOARD $ROOT/prds"
  elif [ ! -f "$BOARD/settings.md" ]; then
    row board broken "$N PRDs · no settings.md"
    fix "the first run writes it, per @references/settings.md — ask the board language"
  else
    LANG=$(grep -E '^[[:space:]]*language:' "$BOARD/settings.md" | head -1 | sed 's/.*language:[[:space:]]*//')
    if [ -z "$LANG" ]; then
      row board broken "$BOARD · $N PRDs · settings.md has no language"
      fix "write language: <language>, asked from the user, per @references/settings.md"
    else
      row board ok "$BOARD · $N PRDs · language $LANG"
    fi
  fi
fi

# ── members: the boards a master merges ──────────────────────────────────────
# Only on a master board. A member that is not on disk is the one failure that
# matters: the plan silently loses a whole project, and the board looks smaller
# rather than broken.
if [ -n "$BOARD" ] && grep -qE '^[[:space:]]*members:' "$BOARD/settings.md" 2>/dev/null; then
  MEM=$(python3 "$DIR/view/plan.py" members "$BOARD" 2>/dev/null | grep .)
  NM=$(printf '%s\n' "$MEM" | grep -c . )
  MISS=$(printf '%s\n' "$MEM" | grep -c MISSING || true)
  NAMES=$(printf '%s\n' "$MEM" | awk '{print $1}' | tr '\n' ' ')
  MPRDS=$(printf '%s\n' "$MEM" | awk '$0 !~ /MISSING/ {print $2}' \
          | while IFS= read -r m; do [ -d "$m" ] && find "$m" -type f -name prd.md; done \
          | wc -l | tr -d ' ')
  if [ "$NM" -eq 0 ] 2>/dev/null; then
    row members broken "members: is empty — a master board with no members"
    fix "list them, one '- <path>' or '- <name>: <path>' per line, per @references/settings.md"
  elif [ "$MISS" -gt 0 ] 2>/dev/null; then
    row members broken "$NM member board(s) · $MISS not on disk · $NAMES"
    printf '%s\n' "$MEM" | grep MISSING | while IFS= read -r l; do
      printf '  %-11s %-7s %s\n' "" "" "$l"
    done
    fix "correct or drop those members: entries in $BOARD/settings.md"
  else
    # the name is reported, never repaired: what a group of projects is called
    # is the user's call, and the first round that meets an unnamed master
    # board asks for it. Inference keeps the board working until then.
    BNAME=$(python3 -c "import sys;sys.path.insert(0,'$DIR/view');import plan;print(plan.board_name('$BOARD'))" 2>/dev/null)
    if grep -qE '^[[:space:]]*name:' "$BOARD/settings.md" 2>/dev/null; then
      row members ok "$NM member board(s) · ${NAMES}· $MPRDS member PRDs planned here · name $BNAME"
    else
      row members ok "$NM member board(s) · ${NAMES}· $MPRDS member PRDs planned here"
      printf '  %-11s %-7s %s\n' "" "" "name inferred as '$BNAME' — the round asks the user and writes name: to settings.md"
    fi
  fi
fi

# ── origin: the deliverable against what the board found for itself ──────────
# A derived PRD that names no `from:` cannot be traced to the work that
# surfaced it, and a board whose derived tree matches its requested one is
# working on itself. Both are reports, not repairs — the trade is the user's.
# See @references/parts/derived.md.
if [ -n "$BOARD" ] && [ "$N" -gt 0 ] 2>/dev/null; then
  ORIG=$(find "$BOARD" -type f -name prd.md -print0 2>/dev/null | xargs -0 awk '
    FNR==1 { ph=0; og="requested"; fr=""; st="?" }
    { if (ph>=2) next
      if ($0 ~ /^---[ \t]*$/) { ph++; if (ph==2) {
          if (og=="derived") { d++; if (fr=="") nofrom++
            if (st!="done" && st!="deferred") dlive++ }
          else { a++; if (st!="done" && st!="deferred") alive++ } }
        next }
      if (ph==1) {
        if ($1=="origin:") { og=$2; sub(/#.*/,"",og) }
        else if ($1=="from:") { fr=$2; sub(/#.*/,"",fr) }
        else if ($1=="state:") { st=$2; sub(/#.*/,"",st) } } }
    END { printf "%d %d %d %d %d\n", a+0, d+0, nofrom+0, alive+0, dlive+0 }')
  set -- $ORIG
  A=${1:-0}; D=${2:-0}; NOFROM=${3:-0}; ALIVE=${4:-0}; DLIVE=${5:-0}
  if [ "$D" -eq 0 ] 2>/dev/null; then
    row origin ok "$A requested · nothing derived"
  elif [ "$NOFROM" -gt 0 ] 2>/dev/null; then
    row origin broken "$D derived · $NOFROM with no from:"
    fix "add from: <prd> naming the PRD whose work surfaced each one"
  elif [ "$DLIVE" -ge "$ALIVE" ] 2>/dev/null && [ "$DLIVE" -gt 0 ] 2>/dev/null; then
    row origin broken "$DLIVE derived in flight vs $ALIVE requested — the board is working on itself"
    fix "put the split to the user: continue, defer the derived tree, or drop it"
  else
    row origin ok "$A requested ($ALIVE live) · $D derived ($DLIVE live)"
  fi
fi

# ── memos: the board's decision records, and their frontmatter ────────────────
if [ -n "$BOARD" ]; then
  MDIR=$(python3 -c "import sys;sys.path.insert(0,'$DIR');import memos;d,e=memos.memos_dir('$BOARD');print(f'{d}\t{e}')" 2>/dev/null)
  MEXT="${MDIR##*	}"; MDIR="${MDIR%%	*}"
  if [ ! -d "${MDIR:-$BOARD/memos}" ] && [ "$MEXT" != "True" ]; then
    row memos off "no memos/ — a decision gets one when there is a decision"
  elif ! command -v python3 >/dev/null 2>&1; then
    row memos broken "memos/ present, no python3 to read it"
    fix "install python3 — memos.py is the only reader of the format"
  else
    M=$(find "${MDIR:-$BOARD/memos}" -maxdepth 1 -type f -name '*.md' ! -name README.md 2>/dev/null | wc -l | tr -d ' ')
    SRC=""; [ "$MEXT" = "True" ] && SRC=" · external at $MDIR, mirrored read-only"
    PROBLEMS=$(python3 "$DIR/memos.py" check "$BOARD" 2>&1)
    if [ -z "$PROBLEMS" ]; then
      row memos ok "$M memos · frontmatter checks out$SRC"
    else
      NP=$(echo "$PROBLEMS" | wc -l | tr -d ' ')
      row memos broken "$M memos · $NP problem$([ "$NP" = 1 ] || echo s)"
      echo "$PROBLEMS" | while IFS= read -r l; do
        [ -n "$l" ] && printf '  %-11s %-7s %s\n' "" "" "$l"
      done
      fix "edit them to match @references/memo.md — the keys are a closed set"
    fi
  fi
fi

# ── the view service: is the board actually being watched? ────────────────────
# The board is files, so nothing here is required for the board to work. What
# this row answers is whether the live view — the thing a person looks at and
# edits through — is up and watching THIS board. Matched on the registered
# path, never the name: a board keys by its declared `name:`, and grepping the
# directory would report a watched board as unwatched.
if [ -n "$BOARD" ]; then
  SRV_PORT="${PEARDE_PORT:-8443}"
  SRV=$(curl -fsS -m 2 "http://127.0.0.1:$SRV_PORT/status" 2>/dev/null)
  if [ -z "$SRV" ]; then
    row view off "not running — the board reads and plans without it"
    fix "python3 $DIR/view/serve.py ensure $BOARD"
    if [ "$FIX" = 1 ] && python3 "$DIR/view/serve.py" ensure "$BOARD" >/dev/null 2>&1; then
      did "view service started"
    fi
  elif printf '%s' "$SRV" | grep -qF "\"$BOARD\"" \
       || printf '%s' "$SRV" | grep -qF "\"$PBOARD\""; then
    BN=$(printf '%s' "$SRV" | tr '{' '\n' | grep -F "\"$BOARD\"" \
         | sed -n 's/.*"name": "\([^"]*\)".*/\1/p' | head -1)
    row view ok "watching · http://127.0.0.1:$SRV_PORT/board/${BN:-?}"
  else
    row view broken "the service is up but this board is not registered"
    fix "python3 $DIR/view/serve.py ensure $BOARD"
    if [ "$FIX" = 1 ] && python3 "$DIR/view/serve.py" ensure "$BOARD" >/dev/null 2>&1; then
      did "board registered"
    fi
  fi
fi

# ── the plan: is there one, and how old is it? ────────────────────────────────
# A board with no plan has no order, no critical path and no bars — the view
# opens and says so. Not broken: a board planned once and never re-planned is
# a normal state, and `plan` is one command.
if [ -n "$BOARD" ]; then
  PLANNED=$(sed -n 's/.*"planned_at"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
            "$BOARD/.plan.json" 2>/dev/null | head -1)
  if [ -z "$PLANNED" ]; then
    row plan off "no plan on record — the view has no bars until there is one"
    fix "python3 $DIR/view/plan.py plan $BOARD"
  else
    row plan ok "planned $PLANNED"
  fi
fi

echo
if [ "$FIX" = 1 ] && [ "$REPAIRED" = 1 ]; then
  echo "pearde: repaired — re-checking."
  echo
  exec bash "$0" "$START"
fi
[ "$BROKEN" = 1 ] && echo "pearde: something is installed and not working — the fixes are above." && exit 1
# `off` everywhere is not `ok`: an unwired repo works when run by hand and is
# one command from being reached by name. Saying "wired" here would be the
# false green the whole report exists to avoid.
[ "$UNWIRED" = 1 ] && echo "pearde: nothing is broken, and no agent has been pointed at it yet." && exit 0
echo "pearde: installed and wired."
