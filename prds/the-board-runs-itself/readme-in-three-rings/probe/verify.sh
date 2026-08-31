#!/usr/bin/env bash
# verify.sh — the README is what the contract says, and true to the code.
#
# One line per assertion, a count at the end. Reads README.md,
# references/parts/states.md, references/language.md, skills/pearde.md and
# index.md; runs index.py check; then hands off to quickstart.sh, which runs
# the five lines on a temp dir. `bash verify.sh --no-run` skips that last
# part (it starts a daemon on a spare port and takes a few seconds).
set -u
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
README="$ROOT/README.md"; STATES="$ROOT/references/parts/states.md"
S="$(mktemp -d)"; trap 'rm -rf "$S"' EXIT
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); }
bad()  { FAIL=$((FAIL+1)); echo "FAIL: $1"; }
eq()   { [ "$2" = "$3" ] && ok || bad "$1 — got '$2', want '$3'"; }
has()  { printf '%s' "$2" | grep -qF -- "$3" && ok || bad "$1 — missing '$3'"; }
lacks(){ printf '%s' "$2" | grep -qF -- "$3" && bad "$1 — has '$3'" || ok; }

echo "A. size and order"
LINES="$(wc -l < "$README" | tr -d ' ')"
[ "$LINES" -le 200 ] && ok || bad "A README is $LINES lines, over 200"
HEADS="$(grep '^## ' "$README" | tr '\n' '|')"
eq "A the seven headings, in the contract's order" "$HEADS" \
   "## In sixty seconds|## What is on disk|## The nine states|## The round|## Three rings|## Glossary|## Addressing|"

echo "B. the quickstart is five lines"
QS="$(awk '/^## In sixty seconds/{f=1;next} f&&/^```sh/{g=1;next} g&&/^```/{exit} g' "$README")"
eq "B five lines" "$(printf '%s\n' "$QS" | wc -l | tr -d ' ')" "5"
has "B line 1 is install --apply" "$(printf '%s\n' "$QS" | sed -n 1p)" "resources/pearde.py install --apply"
has "B line 2 is init --example" "$(printf '%s\n' "$QS" | sed -n 2p)" "pearde init --example"
has "B line 3 is add" "$(printf '%s\n' "$QS" | sed -n 3p)" "pearde add"
eq  "B line 4 is the bare command" "$(printf '%s\n' "$QS" | sed -n 4p)" "pearde"
eq  "B line 5 is view" "$(printf '%s\n' "$QS" | sed -n 5p)" "pearde view"

echo "C. the diagram names the nine states, and no other"
awk '/^```mermaid/{f=1;next} f&&/^```/{exit} f' "$README" > "$S/mermaid"
eq "C one mermaid block" "$(grep -c '^```mermaid' "$README")" "1"
has "C it is a state diagram" "$(head -1 "$S/mermaid")" "stateDiagram-v2"
# every state named on an arrow, either side, minus the start/end marker
grep -- '-->' "$S/mermaid" | sed 's/:.*//' | tr -s ' ' '\n' | grep -v '^$' | grep -vE '^(-->|\[\*\])$' | sort -u > "$S/diagram-states"
# the nine, off the first column of states.md's table
awk -F'|' '/^\| `[a-z]+` +\|/{gsub(/[` ]/,"",$2); print $2}' "$STATES" | sort -u > "$S/table-states"
eq "C states.md names nine" "$(wc -l < "$S/table-states" | tr -d ' ')" "9"
eq "C the diagram names nine" "$(wc -l < "$S/diagram-states" | tr -d ' ')" "9"
eq "C the two sets are equal" "$(diff "$S/table-states" "$S/diagram-states" | wc -l | tr -d ' ')" "0"
# every arrow carries a command from handles.md's Command column — the cell
# is `pearde <cmd>` exactly or with flags after (`pearde add [--dry]`)
awk -F'`' '/`pearde [a-z]+/{ for(i=2;i<=NF;i++) if($i ~ /^pearde [a-z]+( |$|\[)/){ split($i,a," "); print a[2] } }' "$ROOT/references/parts/handles.md" | sort -u > "$S/commands"
NOCMD=0
while IFS= read -r line; do
  case "$line" in *'-->'*) ;; *) continue;; esac
  case "$line" in *'--> [*]'*) continue;; esac       # the terminal arrow
  cmd="$(printf '%s' "$line" | sed -n 's/.*: *\([a-z]*\).*/\1/p')"
  grep -qx "$cmd" "$S/commands" || { NOCMD=$((NOCMD+1)); echo "  no command on: $line"; }
done < "$S/mermaid"
eq "C every arrow carries a pearde command" "$NOCMD" "0"
lacks "C no prose beside the picture" "$(awk '/^## The nine states/{f=1;next} f&&/^## /{exit} f' "$README" | grep -vE '^```|^ |^stateDiagram|^$')" "."

