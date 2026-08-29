#!/bin/bash
# pearde doctor — is the skill installed, wired, and serving this board?
#
#   doctor.sh [board]         report every part, exit 1 when one is broken
#   doctor.sh --fix [board]   report, then repair what is unambiguous
#   doctor.sh --harnesses [board]
#                             also run the board's own verify.sh harnesses,
#                             whatever `harnesses:` in settings.md says
#
# One part per line: `ok`, `off` (installed nowhere, nothing to repair), or
# `broken` (installed and not working — the failure that otherwise runs
# straight past). A broken part carries its exact fix on the next line.
# `skills`, `index`, `statusline`, `board` and `briefs` always report.
# `memos`, `workflows`, `view` and `plan` need a board in scope, `origin`
# needs PRDs in it, and `members` only exists on a master board.
#
# No agent is named in this script and none is looked for. Where a skill goes
# and where a status line is configured are things only the reader knows —
# @references/install.md is the explanation, and it is written to be worked
# out rather than executed. What doctor checks is everything that is true
# regardless: the skill files are well-formed and every command name under
# resources/board/ is claimed by one module, the map matches the tree, the
# status line renders, and the board is on its contract.
#
# `--fix` repairs one thing and only one: a view service that is down or not
# watching this board. Nothing else here is unambiguous enough to repair
# unasked — a status line lives in a settings file that is the user's, and
# which index row a new file belongs in is a judgement. After repairing,
# doctor re-checks itself once, so the report and the exit code describe the
# state the repairs left behind.
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$DIR/.." && pwd)"
FIX=0
HFLAG=0
while [ $# -gt 0 ]; do
  case "${1:-}" in
    --fix)       FIX=1;   shift ;;
    --harnesses) HFLAG=1; shift ;;
    *) break ;;
  esac
done
START="${1:-$PWD}"

BROKEN=0
REPAIRED=0
note() { printf '  %-11s %-7s %s\n' "" "" "$1"; }
row() { printf '  %-11s %-7s %s\n' "$1" "$2" "$3"; [ "$2" = broken ] && BROKEN=1; return 0; }
fix() { printf '  %-11s %-7s fix: %s\n' "" "" "$1"; }
did() { printf '  %-11s %-7s ✓ %s\n' "" "" "$1"; REPAIRED=1; }

echo "pearde doctor — $START"
echo

