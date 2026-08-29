#!/usr/bin/env bash
# workflow-seed — the first library, measured.
#
# Run from the repo root:  bash prds/workflows-on-the-board/workflow-seed/probe/verify.sh
#
# Every fixture this harness needs is built in a directory made at run time and
# removed on exit. Nothing it writes lands under prds/ — a fixture prd.md there
# would become a real PRD, and a probe at the repo root would redden the map
# check for every later PRD.
set -u
cd "$(dirname "$0")/../../../.." || exit 2
ROOT=$PWD
BOARD=$ROOT/prds
WF=$ROOT/resources/workflows.py
LIB=$BOARD/workflows

PASS=0; FAIL=0
t() { # t <name> <expected> <actual>
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); printf '  ok   %s\n' "$1"
  else FAIL=$((FAIL+1)); printf '  FAIL %s\n       want: %s\n       got:  %s\n' "$1" "$2" "$3"; fi
}
ok() { # ok <name> <cmd...>  — passes when the command exits 0
  local n=$1; shift
  if "$@" >/dev/null 2>&1; then PASS=$((PASS+1)); printf '  ok   %s\n' "$n"
  else FAIL=$((FAIL+1)); printf '  FAIL %s  (exit %s)\n' "$n" "$?"; fi
}
no() { # no <name> <cmd...> — passes when the command exits non-zero
  local n=$1; shift
  if "$@" >/dev/null 2>&1; then FAIL=$((FAIL+1)); printf '  FAIL %s  (exited 0, expected non-zero)\n' "$n"
  else PASS=$((PASS+1)); printf '  ok   %s\n' "$n"; fi
}

D=$(mktemp -d); trap 'rm -rf "$D"' EXIT

echo
echo "── the library exists and the reader is silent on it ────────────────────"

t "prds/workflows/ is a directory" "yes" "$([ -d "$LIB" ] && echo yes || echo no)"
OUT=$(python3 "$WF" check "$BOARD" 2>&1); RC=$?
t "workflows.py check prds prints nothing" "" "$OUT"
t "workflows.py check prds exits 0" "0" "$RC"

LIST=$(python3 "$WF" list "$BOARD" 2>/dev/null)
NW=$(printf '%s\n' "$LIST" | awk '$2=="workflow"' | grep -c .)
NA=$(printf '%s\n' "$LIST" | awk '$2=="atomic"'   | grep -c .)
t "at least three workflows (found $NW)" "yes" "$([ "$NW" -ge 3 ] && echo yes || echo no)"
t "at least six atomics (found $NA)"     "yes" "$([ "$NA" -ge 6 ] && echo yes || echo no)"
t "every .md in the library is one of the two kinds" \
  "$(ls "$LIB"/*.md | wc -l | tr -d ' ')" "$((NW+NA))"

echo
echo "── runs and updated, as a collect leaves them ───────────────────────────"

# A collect increments runs, so a check that pins runs: 0 is true only until
# the library is first used and can never be true again. What holds on both
# sides of a collect is the shape: an integer >= 0 on every file, the same
# integer in the list column, and an updated: that is a date and not older
# than the day the file was written. A hand-edited library still fails these.
#
# The census enumerates the directory, not a list this harness already holds.
BADRUNS=""
for f in "$LIB"/*.md; do
  v=$(awk '/^---$/{n++; next} n==1 && /^runs:/{sub(/^runs:[[:space:]]*/,""); print; exit}' "$f")
  case "$v" in ''|*[!0-9]*) BADRUNS="$BADRUNS $(basename "$f")=${v:-<absent>}" ;; esac
done
t "every file carries runs as an integer >= 0" "" "$BADRUNS"

BADCOL=$(printf '%s\n' "$LIST" | awk '$3 !~ /^[0-9]+$/ {printf "%s=%s ", $1, $3}')
t "list prints an integer >= 0 in the runs column on every row" "" "${BADCOL% }"

