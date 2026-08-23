#!/bin/bash
# pearde doctor — is the skill installed, wired, and serving this board?
#
#   doctor.sh [board]        report every part, exit 1 when one is broken
#   doctor.sh --fix [board]  report, then repair what is unambiguous
#
# One part per line: `ok`, `off` (installed nowhere, nothing to repair), or
# `broken` (installed and not working — the failure the loop used to run
# straight past). A broken part carries its exact fix on the next line.
# `skill`, `statusline`, `board`, `memos`, `view` and `plan` always report;
# `origin` needs PRDs to read, and `members` only exists on a master board.
#
# `--fix` repairs three things and only three: the missing skill symlink, a
# dead status-line symlink, and a view service that is down or not watching
# this board. A status
# line absent from settings.json is printed, never written: that file is the
# user's. After repairing, doctor re-checks itself once, so the report and the
# exit code describe the state the repairs left behind — never the state they
# replaced.
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIX=0
[ "${1:-}" = "--fix" ] && { FIX=1; shift; }
START="${1:-$PWD}"

BROKEN=0
REPAIRED=0
row() { printf '  %-11s %-7s %s\n' "$1" "$2" "$3"; [ "$2" = broken ] && BROKEN=1; return 0; }
fix() { printf '  %-11s %-7s fix: %s\n' "" "" "$1"; }
did() { printf '  %-11s %-7s ✓ %s\n' "" "" "$1"; REPAIRED=1; }

echo "pearde doctor — $START"
[ -n "${CLAUDE_CONFIG_DIR:-}" ] && echo "  config     $CLAUDE_CONFIG_DIR"
echo

# Is Claude Code on this machine at all? The next two rows check wiring that is
# specific to it — a skills symlink and a statusLine — and neither is something
# the board needs. README: all state is on disk, and anything that can read
# files, write files and run commands can work it. So on a machine without the
# harness these rows must not read as damage, and their fix must point at the
# agent-neutral entry point instead of at a symlink nobody wants.
HARNESS=0
for d in "${CLAUDE_CONFIG_DIR:-}" "$HOME/.claude"; do
  [ -n "$d" ] && [ -d "$d" ] && { HARNESS=1; break; }
done

# ── skill: discoverable as a skill named pearde ───────────────────────────────
SKILL_LINKS=()
for p in "$HOME/.claude/skills/pearde" "$START/.claude/skills/pearde"; do
  [ -e "$p" ] || [ -L "$p" ] && SKILL_LINKS+=("$p")