# ── skills: every entry point, well-formed ───────────────────────────────────
# A skill is found by its frontmatter, so frontmatter that does not parse is a
# skill that silently never fires — the failure that looks like the model
# choosing not to use it. The folder name an install builds comes from the
# file name, so a `name:` that disagrees with it installs one skill under
# another's name.
#
# Where they are installed is not checked, and cannot be: only the reader
# knows which directory their agent scans, and there is deliberately no list
# of agents here. @references/install.md is that step.
SKN=0; SKBAD=""
for f in "$SKILL_ROOT"/skills/*.md; do
  [ -e "$f" ] || continue
  SKN=$((SKN + 1))
  base="$(basename "$f" .md)"
  nm=$(awk 'NR==1 && $0 !~ /^---/ {exit} /^---/ {n++; if (n==2) exit; next}
            n==1 && $1=="name:" {sub(/^[[:space:]]*name:[[:space:]]*/,""); print; exit}' "$f")
  ds=$(awk 'NR==1 && $0 !~ /^---/ {exit} /^---/ {n++; if (n==2) exit; next}
            n==1 && $1=="description:" {print "y"; exit}' "$f")
  if [ -z "$nm" ]; then SKBAD="$SKBAD
skills/$base.md has no name: in frontmatter — it is not a skill"
  elif [ "$nm" != "$base" ]; then SKBAD="$SKBAD
skills/$base.md says name: $nm — an install would build it as $nm/"
  elif [ -z "$ds" ]; then SKBAD="$SKBAD
skills/$base.md has no description: — nothing decides when it fires"
  fi
done
# One name, one module. pearde.py discovers resources/board/*.py and says
# on stderr which names clash; a clash is a skill whose command answers
# for the wrong file, so it is broken here rather than silently first-wins.
CLASH=$(python3 "$SKILL_ROOT/resources/pearde.py" help 2>&1 >/dev/null | sed -n 's/^pearde: //p')
[ -n "$CLASH" ] && SKBAD="$SKBAD
$CLASH"
if [ "$SKN" -eq 0 ]; then
  row skills broken "skills/ holds no .md file — there is nothing to install"
  fix "one file per skill, frontmatter name: matching the file name, and description:"
elif [ -n "$SKBAD" ]; then
  NS=$(printf '%s' "$SKBAD" | grep -c . )
  row skills broken "$SKN skill$([ "$SKN" = 1 ] || echo s) · $NS problem$([ "$NS" = 1 ] || echo s)"
  printf '%s\n' "$SKBAD" | while IFS= read -r l; do [ -n "$l" ] && note "$l"; done
  fix "frontmatter is what makes a skill findable — @references/install.md; one name per module under resources/board/ — python3 $SKILL_ROOT/resources/pearde.py help"
else
  NAMES=$(for f in "$SKILL_ROOT"/skills/*.md; do basename "$f" .md; done | tr '\n' ' ')
  row skills ok "$SKN well-formed · $NAMES"
  note "installed where your agent looks — @references/install.md, then: bash $DIR/install.sh --apply <skills-dir>"
fi

# ── index: does the map still match the tree? ─────────────────────────────────
# index.md is what `@<path>` and `@@<keyword>` resolve against, and
# references/files.md is the manifest behind it. A map that has drifted answers
# confidently and wrongly, and nothing else in this repo notices — every other
# check reads a path someone already typed correctly.
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
    fix "a row per file in references/files.md, every @@ keyword in index.md"
  fi
fi

# ── status line: does it render, for this board ──────────────────────────────
# Where a status line is wired is the reader's setup and not this repo's
# business — a config path here would be one agent's, and there is no list of
# agents. What doctor can answer is the half that is ours: given this board,
# does the script produce the line. A wired status line that renders nothing
# and one that is not wired at all look identical in the terminal, and this
# tells them apart.
out=$(PRD_STATUS_JSON="{\"current_dir\":\"$START\"}" bash "$DIR/statusline.sh" 2>/dev/null)
if [ -z "$out" ]; then
  row statusline broken "$DIR/statusline.sh renders nothing for $START"
  fix "run it directly and read the error: bash $DIR/statusline.sh <<< '{}'"
else
  # strip colours AND the OSC-8 hyperlink, or the preview prints the URL
  # sequence raw and reads as garbage
  clean=$(printf '%s' "$out" | perl -pe 's/\e\]8;;[^\e]*\e\\//g; s/\e\[[0-9;]*m//g' 2>/dev/null \
          || printf '%s' "$out" | sed 's/\x1b\[[0-9;]*m//g')
  # the preview keeps the status line's two rows, so what doctor shows is
  # shaped like what the terminal shows
  row statusline ok "$(printf '%s' "$clean" | head -1)"
  printf '%s' "$clean" | tail -n +2 | while IFS= read -r l || [ -n "$l" ]; do
    [ -n "$l" ] && note "$l"
  done
  note "wire it where your setup runs a command for one — @references/install.md"
fi

# ── guard: the loop's rules, wired as a hook ─────────────────────────────────
# A rule written in a reference file is advice, and the round that cost
# 318,584 tokens ignored three of them. The guard is the same rules as a
# PreToolUse hook — @references/parts/guard.md. Where hooks are configured IS
# knowable here, unlike a status line: the settings file sits in the repo the
# board lives in, so this checks that file and `--fix` writes the block.
GSET=""
d="$START"
while [ "$d" != "/" ]; do
  [ -d "$d/prds" ] && { GSET="$d/.claude/settings.json"; break; }
  d="$(dirname "$d")"
done
if [ -z "$GSET" ]; then
  :
elif ! python3 -c 'import sys' 2>/dev/null; then
  row guard broken "python3 not on PATH — the guard cannot run"
  fix "install python3, or drop the hooks block from $GSET"
else
  probe=$(echo '{"tool_name":"Bash","tool_input":{"command":"find prds -name prd.md"},"cwd":"'"$(dirname "$GSET")"'"}' \
          | python3 "$DIR/guard.py" pre 2>/dev/null)
  if ! printf '%s' "$probe" | grep -q '"deny"'; then
    row guard broken "$DIR/guard.py does not refuse a hand-walked board"
    fix "run it directly and read the error: echo '{}' | python3 $DIR/guard.py pre"
  elif [ -f "$GSET" ] && grep -q 'guard.py' "$GSET" 2>/dev/null; then
    tk=$(grep -o 'MAX_THINKING_TOKENS"[[:space:]]*:[[:space:]]*"[0-9]*' "$GSET" \
         2>/dev/null | grep -o '[0-9]*$' | head -1)
    [ -n "$tk" ] && tk="MAX_THINKING_TOKENS=$tk"
    row guard ok "wired in $GSET${tk:+ · $tk} · skill tree guarded"
    [ -z "$tk" ] && note "no MAX_THINKING_TOKENS — the other half of the fix, @references/parts/guard.md"
  else
    row guard off "not wired in $GSET"
    fix "pearde guard on — writes the block of @references/parts/guard.md into $GSET, then /hooks or restart (python3 $SKILL_ROOT/resources/pearde.py guard on)"
  fi
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
    row board off "no board — pearde init creates prds/"
    fix "python3 $SKILL_ROOT/resources/pearde.py init [<dir>] — a board, asking nothing"
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
    fix "python3 $SKILL_ROOT/resources/pearde.py init $(dirname "$BOARD") — writes it, language English unless --language"
  else
    # a missing `language:` reads at its default — English, the way every
    # other key reads, @references/settings.md. Not broken: said, not asked.
    LANG=$(grep -E '^[[:space:]]*language:' "$BOARD/settings.md" | head -1 | sed 's/.*language:[[:space:]]*//')
    row board ok "$BOARD · $N PRDs · language ${LANG:-English (default)}"
  fi
fi

# ── members: the boards a master merges ──────────────────────────────────────
# Only on a master board. A member that is not on disk is the one failure that
# matters: the plan silently loses a whole project, and the board looks smaller
# rather than broken.
if [ -n "$BOARD" ] && grep -qE '^[[:space:]]*members:' "$BOARD/settings.md" 2>/dev/null; then
  MEM=$(python3 "$DIR/board/plan.py" members "$BOARD" 2>/dev/null | grep .)
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
    BNAME=$(python3 -c "import sys;sys.path.insert(0,'$DIR/board');import plan;print(plan.board_name('$BOARD'))" 2>/dev/null)
    if grep -qE '^[[:space:]]*name:' "$BOARD/settings.md" 2>/dev/null; then
      row members ok "$NM member board(s) · ${NAMES}· $MPRDS member PRDs planned here · name $BNAME"
    else
      row members ok "$NM member board(s) · ${NAMES}· $MPRDS member PRDs planned here"
      printf '  %-11s %-7s %s\n' "" "" "name inferred as '$BNAME' — the round asks the user and writes name: to settings.md"
    fi
  fi
fi

# ── vision: where the board says it is going, and whether the names hold ─────
# `prds/vision.md` names the PRDs whose completion is the destination, and the
# plan orders toward them. A terminal or an edge end that names no PRD is a
# silent failure: the PRD it meant is off the axis, and the scan just says so
# in a number. `plan.py vision --check` is the one reader.
if [ -n "$BOARD" ]; then
  if [ ! -f "$BOARD/vision.md" ]; then
    row vision off "no vision.md — the board orders by dependency, weight and priority alone"
    fix "write $BOARD/vision.md from @references/templates/vision.md — one sentence, then terminals:"
  else
    VOUT=$(python3 "$DIR/board/plan.py" vision --check "$BOARD" 2>&1); VRC=$?
    if [ "$VRC" -eq 0 ]; then
      row vision ok "$VOUT"
    else
      NV=$(printf '%s\n' "$VOUT" | grep -c . )
      row vision broken "$NV name$([ "$NV" = 1 ] || echo s) in vision.md resolve$([ "$NV" = 1 ] && echo s) to no PRD"
      printf '%s\n' "$VOUT" | while IFS= read -r l; do
        [ -n "$l" ] && printf '  %-11s %-7s %s\n' "" "" "$l"
      done
      fix "name the PRD as needs: would — <prd>, @<member>/<prd>, or @<name>/<prd> for the board's own — or drop the line"
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
            if (st!="done" && st!="deferred" && st!="superseded") dlive++ }
          else { a++; if (st!="done" && st!="deferred" && st!="superseded") alive++ } }
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