# The file's runs and the list column are one number read two ways.
DRIFT=""
while read -r slug kind runs rest; do
  [ -n "${slug:-}" ] || continue
  v=$(awk '/^---$/{n++; next} n==1 && /^runs:/{sub(/^runs:[[:space:]]*/,""); print; exit}' "$LIB/$slug.md")
  [ "$v" = "$runs" ] || DRIFT="$DRIFT $slug:file=$v,list=$runs"
done <<< "$LIST"
t "the runs column never disagrees with the file's own runs" "" "$DRIFT"

# updated: is optional — a run that changed no text writes none — but when it
# is there it is a date, and no file was updated before it was written.
BADUPD=""
for f in "$LIB"/*.md; do
  u=$(awk '/^---$/{n++; next} n==1 && /^updated:/{sub(/^updated:[[:space:]]*/,""); print; exit}' "$f")
  [ -n "$u" ] || continue
  d=$(awk '/^---$/{n++; next} n==1 && /^date:/{sub(/^date:[[:space:]]*/,""); print; exit}' "$f")
  case "$u" in
    [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
    *) BADUPD="$BADUPD $(basename "$f")=$u"; continue ;;
  esac
  if [ "$u" \< "$d" ]; then BADUPD="$BADUPD $(basename "$f")=$u<date:$d"; fi
done
t "every updated: is a date and none predates its own date:" "" "$BADUPD"

echo
echo "── every atomic is named by at least one workflow ───────────────────────"

# Census: the population is every atomic file on disk, enumerated here, not the
# ones this harness happens to know. Each must appear in some Steps table.
WFS=$(printf '%s\n' "$LIST" | awk '$2=="workflow"{print $1}')
ATOMS=$(printf '%s\n' "$LIST" | awk '$2=="atomic"{print $1}')
STEPCELLS=$(for w in $WFS; do
  awk '/^## Steps/{on=1;next} /^## /{on=0} on' "$LIB/$w.md" \
    | sed -n 's/^|[^|]*|[[:space:]]*`\([a-z0-9-]*\)`.*/\1/p'
done | sort -u)
ORPHAN=""
for a in $ATOMS; do
  printf '%s\n' "$STEPCELLS" | grep -qx "$a" || ORPHAN="$ORPHAN $a"
done
t "no atomic is unreferenced by every workflow" "" "$ORPHAN"
t "the atomic census counted every atomic on disk" \
  "$(ls "$LIB"/*.md | wc -l | tr -d ' ')" "$((NW + $(printf '%s\n' "$ATOMS" | grep -c .)))"

# and the other direction: no Steps cell names a file that is not an atomic
DANGLE=""
for c in $STEPCELLS; do
  printf '%s\n' "$ATOMS" | grep -qx "$c" || DANGLE="$DANGLE $c"
done
t "no step names a workflow or a missing file as its atomic" "" "$DANGLE"

echo
echo "── the bodies the format requires ───────────────────────────────────────"

MISSING=""
for a in $ATOMS; do
  for s in "## Do" "## Done when" "## Fails when"; do
    grep -qx "$s" "$LIB/$a.md" || MISSING="$MISSING $a:$s"
  done
done
t "every atomic has Do, Done when and Fails when" "" "$MISSING"

EMPTY=""
for a in $ATOMS; do
  n=$(awk '/^## Do$/{on=1;next} /^## /{on=0} on && NF' "$LIB/$a.md" | grep -c .)
  [ "$n" -ge 1 ] || EMPTY="$EMPTY $a:Do"
  n=$(awk '/^## Done when$/{on=1;next} /^## /{on=0} on && NF' "$LIB/$a.md" | grep -c .)
  [ "$n" -ge 1 ] || EMPTY="$EMPTY $a:Done"
done
t "no atomic has an empty Do or Done when" "" "$EMPTY"

