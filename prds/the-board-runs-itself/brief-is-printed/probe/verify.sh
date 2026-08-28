#!/bin/bash
# brief-is-printed — the probe's harness. One line per assertion, a count at
# the end. Fixtures are built in a temp dir at run time and removed at exit;
# nothing under prds/ is written.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PROBE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# the module under test: resources/board/brief.py, where spec01 moved it;
# BRIEF_PY names another copy
BRIEF="${BRIEF_PY:-$ROOT/resources/board/brief.py}"
WRK="$ROOT/references/parts/workers.md"
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "  ok   $1"; }
bad() { FAIL=$((FAIL+1)); echo "  FAIL $1"; }
has() { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1 — missing: $3"; fi; }
not() { if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1 — present: $3"; else ok "$1"; fi; }
eq()  { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 — got: $2 · want: $3"; fi; }

python3 "$ROOT/resources/board/plan.py" example "$D/ex" >/dev/null || { echo "no example board"; exit 1; }
B="$D/ex/prds"
run() { python3 "$BRIEF" "$@" --board "$B" 2>"$D/err"; RC=$?; ERR=$(cat "$D/err"); }

echo "── the source: workers.md"
for b in workflow every analyst implementer consultant; do
  eq "marker pair brief:$b opens once" "$(grep -c "^<!-- brief:$b -->$" "$WRK")" 1
done
eq "five closers" "$(grep -c '^<!-- /brief -->$' "$WRK")" 5
CHK=$(python3 "$BRIEF" --check 2>&1); eq "--check is silent on the real file" "$CHK" ""

echo "── the analyst brief on the ready PRD"
run big/second >"$D/out"; OUT=$(cat "$D/out")
eq "big/second exits 0" "$RC" 0
eq "header line" "$(sed -n 1p "$D/out")" "# brief big/second · analyst · as engineer · wf none · repo $D/ex"
eq "persona line third" "$(sed -n 3p "$D/out")" "Work as @references/personas/engineer.md."
# the role section equals the analyst block of workers.md, unquoted, six placeholders filled
awk '/^<!-- brief:analyst -->$/{on=1;next} /^<!-- \/brief -->$/{if(on)exit} on' "$WRK" \
  | sed -e 's/^> \{0,1\}//' \
        -e 's#<prd>#big/second#g' -e "s#<repo>#$D/ex#g" -e 's#<language>#English#g' -e 's#<probe>#prds/big/second/probe/#g' -e 's#<split_above>#40#g' -e 's#<specs_above>#6#g' \
  > "$D/want"
N=$(wc -l < "$D/want" | tr -d ' ')
sed -n "5,$((4+N))p" "$D/out" > "$D/got"
if diff -q "$D/want" "$D/got" >/dev/null; then ok "the role section is the analyst block with the placeholders filled"; else bad "the role section drifted from workers.md:"; diff "$D/want" "$D/got" | sed 's/^/       /'; fi
for t in '<prd>' '<repo>' '<language>' '<probe>' '<board>' '<id>'; do not "no unfilled $t" "$OUT" "$t"; done
has "probe path is in the brief" "$OUT" 'Probe code lives at `prds/big/second/probe/`'
has "the fixture clause" "$OUT" 'never under `prds/`'
has "the box clause" "$OUT" 'backtick-quoted'
has "the language is named" "$OUT" 'Write in `English`'
has "the every-worker block is last" "$(tail -3 "$D/out")" 'never write outside `prds/big/second/`'

echo "── the skips"
run building; eq "building exits 1" "$RC" 1; has "building is held" "$ERR" "held"; has "the claim is quoted" "$ERR" 'claim: worker-building'
run next; eq "next exits 1" "$RC" 1; has "next names building" "$ERR" "building"; has "next is gated" "$ERR" "gated"
run finished; eq "finished (claimed, all boxes) exits 1" "$RC" 1; has "finished is held" "$ERR" "held"
run landed; eq "landed (done) exits 1" "$RC" 1; has "done is a state skip" "$ERR" 'state'
run asking; eq "asking (question) exits 1" "$RC" 1
run nothing-here; eq "unknown PRD exits 1" "$RC" 1; has "unknown PRD is named" "$ERR" 'no PRD named `nothing-here`'
run next --force >"$D/out"; eq "next --force exits 0" "$RC" 0
has "next --force says forced on the header" "$(sed -n 1p "$D/out")" " · forced"
has "next --force says why on stderr" "$ERR" "forced past gated"
has "next --force still an analyst" "$(sed -n 1p "$D/out")" "· analyst ·"

echo "── the workflow block, route inlined"
run building --force --as skeptic >"$D/out"; OUT=$(cat "$D/out")
eq "building --force exits 0" "$RC" 0
has "header says implementer" "$(sed -n 1p "$D/out")" "· implementer ·"
has "header says wf fix-a-line" "$(sed -n 1p "$D/out")" "· wf fix-a-line ·"
has "header says as skeptic" "$(sed -n 1p "$D/out")" "· as skeptic ·"
eq "persona line is the skeptic" "$(sed -n 3p "$D/out")" "Work as @references/personas/skeptic.md."
has "the workflow block, slug filled" "$OUT" 'Follow the workflow `fix-a-line`'
has "the workflow block, board filled" "$OUT" "brief fix-a-line
$B\` prints it"
has "first atomic inlined" "$OUT" "### 1 — find-the-line"
has "second atomic inlined" "$OUT" "### 2 — change-the-line"
eq "one block per distinct slug" "$(grep -c '^Follow the workflow' "$D/out")" 1
has "the implementer brief follows" "$OUT" 'Read `prds/building/prd.md` and every file in `specs/`'
# a spec naming the same slug adds no second block; a PRD with none and a spec with one gets one
sed -i.bak '1a\
workflow: fix-a-line' "$B/building/specs/spec01.md"
run building --force >"$D/out"; eq "PRD and spec same slug — still one block" "$(grep -c '^Follow the workflow' "$D/out")" 1
sed -i.bak '/^workflow:/d' "$B/building/prd.md"
run building --force >"$D/out"; eq "slug on the spec only — one block" "$(grep -c '^Follow the workflow' "$D/out")" 1
has "header shows the spec's slug" "$(sed -n 1p "$D/out")" "· wf fix-a-line ·"
run building --force --role analyst >"$D/out"; eq "an analyst reads no spec slug" "$(grep -c '^Follow the workflow' "$D/out")" 0
has "analyst header says wf none" "$(sed -n 1p "$D/out")" "· wf none ·"
# a slug that names nothing is a skip; forced, the header marks it
sed -i.bak '1a\
workflow: nope' "$B/big/second/prd.md"
run big/second; eq "dangling slug exits 1" "$RC" 1; has "dangling slug is the workflow skip" "$ERR" "workflow"
run big/second --force >"$D/out"; eq "dangling slug forced exits 0" "$RC" 0
has "dangling slug marked on the header" "$(sed -n 1p "$D/out")" "· wf nope? ·"
eq "dangling slug prints no block" "$(grep -c '^Follow the workflow' "$D/out")" 0
sed -i.bak '/^workflow: nope/d' "$B/big/second/prd.md"

echo "── the placeholders' sources"
sed -i.bak 's/^language: English/language: Deutsch/' "$B/settings.md"
run big/second >"$D/out"; has "language from settings.md" "$(cat "$D/out")" 'Write in `Deutsch`'
sed -i.bak 's/^language: Deutsch/language: English/' "$B/settings.md"
mkdir -p "$D/ex/sub/.git"; sed -i.bak '1a\
repo: sub' "$B/big/second/prd.md"
run big/second >"$D/out"; has "repo: that is a directory is the repo" "$(sed -n 1p "$D/out")" "· repo $D/ex/sub"
has "the repo is in the brief" "$(cat "$D/out")" "Attempt the implementation in \`$D/ex/sub\`"
sed -i.bak '/^repo: sub/d' "$B/big/second/prd.md"
run big/second >"$D/out"; has "repo: pearde (a name) falls back to the board's" "$(sed -n 1p "$D/out")" "· repo $D/ex"
run big/second --role implementer >"$D/out"; has "--role overrides the state" "$(sed -n 1p "$D/out")" "· implementer ·"
run big/second --role foo; eq "--role foo exits 1" "$RC" 1
run big/second --as nobody; eq "--as nobody exits 1" "$RC" 1; has "the roster is named" "$ERR" "personas/INDEX.md"

echo "── the consultant"
python3 "$BRIEF" --consult skeptic --question "is the gate right?" --transcript /x/t.jsonl --board "$B" >"$D/out" 2>"$D/err"; RC=$?
eq "consult exits 0" "$RC" 0
eq "consult header" "$(sed -n 1p "$D/out")" "# brief consult · as skeptic · repo $D/ex"
has "consult persona line" "$(cat "$D/out")" 'Work as `@references/personas/skeptic.md`.'
has "transcript filled" "$(cat "$D/out")" 'The session asking you is `/x/t.jsonl`'
has "board filled" "$(cat "$D/out")" "The board is \`$B\`"
has "question filled" "$(cat "$D/out")" 'Question: `is the gate right?`'
has "the id fills the last line too" "$(cat "$D/out")" '`▸ … · as skeptic` line'
for t in '<id>' '<transcript_path>' '<prds/>' '<repo>' '<the question'; do not "consult: no unfilled $t" "$(cat "$D/out")" "$t"; done
python3 "$BRIEF" --consult skeptic --board "$B" >/dev/null 2>&1; eq "consult without a question exits 1" "$?" 1
python3 "$BRIEF" --consult skeptic --question "q" --board "$B" >"$D/out" 2>&1
has "no transcript says so" "$(cat "$D/out")" 'no transcript was handed over'

echo "── --check reads the shape"
S="$D/skill"; mkdir -p "$S/resources/board" "$S/references/parts" "$S/references/personas" "$S/skills"
cp "$ROOT"/resources/*.py "$ROOT"/resources/*.sh "$S/resources/"
cp "$ROOT"/resources/board/*.py "$S/resources/board/"
cp -R "$ROOT/resources/board/example" "$S/resources/board/example"
cp -R "$ROOT/references/." "$S/references/"; cp -R "$ROOT/skills/." "$S/skills/"
cp "$BRIEF" "$S/resources/board/brief.py"
W="$S/references/parts/workers.md"
CHK=$(python3 "$S/resources/board/brief.py" --check 2>&1); eq "copy: --check silent" "$CHK" ""
cp "$W" "$W.orig"
awk 'BEGIN{n=0} /^<!-- \/brief -->$/{n++; if(n==3) next} {print}' "$W.orig" > "$W"
CHK=$(python3 "$S/resources/board/brief.py" --check 2>&1)
has "a removed closer: the unterminated block is named" "$CHK" "\`brief:analyst\` is not terminated before \`brief:implementer\` opens"
has "and the swallowed text's \`<x>\` is an unnamed placeholder" "$CHK" "\`<x>\` in brief:analyst is not in the placeholder table"
eq "two problems, no third" "$(printf '%s\n' "$CHK" | grep -c .)" 2
sed 's/^<!-- brief:consultant -->$//' "$W.orig" > "$W"
CHK=$(python3 "$S/resources/board/brief.py" --check 2>&1); has "a missing opener is reported" "$CHK" "no \`<!-- brief:consultant -->\`"
has "and its stray closer" "$CHK" "with no block open"
sed 's/^> Question: `<the question, as the user put it>`$/> Question: `<the question, as the user put it>` from <whom>/' "$W.orig" > "$W"
CHK=$(python3 "$S/resources/board/brief.py" --check 2>&1); has "a placeholder the table does not name" "$CHK" "\`<whom>\` in brief:consultant is not in the placeholder table"
sed 's/^| `<transcript_path>` | `--transcript` |$/| `<transcript_path>` | `--transcript` |\
| `<unused>` | nothing |/' "$W.orig" > "$W"
CHK=$(python3 "$S/resources/board/brief.py" --check 2>&1); has "a table row no block uses" "$CHK" "the table names \`<unused>\` and no brief block uses it"
grep -v '^| `<' "$W.orig" > "$W"
CHK=$(python3 "$S/resources/board/brief.py" --check 2>&1); has "no table at all" "$CHK" "no placeholder table"
cp "$W.orig" "$W"
# a fence hides the report shapes: `<N>` and `<dir-name>` are the worker's, and not flagged
not "fenced tokens are not placeholders" "$(python3 "$S/resources/board/brief.py" --check 2>&1)" "<N>"

echo "── the dispatcher and the doctor row"
H=$(python3 "$S/resources/pearde.py" help 2>&1); RC=$?
eq "pearde help exits 0 with brief.py in resources/board/" "$RC" 0
has "help lists brief from the docstring" "$H" "pearde brief                 the worker's brief for one PRD"
not "brief is no longer reserved" "$H" "not yet — brief-is-printed"
python3 "$S/resources/pearde.py" brief big/second --board "$B" >"$D/out" 2>&1; eq "pearde brief routes" "$?" 0
eq "routed header" "$(sed -n 1p "$D/out")" "# brief big/second · analyst · as engineer · wf none · repo $D/ex"
python3 "$S/resources/pearde.py" brief --help >"$D/out" 2>&1; has "pearde brief --help" "$(cat "$D/out")" "pearde brief"
DOC=$(bash "$S/resources/doctor.sh" "$D/ex" 2>&1)
has "doctor: briefs ok" "$DOC" "briefs      ok      5 blocks in references/parts/workers.md · every placeholder named"
awk 'BEGIN{n=0} /^<!-- \/brief -->$/{n++; if(n==3) next} {print}' "$W.orig" > "$W"
DOC=$(bash "$S/resources/doctor.sh" "$D/ex" 2>&1)
has "doctor: briefs broken when a closer is removed" "$DOC" "briefs      broken  5 blocks · 2 problems"
has "doctor: the problem lines follow" "$DOC" "\`brief:analyst\` is not terminated"
has "doctor: the fix line" "$DOC" "fix: close every <!-- brief:<name> --> with <!-- /brief -->"
cp "$W.orig" "$W"
rm "$S/resources/board/brief.py"
DOC=$(bash "$S/resources/doctor.sh" "$D/ex" 2>&1)
has "doctor: briefs off with no module" "$DOC" "briefs      off     no resources/board/brief.py"
RDOC=$(bash "$ROOT/resources/doctor.sh" "$ROOT" 2>&1)
has "the real doctor carries the briefs row" "$RDOC" "  briefs      "

echo
echo "verify: $PASS/$((PASS+FAIL)) checks pass"
[ "$FAIL" = 0 ]