# ── workflows: how a kind of job is done, and the library's shape ────────────
# The library is not a PRD folder: no state, nothing dispatched, invisible to
# scan. What can still be wrong is the format — a step naming an atomic nobody
# wrote is a worker sent nowhere, and it is silent from the outside. Unlike
# `memos:`, a `workflows:` pointing elsewhere is not a foreign system mirrored
# read-only: it is this library, shared between boards, and it gets the whole
# check wherever it lives.
if [ -n "$BOARD" ]; then
  WDIR=$(python3 -c "import sys;sys.path.insert(0,'$DIR');import workflows;d,e=workflows.workflows_dir('$BOARD');print(f'{d}\t{e}')" 2>/dev/null)
  WEXT="${WDIR##*	}"; WDIR="${WDIR%%	*}"
  if [ ! -d "${WDIR:-$BOARD/workflows}" ] && [ "$WEXT" != "True" ]; then
    row workflows off "no workflows/ — a job gets one when it repeats"
  elif ! command -v python3 >/dev/null 2>&1; then
    row workflows broken "workflows/ present, no python3 to read it"
    fix "install python3 — workflows.py is the only reader of the format"
  else
    WROWS=$(python3 "$DIR/workflows.py" list "$BOARD" 2>/dev/null)
    WW=$(printf '%s\n' "$WROWS" | awk '$2=="workflow"' | grep -c . )
    WA=$(printf '%s\n' "$WROWS" | awk '$2=="atomic"' | grep -c . )
    WSRC=""; [ "$WEXT" = "True" ] && WSRC=" · shared library at $WDIR"
    WPROB=$(python3 "$DIR/workflows.py" check "$BOARD" 2>&1)
    if [ -z "$WPROB" ]; then
      row workflows ok "$WW workflow$([ "$WW" = 1 ] || echo s) · $WA atomic$([ "$WA" = 1 ] || echo s) · the library checks out$WSRC"
    else
      NW=$(echo "$WPROB" | wc -l | tr -d ' ')
      row workflows broken "$WW workflow$([ "$WW" = 1 ] || echo s) · $WA atomic$([ "$WA" = 1 ] || echo s) · $NW problem$([ "$NW" = 1 ] || echo s)"
      echo "$WPROB" | while IFS= read -r l; do
        [ -n "$l" ] && printf '  %-11s %-7s %s\n' "" "" "$l"
      done
      fix "edit them to match @references/workflow.md — the keys are a closed set, and a step names a slug in the library"
    fi
  fi