# `## Fails when` grows from runs, so the rule is conditional on the file's own
# runs and not on the library's age: a file that has never been in a run has
# learned nothing and a data row on it is invented, while a file that has been
# in one may carry rows or none — a clean run adds nothing.
NONEMPTY=""
for a in $ATOMS; do
  r=$(awk '/^---$/{n++; next} n==1 && /^runs:/{sub(/^runs:[[:space:]]*/,""); print; exit}' "$LIB/$a.md")
  n=$(awk '/^## Fails when$/{on=1;next} /^## /{on=0} on && /^\|/' "$LIB/$a.md" \
      | grep -vc '^|[[:space:]]*seen\|^|[-| ]*|$')
  if [ "$r" = "0" ] && [ "$n" != "0" ]; then NONEMPTY="$NONEMPTY $a=$n@runs:0"; fi
done
t "no atomic carries a Fails when data row while its own runs is 0" "" "$NONEMPTY"

# The header is there either way, so a row a run learns has somewhere to land.
NOHDR=""
for a in $ATOMS; do
  awk '/^## Fails when$/{on=1;next} /^## /{on=0} on' "$LIB/$a.md" \
    | grep -q '^|[[:space:]]*seen[[:space:]]*|' || NOHDR="$NOHDR $a"
done
t "every atomic's Fails when carries the header row" "" "$NOHDR"

NOUSE=""
for w in $WFS; do
  grep -qx "## Use when" "$LIB/$w.md" || NOUSE="$NOUSE $w"
  awk '/^## Steps/{on=1;next} /^## /{on=0} on' "$LIB/$w.md" | grep -q '^|' \
    || NOUSE="$NOUSE $w:Steps"
done
t "every workflow has Use when and a Steps table" "" "$NOUSE"

# `## Use when` names the near-miss and the slug that fits it, so the lookup
# has a boundary rather than only a match.
NOMISS=""
for w in $WFS; do
  awk '/^## Use when$/{on=1;next} /^## /{on=0} on' "$LIB/$w.md" \
    | grep -qi 'not when' || NOMISS="$NOMISS $w"
done
t "every workflow's Use when names a near-miss it does not fit" "" "$NOMISS"

echo
echo "── the steps grammar, and a back-edge someone would take ────────────────"

FAILCOL() { awk '/^## Steps/{on=1;next} /^## /{on=0} on && /^\|/' "$LIB/$1.md" \
  | awk -F'|' 'NF>4 {gsub(/^[ \t]+|[ \t]+$/,"",$5); gsub(/`/,"",$5); print $5}' \
  | grep -v '^on failure$' | grep -v '^[-]*$'; }

FIRSTNOTSTOP=""; ALLONE=""; FWD=""
for w in $WFS; do
  col=$(FAILCOL "$w")
  first=$(printf '%s\n' "$col" | head -1)
  [ "$first" = "stop" ] || FIRSTNOTSTOP="$FIRSTNOTSTOP $w=$first"
  rest=$(printf '%s\n' "$col" | tail -n +2 | sort -u | grep -c .)
  [ "$rest" -ge 2 ] || ALLONE="$ALLONE $w"
  i=0
  while IFS= read -r c; do
    i=$((i+1))
    case "$c" in
      stop) ;;
      "→ "*) n=${c#→ }; [ "$n" -lt "$i" ] && [ "$n" -ge 1 ] || FWD="$FWD $w:$i=$c" ;;
      *) FWD="$FWD $w:$i=$c" ;;
    esac
  done <<< "$col"
done
t "step 1 of every workflow is stop — there is nowhere earlier to go" "" "$FIRSTNOTSTOP"
t "no workflow is a list: each has two or more distinct back-edge targets" "" "$ALLONE"
t "no on-failure cell is a forward jump or an unknown word" "" "$FWD"

echo
echo "── brief prints every step with its atomic under it ─────────────────────"

for w in $WFS; do
  B=$(python3 "$WF" brief "$w" "$BOARD" 2>&1); RC=$?
  n=$(printf '%s\n' "$B" | grep -c '^### ')
  rows=$(FAILCOL "$w" | grep -c .)
  t "brief $w exits 0" "0" "$RC"
  t "brief $w prints one heading per step" "$rows" "$n"
  d=$(printf '%s\n' "$B" | grep -c '^#### Do$')
  t "brief $w inlines an atomic body under each step" "$rows" "$d"
  printf '%s\n' "$B" | grep -q 'no `.*` in the library' \
    && { FAIL=$((FAIL+1)); printf '  FAIL brief %s sends a step nowhere\n' "$w"; } \
    || { PASS=$((PASS+1)); printf '  ok   brief %s sends no step nowhere\n' "$w"; }
