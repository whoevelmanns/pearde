#!/bin/bash
# pearde doctor — is the skill installed, wired, and mirroring for this board?
#
#   doctor.sh [board]        report every part, exit 1 when one is broken
#   doctor.sh --fix [board]  report, then repair what is unambiguous
#
# Five parts, each on one line: `ok`, `off` (installed nowhere, nothing to
# repair), or `broken` (installed and not working — the failure the loop used
# to run straight past). A broken part carries its exact fix on the next line.
#
# `--fix` repairs four things and only four: the missing skill symlink, a dead
# status-line symlink, a board that Plane is running for but has never been
# bootstrapped, and a live service that is not watching this board. A status
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

# ── skill: discoverable as a skill named pearde ───────────────────────────────
SKILL_LINKS=()
for p in "$HOME/.claude/skills/pearde" "$START/.claude/skills/pearde"; do
  [ -e "$p" ] || [ -L "$p" ] && SKILL_LINKS+=("$p")
done
if [ ${#SKILL_LINKS[@]} -eq 0 ]; then
  row skill off "discovered nowhere — the /pearde command does not exist"
  fix "ln -s $DIR ~/.claude/skills/pearde"
  if [ "$FIX" = 1 ]; then
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
  row statusline off "no statusLine in $CFG_DIR — the board numbers show nowhere"
  fix "add to $CFG_DIR/settings.json: \"statusLine\": {\"type\": \"command\", \"command\": \"bash $DIR/statusline.sh\"}"
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

# ── plane: installed, running, configured for THIS board ──────────────────────
PL="$DIR/plane/plane.sh"
if [ ! -f "$DIR/plane/plane-app/plane.env" ]; then
  row plane off "not installed — the mirror is opt-in"
  fix "$PL boot"
else
  URL=$(bash "$PL" url 2>/dev/null)
  if ! curl -fsS -o /dev/null -m 3 "$URL" 2>/dev/null; then
    row plane broken "installed, $URL not reachable"
    fix "$PL start"
    [ "$FIX" = 1 ] && bash "$PL" start && did "started"
  elif [ -z "$BOARD" ]; then
    row plane ok "up at $URL · no board to mirror"
  elif [ -f "$BOARD/.plane.env" ]; then
    KEY=$(grep '^PLANE_API_KEY=' "$BOARD/.plane.env" | cut -d= -f2-)
    CODE=$(curl -s -o /dev/null -w '%{http_code}' -m 5 -H "X-API-Key: $KEY" "$URL/api/v1/users/me/" 2>/dev/null)
    case "$CODE" in
      200)
        SRV_PORT="${PLANE_SERVE_PORT:-8443}"
        if curl -fsS -m 2 "http://127.0.0.1:$SRV_PORT/status" 2>/dev/null | grep -q "\"$(basename "$(dirname "$BOARD")")\""; then
          row plane ok "up at $URL · this board mirrors · live service watching"
        elif [ "$FIX" = 1 ] && python3 "$DIR/plane/serve.py" ensure "$BOARD" >/dev/null 2>&1; then
          row plane ok "up at $URL · this board mirrors · live service watching"
          did "live service started"
        else
          row plane ok "up at $URL · this board mirrors · live service off — python3 $DIR/plane/serve.py ensure"
        fi ;;
      429) row plane ok "up at $URL · this board mirrors · api rate-limiting a sync in flight" ;;
      401|403)
        row plane broken "up at $URL · $BOARD/.plane.env token rejected"
        fix "$PL bootstrap $BOARD"
        [ "$FIX" = 1 ] && bash "$PL" bootstrap "$BOARD" && did "re-bootstrapped" ;;
      *) row plane ok "up at $URL · token unverified (HTTP ${CODE:-none})" ;;
    esac
  else
    row plane broken "up at $URL · this board was never bootstrapped, so nothing mirrors"
    fix "$PL bootstrap $BOARD && python3 $DIR/plane/sync.py sync"
    if [ "$FIX" = 1 ]; then
      bash "$PL" bootstrap "$BOARD" && python3 "$DIR/plane/sync.py" sync "$BOARD" && did "bootstrapped and synced"
      python3 "$DIR/plane/serve.py" ensure "$BOARD" >/dev/null 2>&1 && did "live service watching"
    fi
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