fi

# ── briefs: the worker briefs, one source, every placeholder named ──────────
# A brief is printed by `pearde brief` from the blocks between
# `<!-- brief:<name> -->` … `<!-- /brief -->` in references/parts/workers.md.
# A marker missing or unterminated prints a brief with a hole in it, and a
# placeholder the table does not name is filled by nobody — both silent from
# the outside. brief.py `--check` is the one reader of that shape.
if [ ! -f "$DIR/board/brief.py" ]; then
  row briefs off "no resources/board/brief.py — nothing prints a brief yet"
  fix "land brief-is-printed: the module under resources/board/ exposing COMMANDS"
else
  BPROB=$(python3 "$DIR/board/brief.py" --check 2>&1)
  NB=$(grep -c '^<!-- brief:' "$SKILL_ROOT/references/parts/workers.md" 2>/dev/null | tr -d ' ')
  if [ -z "$BPROB" ]; then
    row briefs ok "$NB blocks in references/parts/workers.md · every placeholder named"
  else
    NP=$(echo "$BPROB" | wc -l | tr -d ' ')
    NB=${NB:-0}
    row briefs broken "$NB block$([ "$NB" = 1 ] || echo s) · $NP problem$([ "$NP" = 1 ] || echo s)"
    echo "$BPROB" | while IFS= read -r l; do
      [ -n "$l" ] && printf '  %-11s %-7s %s\n' "" "" "$l"
    done
    fix "close every <!-- brief:<name> --> with <!-- /brief -->, and name each placeholder in the table — references/parts/workers.md"
  fi
fi