done

echo
echo "── the seed writes no tool, agent, hook or vendor name ──────────────────"

# A vendor NAME, not a path that contains one and not a word of English.
# `workflow-format`'s rule is "No agent, tool, hook or vendor name. Commands
# and files." — so a path IS allowed, and the first row to name `.claude/` or
# `github.com/…` tripped a check that could not tell the two apart. `agent`
# and `hook` are gone from the pattern for the same reason: "a git hook", "the
# agent that ran it" are ordinary English and a `## Fails when` row will say
# them. Skipped: anything preceded by `/` or `.`, and anything inside
# backticks — both are how this library spells a command or a file.
HITS=$(grep -rniE '(^|[^/.`[:alnum:]-])(claude|anthropic|openai|copilot|cursor|codex|gpt|chatgpt|llm|vendor|npm|docker)([^/.`[:alnum:]-]|$)' "$LIB" \
       | grep -vE '`[^`]*(claude|anthropic|openai|copilot|cursor|codex|gpt|chatgpt|llm|npm|docker)[^`]*`' || true)
t "no agent, tool, hook or vendor name anywhere in the library" "" "$HITS"

echo
echo "── the carried obligation: runs means one collect, one count ────────────"

# The four named sites carry the settled reading.
ok "workflow.md frontmatter row says one collect, one count" \
   grep -qF 'one collect, one count' "$ROOT/references/workflow.md"
ok "workflow.md prose says runs counts runs, not traversals" \
   grep -qF 'not the traversals inside one' "$ROOT/references/workflow.md"
ok "templates/atomic.md comment says one collect, one count" \
   grep -qF 'one collect, one count' "$ROOT/references/templates/atomic.md"
ok "templates/workflow.md comment says one collect, one count" \
   grep -qF 'one collect, one count' "$ROOT/references/templates/workflow.md"

# and the rejected reading survives at none of them, nor anywhere else the
# skill ships. `prds/` is the board — another PRD's body is not this PRD's to
# edit, and the copies there are named in the report instead.
LOOSE=$(grep -rn "times followed" "$ROOT/references" "$ROOT/resources" 2>/dev/null || true)
t "the phrase 'times followed' ships nowhere under references/ or resources/" "" "$LOOSE"
LOOSE2=$(grep -rnE "times (the|a) file was followed" "$ROOT/references" "$ROOT/resources" 2>/dev/null || true)
t "no 'times the file was followed' under references/ or resources/" "" "$LOOSE2"

# parts/workflows.md is the settling document and must still say it.
SETTLED=$(tr '\n' ' ' < "$ROOT/references/parts/workflows.md" | grep -c 'One collect, *one count')
t "parts/workflows.md still carries the settled reading" "1" "$SETTLED"

echo
echo "── the check can fail: negative controls, all in a temp dir ─────────────"