echo "D. the round is loop.md's seven rows"
awk '/^\| step \| command/{f=1} f&&/^\| [1-7] /{print} f&&/^$/{f=0}' "$README" > "$S/readme-rows"
awk '/^\| step \| command/{f=1} f&&/^\| [1-7] /{print} f&&/^$/{f=0}' "$ROOT/references/parts/loop.md" > "$S/loop-rows"
eq "D seven rows in the README" "$(wc -l < "$S/readme-rows" | tr -d ' ')" "7"
eq "D the rows are loop.md's, byte for byte" "$(diff "$S/loop-rows" "$S/readme-rows" | wc -l | tr -d ' ')" "0"

echo "E. the rings, the glossary, the addressing"
RINGS="$(awk '/^## Three rings/{f=1;next} f&&/^## /{exit} f' "$README")"
has "E core" "$RINGS" "**Core**"; has "E advisors" "$RINGS" "**Advisors**"; has "E tools" "$RINGS" "**Tools**"
has "E the one-question table moved under core" "$RINGS" "| what the round does next | @references/parts/loop.md |"
has "E the scope table moved under core" "$RINGS" "| reading the board | "
eq  "E the one-question table has its eleven rows" "$(printf '%s\n' "$RINGS" | grep -c '^| what\|^| which\|^| who \|^| putting')" "11"
for k in loop drill memos workflows personas consult report master doctor guard statusline scout install; do
  has "E the ring ends in @@$k" "$RINGS" "\`@@$k\`"
done
GLOSS="$(awk '/^## Glossary/{f=1;next} f&&/^## /{exit} f' "$README" | grep -c '^| [A-Za-z]')"
[ "$GLOSS" -le 21 ] && ok || bad "E the glossary has $GLOSS rows, over twenty"
for w in PRD spec box footprint needs weight axis band collect claim memo workflow atomic persona consult drill master member guard doctor; do
  grep -q "^| $w |" "$README" && ok || bad "E glossary lacks $w"
done
has "E addressing keeps @ and @@" "$(awk '/^## Addressing/{f=1;next} f' "$README")" '`@<path>` is one file. `@@<keyword>` is one scope.'

echo "F. every claim is true to the code"
# on a copy of the example board, never the live one: `add` writes a PRD
python3 "$ROOT/resources/board/plan.py" example "$S/copy" >/dev/null
has "F add as printed — no --as, no PEARDE_AS — files it as engineer, so the quickstart row says so" "$(env -u PEARDE_AS python3 "$ROOT/resources/board/transitions.py" add "quickstart probe" --board "$S/copy" 2>&1)" "· as engineer"
eq  "F the daemon's default port is 8443" "$(grep -c '127.0.0.1:8443' "$README")" "2"
eq  "F twelve skills" "$(ls "$ROOT/skills"/*.md | wc -l | tr -d ' ')" "12"
has "F init's first line names the language" "$(sed -n '/^def cmd_init/,/^def /p' "$ROOT/resources/board/init.py")" 'language {language} — '
has "F view opens the browser" "$(sed -n '/^def cmd_view/,/^def /p' "$ROOT/resources/pearde.py")" "webbrowser.open"
has "F the five bands, in the scan's words" "$(python3 "$ROOT/resources/board/plan.py" scan "$ROOT/resources/board/example/prds" 2>&1)" "gated"
lacks "F no emoji" "$(grep -vE '^\| `install --apply`' "$README")" "✓"

echo "G. the footprint beside the README"
has "G language.md has the README row" "$(cat "$ROOT/references/language.md")" "| README        | a person, first time | quickstart, then rings |"
has "G skills/pearde.md still opens with Read @README.md" "$(sed -n 6p "$ROOT/skills/pearde.md")" "Read @README.md"
has "G ...and points at the table's new place" "$(sed -n '6,8p' "$ROOT/skills/pearde.md")" "under **Three rings**"
eq  "G index.py check is silent" "$(python3 "$ROOT/resources/index.py" check 2>&1 | wc -l | tr -d ' ')" "0"
eq  "G nothing anchors into a README heading" "$(grep -rl 'README.md#' "$ROOT/references" "$ROOT/skills" "$ROOT/index.md" "$ROOT/SKILL.md" 2>/dev/null | wc -l | tr -d ' ')" "0"

if [ "${1:-}" != "--no-run" ]; then
  echo "H. the five lines, end to end"
  bash "$ROOT/prds/the-board-runs-itself/readme-in-three-rings/probe/quickstart.sh" </dev/null > "$S/qs" 2>&1; RC=$?
  eq  "H quickstart.sh exits 0" "$RC" "0"
  has "H ...and every check passed" "$(tail -1 "$S/qs")" " 0 fail"
  [ "$RC" = 0 ] || sed 's/^/  /' "$S/qs" | grep '^  FAIL'
fi

echo
echo "$((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" = 0 ]