# ── questions: what the board says it is waiting on you for ──────────────────
# A round that is not asked is indistinguishable from a board with nothing to
# ask. Both are silent. This row reads the shape of `## Questions` and
# `## Answers` in every prd.md: a heading with nothing under it, a question
# with no recommended answer, an answer to a question nobody wrote down, a
# PRD parked on the user that never says what it is asking, and a `needs:`
# holding prose — which `plan` resolves to nothing and reports nowhere.
# @resources/questions.py is the only reader of that format.
if [ -n "$BOARD" ] && [ "$N" -gt 0 ] 2>/dev/null; then
  if ! command -v python3 >/dev/null 2>&1; then
    row questions broken "PRDs present, no python3 to read the rounds"
    fix "install python3 — questions.py is the only reader of that format"
  else
    QSTAT=$(python3 "$DIR/questions.py" list "$BOARD" 2>/dev/null | wc -l | tr -d ' ')
    QBAD=$(python3 "$DIR/questions.py" check "$BOARD" 2>&1)
    if [ -z "$QBAD" ]; then
      if [ "$QSTAT" = 0 ]; then
        row questions ok "no PRD carries a round — nothing is waiting on you"
      else
        row questions ok "$QSTAT PRD$([ "$QSTAT" = 1 ] || echo s) carr$([ "$QSTAT" = 1 ] && echo ies || echo y) a round · each asks and offers an answer"
      fi
    else
      NQ=$(echo "$QBAD" | wc -l | tr -d ' ')
      row questions broken "$NQ round$([ "$NQ" = 1 ] || echo s) the user cannot act on"
      echo "$QBAD" | while IFS= read -r l; do
        [ -n "$l" ] && printf '  %-11s %-7s %s\n' "" "" "$l"
      done
      fix "write the fork and its recommended answers, or delete the heading — @references/drill.md"
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
    fix "python3 $DIR/board/serve.py ensure $BOARD"
    if [ "$FIX" = 1 ] && python3 "$DIR/board/serve.py" ensure "$BOARD" >/dev/null 2>&1; then
      did "view service started"
    fi
  elif printf '%s' "$SRV" | grep -qF "\"$BOARD\"" \
       || printf '%s' "$SRV" | grep -qF "\"$PBOARD\""; then
    BN=$(printf '%s' "$SRV" | tr '{' '\n' | grep -F "\"$BOARD\"" \
         | sed -n 's/.*"name": "\([^"]*\)".*/\1/p' | head -1)
    row view ok "watching · http://127.0.0.1:$SRV_PORT/board/${BN:-?}"
  else
    row view broken "the service is up but this board is not registered"
    fix "python3 $DIR/board/serve.py ensure $BOARD"
    if [ "$FIX" = 1 ] && python3 "$DIR/board/serve.py" ensure "$BOARD" >/dev/null 2>&1; then
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
    fix "python3 $DIR/board/plan.py plan $BOARD"
  else
    row plan ok "planned $PLANNED"
  fi
fi