done
if [ ${#SKILL_LINKS[@]} -eq 0 ]; then
  if [ "$HARNESS" = 0 ]; then
    row skill off "no Claude Code here — the board does not need one"
    fix "point your agent at $DIR/references/system.md, or run the commands in README.md directly"
  else
    row skill off "discovered nowhere — the /pearde command does not exist"
    fix "ln -s $DIR ~/.claude/skills/pearde"
  fi
  if [ "$FIX" = 1 ] && [ "$HARNESS" = 1 ]; then
    mkdir -p "$HOME/.claude/skills"
    ln -s "$DIR" "$HOME/.claude/skills/pearde" && did "linked ~/.claude/skills/pearde"
  fi
else
  bad=""
  for p in "${SKILL_LINKS[@]}"; do
    [ -e "$p/README.md" ] || bad="$p"
  done
  if [ -n "$bad" ]; then
    row skill broken "$bad does not resolve to a skill folder"
    fix "ln -sfn $DIR $bad"
    [ "$FIX" = 1 ] && ln -sfn "$DIR" "$bad" && did "repointed $bad"
  else
    row skill ok "$(printf '%s ' "${SKILL_LINKS[@]}")-> $DIR"
  fi
fi

# ── status line: configured, and its command resolves ─────────────────────────
# $CLAUDE_CONFIG_DIR is the config in force, and it is not always ~/.claude.
# Reading the wrong one reports a status line that is fine in a file nothing
# loads — the false green this whole check exists to catch.
CFG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SL_FILE=""; SL_CMD=""
for s in "$START/.claude/settings.local.json" "$START/.claude/settings.json" \
         "$CFG_DIR/settings.local.json" "$CFG_DIR/settings.json"; do
  [ -f "$s" ] || continue
  c=$(python3 - "$s" <<'PY' 2>/dev/null
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)
sl = d.get("statusLine") or {}
print(sl.get("command", "") if sl.get("type") == "command" else "")
PY
)
  [ -n "$c" ] && { SL_FILE="$s"; SL_CMD="$c"; break; }
done

if [ -z "$SL_CMD" ]; then
  if [ "$HARNESS" = 0 ]; then
    row statusline off "no Claude Code here — nowhere to render a status line"
    fix "the same numbers, on demand: bash $DIR/statusline.sh <<< '{}'"
  else
    row statusline off "no statusLine in $CFG_DIR — the board numbers show nowhere"
    fix "add to $CFG_DIR/settings.json: \"statusLine\": {\"type\": \"command\", \"command\": \"bash $DIR/statusline.sh\"}"
  fi
else
  # the command's script path: the first argument that exists, or looks like one
  SL_PATH=$(printf '%s\n' $SL_CMD | grep -E '/|\.sh$' | head -1)
  if [ -n "$SL_PATH" ] && [ ! -e "$SL_PATH" ]; then
    if [ -L "$SL_PATH" ]; then
      row statusline broken "$SL_PATH -> $(readlink "$SL_PATH") · dead symlink"
      fix "ln -sfn $DIR/statusline.sh $SL_PATH"
      [ "$FIX" = 1 ] && ln -sfn "$DIR/statusline.sh" "$SL_PATH" && did "repointed $SL_PATH"
    else
      row statusline broken "$SL_PATH does not exist · configured in $SL_FILE"
      fix "point that command at: bash $DIR/statusline.sh"
    fi
  else
    out=$(PRD_STATUS_JSON="{\"current_dir\":\"$START\"}" bash ${SL_PATH:-$DIR/statusline.sh} 2>/dev/null)
    if [ -z "$out" ]; then
      row statusline broken "$SL_PATH renders nothing for $START"
      fix "bash $DIR/statusline.sh — compare, per references/install.md step 2"
    else
      # strip colours AND the OSC-8 hyperlink, or the preview prints the URL
      # sequence raw and reads as garbage
      clean=$(printf '%s' "$out" | perl -pe 's/\e\]8;;[^\e]*\e\\//g; s/\e\[[0-9;]*m//g' 2>/dev/null \
              || printf '%s' "$out" | sed 's/\x1b\[[0-9;]*m//g')
      # the status line renders two rows; the preview keeps them two rows, so
      # what doctor shows is shaped like what the terminal shows
      row statusline ok "$(printf '%s' "$clean" | head -1)"
      # `|| [ -n "$l" ]`: the last line carries no newline, and a bare `read`
      # returns false on it and drops it
      printf '%s' "$clean" | tail -n +2 | while IFS= read -r l || [ -n "$l" ]; do
        [ -n "$l" ] && printf '  %-11s %-7s %s\n' "" "" "$l"
      done
    fi
  fi
fi

# ── board: on the contract path, with settings ────────────────────────────────
BOARD=""; d="$START"
while [ -n "$d" ] && [ "$d" != "/" ]; do
  [ -d "$d/prds" ] && { BOARD="$d/prds"; break; }
  d=$(dirname "$d")
done
if [ -z "$BOARD" ]; then
  # a board off the contract path is found, not skipped: one level down, dot-dirs too
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
    fix "the first run writes it, per references/settings.md — ask the board language"
  else
    LANG=$(grep -E '^[[:space:]]*language:' "$BOARD/settings.md" | head -1 | sed 's/.*language:[[:space:]]*//')
    if [ -z "$LANG" ]; then
      row board broken "$BOARD · $N PRDs · settings.md has no language"
      fix "write language: <language>, asked from the user, per references/settings.md"
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
    fix "list them, one '- <path>' or '- <name>: <path>' per line, per references/settings.md"
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
# See README, Derived work.
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
      fix "edit them to match references/memo.md — the keys are a closed set"
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
# A board with no plan has no waves, no critical path and no bars — the view
# opens and says so. Not broken: a board planned once and never re-planned is
# a normal state, and `plan` is one command.
if [ -n "$BOARD" ]; then
  PLANNED=$(sed -n 's/.*"planned_at"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
            "$BOARD/.plan.json" 2>/dev/null | head -1)
  if [ -z "$PLANNED" ]; then
    row plan off "no plan on record — the view has no bars until there is one"
    fix "python3 $DIR/view/plan.py plan $BOARD"
  else
    NW=$(grep -c '": [0-9]*,\?$' "$BOARD/.plan.json" 2>/dev/null || echo 0)
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
echo "pearde: installed and wired."