mkdir -p "$D/prds/workflows"
cp "$LIB"/*.md "$D/prds/workflows/"
ok "a copy of the library in a temp board is also clean" \
   python3 "$WF" check "$D/prds"

# A control that substitutes on a value the library happens to hold stops
# biting the moment that value moves: the first collect turned every
# `runs: 0` into `runs: 1`, the substitution below used to match nothing, no
# invalid file was ever written, and `check` correctly exited 0. Each control
# now rewrites the key whatever it holds and names its victim from the library
# at run time — and each asserts the fixture really changed before asserting
# the check rejects it, so a control that stops breaking anything says so
# instead of passing quietly.
VICTIM=$(printf '%s\n' "$ATOMS" | head -1)
VW=$(printf '%s\n' "$WFS" | head -1)
BADF=$D/prds/workflows/$VICTIM.md

# a runs value that is not an integer >= 0
sed -i.bak 's/^runs:.*$/runs: -1/' "$BADF" && rm -f "$D/prds/workflows/"*.bak
t "the runs fixture really differs from the library file it was copied from" \
  "differs" "$(cmp -s "$BADF" "$LIB/$VICTIM.md" && echo same || echo differs)"
no "check rejects runs: -1" python3 "$WF" check "$D/prds"
OUT=$(python3 "$WF" check "$D/prds" 2>&1)
t "and says which file and which key" "yes" \
  "$(printf '%s' "$OUT" | grep -q "$VICTIM.md: runs" && echo yes || echo no)"
# Restored by copying the pristine file back, never by a reverse substitution
# on a value — the reverse sed hard-coded runs: 0 the same way.
cp "$LIB/$VICTIM.md" "$BADF"
ok "restored from the library, and clean again" python3 "$WF" check "$D/prds"

# a step naming a file that is not there — the cell to corrupt is read out of
# the workflow, so renaming an atomic cannot make this control vacuous
CELL=$(awk '/^## Steps/{on=1;next} /^## /{on=0} on' "$LIB/$VW.md" \
       | sed -n 's/^|[^|]*|[[:space:]]*`\([a-z0-9-]*\)`.*/\1/p' | head -1)
t "a step cell was found in $VW to corrupt" "yes" \
  "$([ -n "$CELL" ] && echo yes || echo no)"
sed -i.bak "s/\`$CELL\`/\`$CELL-no-such-file\`/" "$D/prds/workflows/$VW.md" && rm -f "$D/prds/workflows/"*.bak
t "the dangling-step fixture really differs from the library file" "differs" \
  "$(cmp -s "$D/prds/workflows/$VW.md" "$LIB/$VW.md" && echo same || echo differs)"
no "check rejects a step naming no file in the library" python3 "$WF" check "$D/prds"
cp "$LIB/$VW.md" "$D/prds/workflows/$VW.md"
ok "restored from the library, and clean again after the dangling step" \
   python3 "$WF" check "$D/prds"

# a step naming an atomic as a route — the slug comes from the atomic census
mkdir -p "$D/prds/naming-an-atomic"
printf -- '---\nstate: open\nworkflow: %s\n---\n\n# fixture\n' "$VICTIM" \
  > "$D/prds/naming-an-atomic/prd.md"
no "check rejects a PRD routed to an atomic" python3 "$WF" check "$D/prds"
OUT=$(python3 "$WF" check "$D/prds" 2>&1)
t "and says a route was asked for and a single step was found" "yes" \
  "$(printf '%s' "$OUT" | grep -q 'a route was asked for' && echo yes || echo no)"

# a PRD routed to a real workflow resolves
printf -- '---\nstate: open\nworkflow: %s\n---\n\n# fixture\n' "$VW" \
  > "$D/prds/naming-an-atomic/prd.md"
ok "a PRD routed to a real workflow in this library resolves" python3 "$WF" check "$D/prds"

echo
echo "── nothing this PRD wrote leaks onto the board or the repo root ─────────"

STRAY=$(find "$BOARD" -name prd.md -path '*/probe/*' 2>/dev/null || true)
t "no fixture prd.md under any probe/ on the board" "" "$STRAY"
# The rule this guards is this PRD's own attempt-the-build: probe code lives
# under prds/<prd>/probe/, NEVER at the repo root. That forbids DROPPING a new
# file at the root. It says nothing about a committed root file being edited —
# and the earlier form conflated the two, so it went red when a neighbour
# modified the tracked `index.md` to map its own new files. An untracked path
# at the root is the litter the rule means; a tracked one is somebody working.
ROOTNEW=$(git -C "$ROOT" status --porcelain --untracked-files=all \
          | awk '$1=="??"{print $NF}' | grep -E '^[^/]+$' || true)
t "this run dropped no new file at the repo root" "" "$ROOTNEW"
ROOTMOD=$(git -C "$ROOT" status --porcelain --untracked-files=all \
          | awk '$1!="??"{print $NF}' | grep -E '^[^/]+$' || true)