# ── harnesses: the board's own acceptance checks, actually run ───────────────
# Every PRD is closed against its own verify.sh, and until this row existed
# nothing ran one: `grep -rn verify.sh resources/ .claude` returned nothing,
# there is no CI and no hook, and every green total on record was a person
# remembering to type the command. So doctor runs them.
#
# The expected count is the harness's own and is never recorded here. A
# harness that pins its denominator — `[ "$((PASS+FAIL))" = 39 ] || no ...` —
# fails loudly when a check is dropped; one that does not prints a smaller
# total and exits 0, which is indistinguishable from success. So a harness
# that does not pin one is reported as unpinned rather than trusted, and its
# pass does not make this row green on its own account. A recorded expected
# total would be a second copy of a number the file already carries, and this
# board has twice paid for that shape.
#
# Opt-in, because it is slow: the row is the only one here measured in tens of
# seconds, and doctor is run to answer "is this wired up" in a second.
if [ -n "$BOARD" ]; then
  HLIST=$(find "$BOARD" -name verify.sh 2>/dev/null | sort)
  HN=$(printf '%s\n' "$HLIST" | grep -c .)
  HON=0
  [ "$HFLAG" = 1 ] && HON=1
  grep -qE '^[[:space:]]*harnesses:[[:space:]]*(on|yes|true)[[:space:]]*$' \
       "$BOARD/settings.md" 2>/dev/null && HON=1
  if [ "$HN" = 0 ]; then
    row harnesses off "no verify.sh under $BOARD — a PRD gets one when it is specced"
  elif [ -n "${PEARDE_HARNESSES:-}" ]; then
    # A harness may run doctor — two on this board do. Without this guard a
    # board with `harnesses: on` runs doctor, which runs the harness, which
    # runs doctor, forever.
    row harnesses off "$HN harness$([ "$HN" = 1 ] || echo es) · not run inside a harness"
  elif [ "$HON" = 0 ]; then
    row harnesses off "$HN harness$([ "$HN" = 1 ] || echo es) · not run — this row costs tens of seconds"
    fix "harnesses: on in $BOARD/settings.md, or one run: bash $DIR/doctor.sh --harnesses $START"
  else
    HG=0; HU=0; HF=0; HFAILED=""; HUNPINNED=""
    HT0=$(date +%s)
    HTMP=$(mktemp -d)
    while IFS= read -r h; do
      [ -n "$h" ] || continue
      rel="${h#"$START"/}"; rel="${rel#"$SKILL_ROOT"/}"
      PEARDE_HARNESSES=1 bash "$h" </dev/null >"$HTMP/out" 2>&1
      hrc=$?
      # The pin is read as the idiom, not as semantics: a test comparing the
      # harness's own executed total against an integer literal.
      if grep -qE '\$\(\([[:space:]]*[Pp][Aa][Ss][Ss][[:space:]]*\+[[:space:]]*[Ff][Aa][Ii][Ll][[:space:]]*\)\)[^=]*(=|-eq)[[:space:]]*"?[0-9]+' "$h"; then
        pinned=1
      else
        pinned=0
      fi
      if [ "$hrc" != 0 ]; then
        HF=$((HF + 1))
        # the marker every harness on this board prints, at the start of its
        # own line — matching `FAIL` anywhere on a line quotes a passing
        # check whose name happens to contain the word
        first=$(grep -m1 -E '^[[:space:]]*FAIL' "$HTMP/out" | sed 's/^[[:space:]]*//')
        [ -z "$first" ] && first=$(tail -1 "$HTMP/out" | sed 's/^[[:space:]]*//')
        HFAILED="$HFAILED
$rel — exit $hrc${first:+ · $first}"
      elif [ "$pinned" = 1 ]; then
        HG=$((HG + 1))
      fi
      [ "$pinned" = 0 ] && { HU=$((HU + 1)); HUNPINNED="$HUNPINNED
$rel"; }
    done <<EOF
$HLIST
EOF
    rm -rf "$HTMP"
    HSECS=$(( $(date +%s) - HT0 ))
    HDET="$HG of $HN green · ${HSECS}s"
    [ "$HU" -gt 0 ] && HDET="$HG of $HN green · $HU unpinned · ${HSECS}s"
    if [ "$HF" -gt 0 ]; then
      row harnesses broken "$HDET · $HF failed"
      printf '%s\n' "$HFAILED" | while IFS= read -r l; do [ -n "$l" ] && note "$l"; done
      fix "run the named harness and read its FAIL lines: bash $START/<path above>"
    else
      row harnesses ok "$HDET"
    fi
    if [ "$HU" -gt 0 ]; then
      printf '%s\n' "$HUNPINNED" | grep -v '^$' | head -5 \
        | while IFS= read -r l; do note "unpinned · $l"; done
      [ "$HU" -gt 5 ] && note "unpinned · … and $((HU - 5)) more"
      note "unpinned: the total it prints is the total it ran, so a dropped check reads as success"
      note "pin it: [ \"\$((PASS+FAIL))\" = <n> ] || no \"expected <n> checks, ran \$((PASS+FAIL))\""
    fi
  fi
fi

echo
if [ "$FIX" = 1 ] && [ "$REPAIRED" = 1 ]; then
  echo "pearde: repaired — re-checking."
  echo
  if [ "$HFLAG" = 1 ]; then exec bash "$0" --harnesses "$START"; else exec bash "$0" "$START"; fi
fi
[ "$BROKEN" = 1 ] && echo "pearde: something is installed and not working — the fixes are above." && exit 1
# What doctor cannot see is where the skills were installed — that is the
# reader's setup, and @references/install.md is the step. So the last line
# claims only what was checked.
echo "pearde: every part this repo owns checks out."
