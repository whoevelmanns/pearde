#!/usr/bin/env bash
# the-gate-runs-the-harnesses — the probe's harness.
#
# Run from anywhere:  bash prds/the-gate-runs-the-harnesses/probe/verify.sh
#
# Every fixture is built in a directory made at run time and removed on exit.
# Nothing it writes lands under prds/ — a fixture prd.md there would become a
# real PRD and move the board's counts.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DOC="$ROOT/resources/doctor.sh"
DOCMD="$ROOT/references/parts/doctor.md"

PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); printf '  ok   %s\n' "$1"; }
bad() { FAIL=$((FAIL+1)); printf '  FAIL %s\n' "$1"; }
eq()  { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 — got: $2 · want: $3"; fi; }
has() { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1 — missing: $3"; fi; }
not() { if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1 — present: $3"; else ok "$1"; fi; }
hase() { if printf '%s' "$2" | grep -qE -- "$3"; then ok "$1"; else bad "$1 — no match: $3"; fi; }

D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
now() { python3 -c 'import time;print(time.time())'; }
took() { python3 -c "print(f'{$2-$1:.2f}')"; }

# ── a fixture board, and harnesses to hang off it ────────────────────────────
python3 "$ROOT/resources/board/plan.py" example "$D/ex" >/dev/null 2>&1 \
  || { echo "no example board"; exit 2; }
B="$D/ex/prds"
MARK="$D/ran"

# green() <name> <pinned 0|1> — a harness that passes, with or without the pin
green() {
  mkdir -p "$B/$1/probe"
  {
    echo '#!/usr/bin/env bash'
    echo "echo '  ok   a check that passed'"
    echo "echo '  ok   a check named with a bad word in it'"
    echo "echo '$1' >> \"$MARK\""
    [ "$2" = 1 ] && echo 'PASS=2; FAIL=0; [ "$((PASS+FAIL))" = 2 ] || exit 1'
    echo 'exit 0'
  } > "$B/$1/probe/verify.sh"
}
# red() <name> — a harness that prints a FAIL line and exits non-zero
red() {
  mkdir -p "$B/$1/probe"
  {
    echo '#!/usr/bin/env bash'
    echo "echo '  ok   a check named with a bad word in it'"
    echo "echo '  FAIL the assertion this harness exists for'"
    echo "echo '$1' >> \"$MARK\""
    echo 'PASS=1; FAIL=1; [ "$((PASS+FAIL))" = 2 ] || exit 1'
    echo 'exit 1'
  } > "$B/$1/probe/verify.sh"
}
setkey() { # setkey <value|->  — write or drop `harnesses:` in the fixture settings
  grep -v '^harnesses:' "$B/settings.md" > "$D/s"; mv "$D/s" "$B/settings.md"
  [ "$1" = "-" ] || printf 'harnesses: %s\n' "$1" >> "$B/settings.md"
}
# doctor sets PEARDE_HARNESSES=1 for every harness it runs, this file among
# them, and it is inherited. A probe of the row must clear it or every fixture
# run below reads the guard instead of the behaviour under test. PEARDE_PORT
# points the view row at a dead port: --fix must never reach the live daemon.
FRESH="env -u PEARDE_HARNESSES PEARDE_PORT=1"
doc() { : > "$MARK"; OUT=$($FRESH bash "$DOC" "$@" 2>&1); RC=$?; }
hrow() { printf '%s\n' "$OUT" | grep -A9 '^  harnesses '; }

echo
echo "── A. off by default, and nothing runs ──────────────────────────────────"

green pinned-one 1
green pinned-two 1
setkey -
doc "$D/ex"
RC_BASE=$RC
eq  "A the fixture board is otherwise green — so exit 1 later means this row" "$RC_BASE" "0"
has "A the row is off with no harnesses: key" "$(hrow)" "harnesses   off"
has "A ...and says how many it did not run"   "$(hrow)" "2 harnesses · not run"
has "A ...and the fix names the key and the flag" "$(hrow)" "harnesses: on in $B/settings.md"
eq  "A no harness ran"                        "$(cat "$MARK" | wc -l | tr -d ' ')" "0"
has "A the fix names one run without the key" "$(hrow)" "--harnesses"

setkey off
doc "$D/ex"
has "A harnesses: off is off"                 "$(hrow)" "harnesses   off"
eq  "A ...and still nothing ran"              "$(cat "$MARK" | wc -l | tr -d ' ')" "0"

echo
echo "── B. the flag runs them regardless of the key ──────────────────────────"

doc --harnesses "$D/ex"
has "B --harnesses with harnesses: off runs them" "$(hrow)" "harnesses   ok"
eq  "B ...both harnesses ran"                     "$(cat "$MARK" | wc -l | tr -d ' ')" "2"
has "B ...and the row is green on its own count"  "$(hrow)" "2 of 2 green"
eq  "B ...and doctor's exit code is the off-run's" "$RC" "$RC_BASE"

# --fix is never run against a fixture board: its one repair registers the
# board it is handed with the live view daemon, and a temp path would outlive
# the run in the real registry. What is checked here is that both flags are
# consumed in either order rather than read as the board path.
H1=$($FRESH bash "$DOC" --fix --harnesses "$D/nowhere" 2>&1 | head -1)
H2=$($FRESH bash "$DOC" --harnesses --fix "$D/nowhere" 2>&1 | head -1)
eq  "B --fix --harnesses <board>: the board is still the board" "$H1" "pearde doctor — $D/nowhere"
eq  "B --harnesses --fix <board>: order does not matter"        "$H2" "pearde doctor — $D/nowhere"

echo
echo "── C. the key runs them with no flag ────────────────────────────────────"

setkey on
doc "$D/ex"
has "C harnesses: on runs them"           "$(hrow)" "harnesses   ok"
eq  "C ...both ran"                       "$(cat "$MARK" | wc -l | tr -d ' ')" "2"
hase "C ...the wall-clock is on the row"  "$(hrow)" '· [0-9]+s' 

echo
echo "── D. a harness that does not pin its denominator ───────────────────────"

green unpinned 0
doc "$D/ex"
has "D three ran, two are green"          "$(hrow)" "2 of 3 green"
has "D ...the third is counted unpinned"  "$(hrow)" "1 unpinned"
has "D ...and named"                      "$(hrow)" "unpinned · prds/unpinned/probe/verify.sh"
has "D ...with what an unpinned total hides" "$(hrow)" "a dropped check reads as success"
has "D ...and the idiom that pins it"     "$(hrow)" 'PASS+FAIL'
eq  "D ...it still ran"                   "$(grep -c unpinned "$MARK" | tr -d ' ')" "1"
has "D an unpinned pass does not make the row green on its own" "$(hrow)" "2 of 3 green · 1 unpinned"

echo
echo "── E. a harness that fails ──────────────────────────────────────────────"

red broken-one
doc "$D/ex"
has "E the row is broken"                 "$(hrow)" "harnesses   broken"
has "E ...it names the harness"           "$(hrow)" "prds/broken-one/probe/verify.sh — exit 1"
has "E ...and its first FAIL line"        "$(hrow)" "FAIL the assertion this harness exists for"
not "E ...not a passing check whose name holds a bad word" "$(hrow)" "a check named with a bad word"
has "E ...and the count of failures"      "$(hrow)" "1 failed"
eq  "E doctor exits 1"                    "$RC" "1"
has "E ...and says so on the last line"   "$OUT" "something is installed and not working"
eq  "E every harness still ran"           "$(cat "$MARK" | wc -l | tr -d ' ')" "4"

rm -rf "$B/broken-one"
doc "$D/ex"
has "E restored: the row is ok again"     "$(hrow)" "harnesses   ok"
eq  "E ...and the exit code is back"      "$RC" "$RC_BASE"

echo
echo "── F. a board with no harness ───────────────────────────────────────────"

python3 "$ROOT/resources/board/plan.py" example "$D/bare" >/dev/null 2>&1
printf 'harnesses: on\n' >> "$D/bare/prds/settings.md"
doc --harnesses "$D/bare"
has "F off, with no verify.sh under the board" "$(hrow)" "harnesses   off"
has "F ...and says the board has none"         "$(hrow)" "no verify.sh under $D/bare/prds"

echo
echo "── G. a harness that runs doctor does not run doctor forever ────────────"

mkdir -p "$B/calls-doctor/probe"
cat > "$B/calls-doctor/probe/verify.sh" <<INNER
#!/usr/bin/env bash
bash "$DOC" "$D/ex" 2>&1 | grep '^  harnesses ' > "$D/inner"
echo 'calls-doctor' >> "$MARK"
PASS=1; FAIL=0; [ "\$((PASS+FAIL))" = 1 ] || exit 1
exit 0
INNER
setkey on
doc "$D/ex"
eq  "G the outer run terminates"                "$RC" "$RC_BASE"
has "G the inner doctor did not run harnesses"  "$(cat "$D/inner" 2>/dev/null)" "not run inside a harness"
has "G ...and the row is off, not broken"       "$(cat "$D/inner" 2>/dev/null)" "harnesses   off"
E=$(PEARDE_HARNESSES=1 bash "$DOC" --harnesses "$D/ex" 2>&1 | grep '^  harnesses ')
has "G the flag does not override the guard"    "$E" "not run inside a harness"
rm -rf "$B/calls-doctor"

echo
echo "── H. no ledger: the expected count is nowhere but the harness ──────────"

not "H doctor.sh records no expected total for any harness" \
    "$(grep -vE '^\s*#' "$DOC" | grep -i harness)" "expected"
eq  "H no per-harness count file is written anywhere on the board" \
    "$(find "$B" -name '*.count' -o -name '.harnesses*' | wc -l | tr -d ' ')" "0"

echo
echo "── I. the wall-clock this row costs ─────────────────────────────────────"

# The `before` is HEAD's doctor.sh run against the same tree: every other file
# it reads is symlinked, so the only difference is this row.
mkdir -p "$D/base/resources"
for f in "$ROOT"/resources/*; do
  bn=$(basename "$f"); [ "$bn" = doctor.sh ] && continue
  ln -s "$f" "$D/base/resources/$bn"
done
for f in "$ROOT"/*; do
  bn=$(basename "$f"); [ "$bn" = resources ] && continue
  ln -s "$f" "$D/base/$bn"
done
git -C "$ROOT" show HEAD:resources/doctor.sh > "$D/base/resources/doctor.sh" 2>/dev/null

# the target is this board — 21 harnesses the opt-out path must not run. If
# the key is on here, the comparison would time a full sweep against a doctor
# that has no such row, so it falls back to the fixture.
T="$ROOT"
grep -qE '^[[:space:]]*harnesses:[[:space:]]*(on|yes|true)' "$ROOT/prds/settings.md" \
  && { setkey -; T="$D/ex"; }
if [ -s "$D/base/resources/doctor.sh" ]; then
  t0=$(now); $FRESH bash "$D/base/resources/doctor.sh" "$T" >/dev/null 2>&1; t1=$(now)
  BEFORE=$(took "$t0" "$t1")
  t0=$(now); $FRESH bash "$DOC" "$T" >/dev/null 2>&1; t1=$(now)
  AFTER=$(took "$t0" "$t1")
  DELTA=$(python3 -c "print(f'{$AFTER-$BEFORE:.2f}')")
  printf '  note doctor on %s, harnesses absent: before %ss · after %ss · delta %ss\n' \
         "$T" "$BEFORE" "$AFTER" "$DELTA"
  eq "I the opt-out path costs under a second more than HEAD's doctor" \
     "$(python3 -c "print('yes' if $AFTER-$BEFORE < 1.0 else 'no')")" "yes"
else
  bad "I HEAD:resources/doctor.sh could not be read"
fi

# The opt-in path is timed on the fixture, never on this board: doctor runs
# every verify.sh it finds, this file among them, so a run against $ROOT from
# inside it would fork a full board sweep per harness. The real board's two
# numbers are measured directly and quoted in the spec.
setkey -
t0=$(now); doc "$D/ex" >/dev/null 2>&1; t1=$(now); OFFT=$(took "$t0" "$t1")
setkey on
t0=$(now); doc "$D/ex" >/dev/null 2>&1; t1=$(now); ONT=$(took "$t0" "$t1")
printf '  note the fixture board, %s harnesses: opt-out %ss · opt-in %ss\n' \
       "$(find "$B" -name verify.sh | grep -c .)" "$OFFT" "$ONT"
eq "I the opt-in run executed every harness the board has" \
   "$(cat "$MARK" | wc -l | tr -d ' ')" "$(find "$B" -name verify.sh | grep -c .)"
hase "I ...and the row carries its own wall-clock" "$(hrow)" '· [0-9]+s' 

echo
echo "── J. the census this board's harnesses give ────────────────────────────"

HL=$(find "$ROOT/prds" -name verify.sh | sort)
HN=$(printf '%s\n' "$HL" | grep -c .)
PIN=0; NOPIN=0; NONZERO=0
for h in $HL; do
  if grep -qE '\$\(\([[:space:]]*[Pp][Aa][Ss][Ss][[:space:]]*\+[[:space:]]*[Ff][Aa][Ii][Ll][[:space:]]*\)\)[^=]*(=|-eq)[[:space:]]*"?[0-9]+' "$h"
  then PIN=$((PIN+1)); else NOPIN=$((NOPIN+1)); fi
  tail -3 "$h" | grep -qE '^\[ .*(FAIL|fail).* \]|exit 1' && NONZERO=$((NONZERO+1))
done
printf '  note census — %s harnesses · %s pin a denominator · %s do not · %s end on a check that sets the exit code\n' \
       "$HN" "$PIN" "$NOPIN" "$NONZERO"
eq "J every harness on this board ends on a test that carries its exit code" "$NONZERO" "$HN"
eq "J the census enumerates the tree, not a list this harness holds" \
   "$(printf '%s\n' "$HL" | grep -c "^$ROOT/prds/")" "$HN"

echo
echo "── K. the page says what the row means ──────────────────────────────────"

has "K doctor.md carries the harnesses row"  "$(cat "$DOCMD")" '| `harnesses`'
has "K ...its off column"                    "$(cat "$DOCMD")" 'harnesses: on'
has "K ...its broken column"                 "$(cat "$DOCMD")" 'exits non-zero'
has "K ...and a bullet saying why it is opt-in" "$(cat "$DOCMD")" 'a gate nobody can afford to run'
has "K ...and that the count is the harness's own" "$(cat "$DOCMD")" 'no ledger'
has "K ...and what unpinned means"           "$(cat "$DOCMD")" 'unpinned'
has "K the usage block names the flag"       "$(cat "$DOCMD")" '--harnesses'

echo
echo "── L. nothing of this probe reached the real board ──────────────────────"

eq "L no fixture prd.md under the real prds/" \
   "$(find "$ROOT/prds" -path '*/the-gate-runs-the-harnesses/probe/*' -name prd.md | wc -l | tr -d ' ')" "0"
eq "L the real board's transitions log is untouched by this run" \
   "$(find "$ROOT/prds" -newer "$MARK" -name '.transitions.jsonl' | wc -l | tr -d ' ')" "0"
eq "L index.py check is silent" \
   "$(python3 "$ROOT/resources/index.py" check 2>&1 | wc -l | tr -d ' ')" "0"

# The line below reports checks executed, not checks expected: drop one to a
# stray `continue` or a quoting slip and it prints a smaller total and exits 0,
# which is indistinguishable from success. Pin the denominator.
[ "$((PASS+FAIL))" = 57 ] || { FAIL=$((FAIL+1)); printf '  FAIL expected 57 checks, ran %s\n' "$((PASS+FAIL))"; }
echo
echo "$((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" = 0 ]
