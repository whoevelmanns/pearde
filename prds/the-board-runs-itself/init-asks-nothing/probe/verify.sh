#!/usr/bin/env bash
# init-asks-nothing — the probe's harness.
#
# Runs `init.py` through an ISOLATED copy of resources/ on a spare port: the
# daemon keeps its registry in state/ beside serve.py, so a copy is the only
# way to exercise `ensure` without putting a temp path into the registry the
# real boards share. The probe file is copied to the path the spec moves it
# to (resources/board/init.py) so the code under test is the code that lands.
# Fixtures are made under mktemp and removed at exit. One line per assertion,
# a count at the end.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
PASS=0; FAIL=0
export GIT_AUTHOR_NAME=probe GIT_AUTHOR_EMAIL=probe@x \
       GIT_COMMITTER_NAME=probe GIT_COMMITTER_EMAIL=probe@x

ok()   { PASS=$((PASS+1)); echo "  ok   $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL $1"; [ -n "${2:-}" ] && echo "       got:  $2"; [ -n "${3:-}" ] && echo "       want: $3"; }
eq()   { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "$2" "$3"; fi; }
has()  { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1" "$2" "contains: $3"; fi; }
lacks(){ if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1" "$2" "without: $3"; else ok "$1"; fi; }

TOP="$(cd "$(mktemp -d)" && pwd -P)"   # physical: init prints the cwd resolved
trap 'rm -rf "$TOP"' EXIT

# ── the isolated skill copy ──────────────────────────────────────────────────
SRV="$TOP/srv/resources"; mkdir -p "$SRV/board"
cp "$ROOT"/resources/*.py "$ROOT"/resources/*.sh "$SRV/"
cp "$ROOT"/resources/board/*.py "$ROOT"/resources/board/*.css "$ROOT"/resources/board/*.js "$SRV/board/"
cp -R "$ROOT/resources/board/example" "$SRV/board/example"
INIT="$SRV/board/init.py"
if [ -f "$ROOT/resources/board/init.py" ]; then
  cp "$ROOT/resources/board/init.py" "$INIT"      # landed: test what landed
else
  cp "$HERE/init.py" "$INIT"                      # the probe, at its future path
fi
for f in skills references index.md README.md; do ln -s "$ROOT/$f" "$TOP/srv/$f"; done
PEARDE="$SRV/pearde.py"
REG="$ROOT/resources/board/state/serve.json"
REG_BEFORE="$( [ -f "$REG" ] && cksum < "$REG" )"
SPARE="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
export PEARDE_PORT="$SPARE"
trap 'PEARDE_PORT="$SPARE" python3 "$SRV/board/serve.py" stop >/dev/null 2>&1; rm -rf "$TOP"' EXIT

repo() { D="$TOP/$1"; mkdir -p "$D"; ( cd "$D" && git init -q -b main ); }
fm()   { grep -E "^$2:" "$D/prds/settings.md" | head -1 | sed "s/^$2:[[:space:]]*//"; }
last3(){ printf '%s\n' "$1" | tail -3; }

# ── A. a fresh git repo ──────────────────────────────────────────────────────
echo "A. pearde init in a fresh repo"
repo a
OUT="$( cd "$D" && python3 "$PEARDE" init 2>&1 )"; RC=$?
eq  "A exit 0" "$RC" "0"
eq  "A the first line says the language and the command that changes it" "$(printf '%s\n' "$OUT" | head -1)" "board a · language English — pearde settings language=<l> changes it"
eq  "A settings.md · language" "$(fm a language)" "English"
eq  "A settings.md · workers" "$(fm a workers)" "3"
eq  "A settings.md · pipeline" "$(fm a pipeline)" "3"
eq  "A settings.md · weight-default" "$(fm a weight-default)" "50"
eq  "A settings.md · gantt-day" "$(fm a gantt-day)" "8h"
eq  "A no name: — inferred" "$(fm a name)" ""
eq  "A no members: — never a master" "$(fm a members)" ""
eq  "A vision.md is the template" "$(cksum < "$D/prds/vision.md")" "$(cksum < "$ROOT/references/templates/vision.md")"
has "A vision.md keeps terminals: commented" "$(cat "$D/prds/vision.md")" "# terminals:"
for n in prds/.plan.json prds/.round.md prds/.history.jsonl prds/.view.html; do
  eq  "A .gitignore holds $n" "$(grep -cxF "$n" "$D/.gitignore")" "1"
done
eq  "A memos/ is not made" "$( [ -d "$D/prds/memos" ] && echo yes || echo no )" "no"
eq  "A workflows/ is not made" "$( [ -d "$D/prds/workflows" ] && echo yes || echo no )" "no"
has "A the daemon registered the board" "$OUT" "serve: registered a"
has "A doctor ran, every line printed — the header" "$OUT" "pearde doctor — $D"
has "A doctor: board ok" "$OUT" "board       ok      $D/prds · 0 PRDs · language English"
has "A doctor: view ok, watching" "$OUT" "view        ok      watching · http://127.0.0.1:$SPARE/board/a"
has "A the daemon's status lists the board" "$(python3 "$SRV/board/serve.py" status 2>&1)" "$D/prds"
eq  "A the last three lines: URL, add, pearde" "$(last3 "$OUT")" "http://127.0.0.1:$SPARE/board/a
pearde add \"<title>\"
pearde"
eq  "A scan reads the board" "$(python3 "$PEARDE" scan "$D/prds" 2>&1 | head -1)" "board: $D/prds · 0 PRDs"
lacks "A nothing was asked" "$OUT" "?"

# ── B. idempotent ────────────────────────────────────────────────────────────
echo "B. pearde init again"
BEFORE="$( cd "$D" && git status --porcelain )"
SUM="$(cat "$D/prds/settings.md" "$D/prds/vision.md" "$D/.gitignore" | cksum)"
OUT2="$( cd "$D" && python3 "$PEARDE" init 2>&1 )"; RC=$?
eq  "B exit 0" "$RC" "0"
eq  "B the same three lines" "$(last3 "$OUT2")" "$(last3 "$OUT")"
eq  "B git status --porcelain unchanged" "$( cd "$D" && git status --porcelain )" "$BEFORE"
eq  "B the three files are byte-identical" "$(cat "$D/prds/settings.md" "$D/prds/vision.md" "$D/.gitignore" | cksum)" "$SUM"
lacks "B nothing written — no init: line" "$OUT2" "init: wrote"
lacks "B doctor not re-run on an existing board" "$OUT2" "pearde doctor"
has "B the first line still says the language" "$OUT2" "board a · language English"

# ── C. --language, --name ────────────────────────────────────────────────────
echo "C. --language German --name kanban"
repo c
OUT="$( cd "$D" && python3 "$PEARDE" init --language German --name kanban 2>&1 )"; RC=$?
eq  "C exit 0" "$RC" "0"
eq  "C language: German" "$(fm c language)" "German"
eq  "C name: kanban" "$(fm c name)" "kanban"
eq  "C the first line names both" "$(printf '%s\n' "$OUT" | head -1)" "board kanban · language German — pearde settings language=<l> changes it"
eq  "C the URL is /board/<name>" "$(last3 "$OUT" | head -1)" "http://127.0.0.1:$SPARE/board/kanban"
eq  "C name: is the first key" "$(sed -n 2p "$D/prds/settings.md")" "name: kanban"

# ── D. settings <key>=<value> ────────────────────────────────────────────────
echo "D. pearde settings"
OUT="$( cd "$D" && python3 "$PEARDE" settings workers=5 2>&1 )"; RC=$?
eq  "D exit 0" "$RC" "0"
eq  "D workers: 5" "$(fm c workers)" "5"
eq  "D the line says what moved" "$OUT" "settings: workers 3 → 5"
eq  "D every other line byte-identical" "$(grep -v '^workers:' "$D/prds/settings.md" | cksum)" "$(printf -- '---\nname: kanban\nlanguage: German\npipeline: 3\nweight-default: 50\ngantt-day: 8h\n---\n' | cksum)"
OUT="$( cd "$D" && python3 "$PEARDE" settings language=English 2>&1 )"
eq  "D language=English replaces the key" "$(fm c language)" "English"
OUT="$( cd "$D" && python3 "$PEARDE" settings split-above=40 2>&1 )"
eq  "D a new key is appended" "$(fm c split-above)" "40"
eq  "D ...and said as new" "$OUT" "settings: split-above 40"
eq  "D --board names the board from elsewhere" "$( cd "$TOP" && python3 "$PEARDE" settings pipeline=2 --board "$D/prds" 2>&1 )" "settings: pipeline 3 → 2"
OUT="$( cd "$D" && python3 "$PEARDE" settings workers 2>&1 )"; RC=$?
eq  "D a key with no = is refused" "$RC" "1"
has "D ...naming the shape" "$OUT" "settings <key>=<value>"
OUT="$( cd "$D" && python3 "$PEARDE" settings workers= 2>&1 )"; RC=$?
eq  "D an empty value is refused" "$RC" "1"
OUT="$( cd "$D" && python3 "$PEARDE" settings 'Bad Key=1' 2>&1 )"; RC=$?
eq  "D a bad key is refused" "$RC" "1"
mkdir -p "$TOP/nosettings/prds"
OUT="$( cd "$TOP/nosettings" && python3 "$PEARDE" settings workers=1 2>&1 )"; RC=$?
eq  "D no settings.md is refused" "$RC" "1"
has "D ...and names pearde init" "$OUT" "pearde init"

# ── E. --example ─────────────────────────────────────────────────────────────
echo "E. pearde init --example"
repo e
OUT="$( cd "$D" && python3 "$PEARDE" init --example 2>&1 )"; RC=$?
eq  "E exit 0" "$RC" "0"
eq  "E the example's settings — name: example" "$(fm e name)" "example"
eq  "E the example's PRDs" "$(find "$D/prds" -name prd.md | wc -l | tr -d ' ')" "8"
SCAN="$(python3 "$PEARDE" scan "$D/prds" 2>&1)"
for s in "collect —" "waiting on you —" "in flight —" "ready —" "gated —"; do
  has "E scan prints: $s" "$SCAN" "$s"
done
has "E vision.md written beside the example" "$(ls "$D/prds")" "vision.md"
eq  "E the first line says example" "$(printf '%s\n' "$OUT" | head -1)" "board example · language English — pearde settings language=<l> changes it"
repo e2; mkdir -p "$D/prds/x"
OUT="$( cd "$D" && python3 "$PEARDE" init --example 2>&1 )"; RC=$?
eq  "E --example refuses a non-empty prds/ without settings.md" "$RC" "1"
eq  "E ...and copied nothing" "$(find "$D/prds" -name prd.md | wc -l | tr -d ' ')" "0"

# ── F. not a git repo, and a hand-made prds/ ─────────────────────────────────
echo "F. no git · hand-made board"
D="$TOP/f"; mkdir -p "$D"
OUT="$( cd "$D" && python3 "$PEARDE" init 2>&1 )"; RC=$?
eq  "F exit 0 outside git" "$RC" "0"
eq  "F no .gitignore written outside git" "$( [ -e "$D/.gitignore" ] && echo yes || echo no )" "no"
eq  "F settings.md still written" "$(fm f language)" "English"
repo g; mkdir -p "$D/prds/one"; printf -- '---\nstate: open\n---\n# one\n' > "$D/prds/one/prd.md"
OUT="$( cd "$D" && python3 "$PEARDE" init 2>&1 )"; RC=$?
eq  "F a hand-made prds/ gains settings.md" "$(fm g language)" "English"
eq  "F ...and keeps its PRD" "$( [ -f "$D/prds/one/prd.md" ] && echo yes )" "yes"
has "F doctor counts it" "$OUT" "board       ok      $D/prds · 1 PRDs · language English"
printf 'node_modules\n' > "$TOP/h.gitignore"; repo h; cp "$TOP/h.gitignore" "$D/.gitignore"
OUT="$( cd "$D" && python3 "$PEARDE" init 2>&1 )"
eq  "F an existing .gitignore keeps its lines" "$(head -1 "$D/.gitignore")" "node_modules"
eq  "F ...and gains the four" "$(grep -c '^prds/\.' "$D/.gitignore")" "4"
OUT="$( cd "$D" && python3 "$PEARDE" init --bogus 2>&1 )"; RC=$?
eq  "F an unknown flag is refused" "$RC" "2"

# ── G. the dispatcher ────────────────────────────────────────────────────────
echo "G. pearde.py discovers init and settings"
H="$(python3 "$PEARDE" help 2>&1)"
has "G help lists pearde init" "$H" "pearde init"
has "G help lists pearde settings" "$H" "pearde settings"
lacks "G no not-yet line for init-asks-nothing" "$H" "not yet — init-asks-nothing"
lacks "G no clash on stderr" "$H" "pearde: "
has "G pearde init --help" "$(python3 "$PEARDE" init --help 2>&1)" "a board that asked nothing"

# ── H. doctor: the board row ─────────────────────────────────────────────────
echo "H. doctor's board row"
mkdir -p "$TOP/empty"
DOC="$(bash "$SRV/doctor.sh" "$TOP/empty" 2>&1)"
has "H board off names pearde init" "$(printf '%s\n' "$DOC" | grep -A1 'board       off')" "pearde.py init"
mkdir -p "$TOP/nolang/prds"; printf -- '---\nworkers: 2\n---\n' > "$TOP/nolang/prds/settings.md"
DOC="$(bash "$SRV/doctor.sh" "$TOP/nolang" 2>&1)"
has "H a missing language: is board ok" "$DOC" "board       ok      $TOP/nolang/prds · 0 PRDs · language English (default)"
lacks "H ...never broken" "$DOC" "settings.md has no language"
DOC="$(bash "$SRV/doctor.sh" "$TOP/nosettings" 2>&1)"
has "H no settings.md still broken, fix is pearde init" "$(printf '%s\n' "$DOC" | grep -A1 'no settings.md')" "pearde.py init"

# ── I. the daemon cannot bind ────────────────────────────────────────────────
echo "I. the port cannot be bound"
python3 "$SRV/board/serve.py" stop >/dev/null 2>&1
repo i
OUT="$( cd "$D" && PEARDE_PORT=1 python3 "$PEARDE" init 2>&1 )"; RC=$?
eq  "I exit 0 without a daemon" "$RC" "0"
has "I says the view is not watching, and goes on" "$OUT" "view: not watching"
has "I doctor still ran" "$OUT" "pearde doctor — $D"
eq  "I the three lines still close it" "$(last3 "$OUT")" "http://127.0.0.1:1/board/i
pearde add \"<title>\"
pearde"

# ── J. the real registry ─────────────────────────────────────────────────────
echo "J. nothing touched the real daemon"
eq  "J the real registry is untouched" "$( [ -f "$REG" ] && cksum < "$REG" )" "$REG_BEFORE"
eq  "J the copy's registry never learned a fixture" "$(tr -d '[:space:]' < "$SRV/board/state/serve.json" 2>/dev/null)" "[]"
eq  "J no fixture prd.md under this probe" "$(find "$HERE" -name prd.md | wc -l | tr -d ' ')" "0"

echo
echo "$((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" = 0 ]