if [ -n "$ROOTMOD" ]; then
  printf '  note tracked root files modified by other work — reported, not gated: %s\n' \
    "$(printf '%s' "$ROOTMOD" | tr '\n' ' ')"
fi

IDX=$(python3 "$ROOT/resources/index.py" check 2>&1)
# Scoped first, and anchored FILE BY FILE. Two bugs were found here, one
# level apart, and both were a pattern claiming more than this PRD owns:
#   - `prds/workflows` unanchored matched the substring inside another node's
#     resources/board/example/prds/workflows/*.md;
#   - `references/templates/` anchored but left as a DIRECTORY PREFIX, which
#     claims every file anyone ever puts in that directory. It caught
#     references/templates/vision.md, which is another session's, and
#     spec.md and prd.md belong to workflow-attach.
# A gate that names a directory makes a claim about every future file in it.
# This PRD writes exactly two files under references/, and they are named.
#
# `prds/workflows/` stays a prefix deliberately: the whole directory is this
# PRD's deliverable, so every .md that appears in it is by definition ours.
OWNED='^(prds/workflows/[^/]+\.md|references/workflow\.md|references/templates/atomic\.md|references/templates/workflow\.md)([[:space:]]|$)'
MINE=$(printf '%s\n' "$IDX" | grep -E "$OWNED" || true)
t "index.py check names no path this PRD wrote" "" "$MINE"

# Nothing else is gated. An earlier version asserted the known pre-existing
# scout-snapshot line was still present — which gates this PRD on a NEIGHBOUR
# NOT FIXING THEIR OWN BUG, and duly went red the moment
# `snapshots-fold-to-one-row` wrote its manifest row. A path this PRD does not
# own is not ours to require present any more than to require absent.
#
# Everything the map names that this PRD did not write belongs to other work.
# The contract asks for it reported separately, and this is that report.
OTHERS=$(printf '%s\n' "$IDX" | grep -vE "$OWNED" || true)
if [ -n "$OTHERS" ]; then
  printf '  note unmapped paths owned by other work — reported, not gated:\n'
  printf '%s\n' "$OTHERS" | sed 's/ is on disk.*//; s/^/         /'
fi

echo
echo "── doctor reads the library ─────────────────────────────────────────────"

DOC=$(bash "$ROOT/resources/doctor.sh" 2>&1 | grep '^  workflows')
t "doctor's workflows row is ok" "yes" \
  "$(printf '%s' "$DOC" | grep -q '^  workflows *ok' && echo yes || echo no)"
t "doctor counts the workflows this seed wrote" "yes" \
  "$(printf '%s' "$DOC" | grep -q "$NW workflows · $NA atomics · the library checks out" && echo yes || echo no)"
# `workflows` is the row this PRD owns, and it is the one this gate is about.
BROKEN=$(bash "$ROOT/resources/doctor.sh" 2>&1 | awk '$2=="broken"{print $1}' | tr '\n' ' ' | sed 's/ $//')
t "the doctor row this PRD owns is not broken" "yes" \
  "$(printf '%s' "$BROKEN" | grep -qw workflows && echo no || echo yes)"
# Every other row is other work in flight, and pinning the exact set of broken
# rows gates this PRD on all of it: `index` was broken at baseline for a scout
# snapshot, and `memos` went broken during this run when another session
# renamed a PRD one of its memos points at. Neither is reachable from this
# footprint, so both are reported rather than failed on — the same rule this
# library's own run-the-scoped-verify states, applied to this harness.
OTHERROWS=$(printf '%s' "$BROKEN" | tr ' ' '\n' | grep -vx 'workflows' | grep -v '^$' \
            | tr '\n' ' ' | sed 's/ $//')
if [ -n "$OTHERROWS" ]; then
  printf '  note doctor rows broken outside this footprint — reported, not gated: %s\n' "$OTHERROWS"
fi

echo
echo "$((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" = 0 ]
