#!/usr/bin/env bash
# verify.sh — the-next-line-runs: every line a command prints as "run this
# next" runs as printed, and the persona is still the line's only record.
#
# Fixtures: the example board copied to a temp dir for the transition checks;
# for the fresh-shell checks the repo is copied (tracked files, as they are in
# the working tree — never resources/board/state/), the skills dir is fresh,
# the board is a fresh git repo, and the daemon is the copy's serve.py on a
# spare port. Nothing here touches the real board or the live daemon. One
# line per assertion, one count at the end; exit 1 on any failure.
set -u
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
T="$ROOT/resources/board/transitions.py"
TOP="$(mktemp -d)"; SCR="$(mktemp -d)"
COPY="$TOP/pearde"; SKILLS="$TOP/skills"; PROJ="$TOP/proj"; HOMED="$TOP/home"
REG="$ROOT/resources/board/state/serve.json"
REG_BEFORE="$( [ -f "$REG" ] && cksum < "$REG" )"
SPARE="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
cleanup() {
  [ -f "$COPY/resources/board/serve.py" ] && PEARDE_PORT="$SPARE" python3 "$COPY/resources/board/serve.py" stop >/dev/null 2>&1
  rm -rf "$TOP" "$SCR"
}
trap cleanup EXIT
unset PEARDE_AS   # the harness decides, per check

PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); }
bad()  { FAIL=$((FAIL+1)); echo "FAIL: $1"; }
eq()   { [ "$2" = "$3" ] && ok || bad "$1 — got '$2', want '$3'"; }
has()  { printf '%s' "$2" | grep -qF -- "$3" && ok || bad "$1 — missing '$3'"; }
not()  { printf '%s' "$2" | grep -qF -- "$3" && bad "$1 — has '$3'" || ok; }
board() { local b; b="$(mktemp -d)"; cp -R "$ROOT/resources/board/example/prds" "$b/prds"; find "$b" -type f -exec touch {} +; echo "$b/prds"; }

echo "A. add with neither --as nor PEARDE_AS files the PRD, and says (default)"
B="$(board)"
OUT="$(python3 "$T" add "A first title" --board "$B" 2>&1)"; RC=$?
eq  "A add exits 0" "$RC" "0"
eq  "A prd.md exists" "$( [ -f "$B/a-first-title/prd.md" ] && echo yes )" "yes"
eq  "A state: open" "$(awk -F'[: #]+' '/^state:/{print $2; exit}' "$B/a-first-title/prd.md")" "open"
eq  "A the line ends · as engineer (default)" "$([[ "$OUT" == *" · as engineer (default)" ]]; echo $?)" "0"
eq  "A the term is last, after workers" "$(printf '%s' "$OUT" | grep -cE ' workers · as engineer \(default\)$')" "1"
eq  "A one line printed" "$(printf '%s\n' "$OUT" | wc -l | tr -d ' ')" "1"
eq  "A the transition is recorded" "$(grep -c '"prd": "a-first-title"' "$B/.transitions.jsonl")" "1"

echo "B. every other transition still refuses, naming PEARDE_AS and the install line"
for c in "claim next w" "release next open" "answer next Q1 yes" "defer next" "retry next" "unblock next" "set next analyzing" "sweep"; do
  OUT="$(python3 "$T" $c --board "$B" 2>&1)"; RC=$?
  eq  "B $c exits 1" "$RC" "1"
  has "B $c names PEARDE_AS" "$OUT" "PEARDE_AS"
  has "B $c names the install line" "$OUT" "export PEARDE_AS=engineer"
  has "B $c names install --apply" "$OUT" "install --apply"
done
eq  "B nothing moved on the board" "$(grep -c 'next' "$B/.transitions.jsonl")" "0"
eq  "B set --force refuses too" "$(python3 "$T" set next open --force --board "$B" >/dev/null 2>&1; echo $?)" "1"

echo "C. a named persona wins, and carries no (default)"
OUT="$(python3 "$T" add "Second" --as skeptic --board "$B" 2>&1)"
eq  "C --as skeptic is last" "$([[ "$OUT" == *" · as skeptic" ]]; echo $?)" "0"
not "C ...without (default)" "$OUT" "(default)"
OUT="$(PEARDE_AS=mentor python3 "$T" add "Third" --board "$B" 2>&1)"
eq  "C PEARDE_AS=mentor is last" "$([[ "$OUT" == *" · as mentor" ]]; echo $?)" "0"
not "C ...without (default)" "$OUT" "(default)"
OUT="$(PEARDE_AS=mentor python3 "$T" add "Fourth" --as designer --board "$B" 2>&1)"
eq  "C --as beats PEARDE_AS" "$([[ "$OUT" == *" · as designer" ]]; echo $?)" "0"
OUT="$(PEARDE_AS='  ' python3 "$T" add "Fifth" --board "$B" 2>&1)"
eq  "C a blank PEARDE_AS is unset" "$([[ "$OUT" == *" · as engineer (default)" ]]; echo $?)" "0"
OUT="$(PEARDE_AS=skeptic python3 "$T" set next analyzing --force --board "$B" 2>&1)"; RC=$?
eq  "C set with PEARDE_AS still runs" "$RC" "0"
eq  "C ...as skeptic" "$([[ "$OUT" == *" · as skeptic" ]]; echo $?)" "0"

echo "D. the status line reads engineer off a (default) line"
LINE="$(python3 "$T" add "Sixth" --board "$B" 2>&1)"
printf '{"type":"assistant","text":"%s"}\n' "$LINE" > "$SCR/transcript.jsonl"
OUT="$(cd "$B/.." && printf '{"transcript_path":"%s","cwd":"%s"}' "$SCR/transcript.jsonl" "$B/.." | bash "$ROOT/resources/statusline.sh" 2>/dev/null)"
has "D the segment shows engineer" "$OUT" "engineer"
not "D ...and not the marker" "$OUT" "default"
not "D ...and no parenthesis" "$OUT" "("

echo "E. install --apply prints the export beside the alias"
OUT="$(bash "$ROOT/resources/install.sh" --apply "$SKILLS" 2>&1)"; RC=$?
eq  "E install exits 0" "$RC" "0"
has "E the alias line" "$OUT" "alias pearde='python3 $ROOT/resources/pearde.py'"
has "E the export line" "$OUT" "export PEARDE_AS=engineer"
eq  "E export is the line after the alias" "$(printf '%s\n' "$OUT" | grep -A1 "^  alias pearde=" | sed -n 2p | sed 's/^ *//')" "export PEARDE_AS=engineer"
has "E the heading says who is working" "$OUT" "who is working"
eq  "E the export line is bare — pasteable" "$(printf '%s\n' "$OUT" | grep -c '^  export PEARDE_AS=engineer$')" "1"
OUT2="$(bash "$ROOT/resources/install.sh" --apply "$SKILLS" 2>&1)"
has "E already built prints them too" "$OUT2" "export PEARDE_AS=engineer"
OUT3="$(bash "$ROOT/resources/install.sh" "$SKILLS" 2>&1)"
not "E report mode does not" "$OUT3" "PEARDE_AS"
LINES="$(printf '%s\n' "$OUT" | grep -E '^  (alias pearde=|export PEARDE_AS=)' | sed 's/^  //')"
eq  "E two lines to paste" "$(printf '%s\n' "$LINES" | wc -l | tr -d ' ')" "2"

echo "F. a fresh shell with the two lines: init's three lines run as printed"
mkdir -p "$COPY" "$PROJ" "$HOMED"
( cd "$ROOT" && git ls-files -z | rsync -a0 --files-from=- "$ROOT/" "$COPY/" )
for f in resources/board/transitions.py resources/install.sh; do cp "$ROOT/$f" "$COPY/$f"; done   # the working tree, edits included
( cd "$PROJ" && git init -q . )
CLINES="$(printf '%s\n' "$LINES" | sed "s|$ROOT|$COPY|")"
cat > "$SCR/shell1.sh" <<SH
shopt -s expand_aliases
$CLINES
cd "$PROJ"
pearde init --example > "$SCR/init.out" 2>&1; echo "init rc=\$?" > "$SCR/rc"
L1="\$(tail -3 "$SCR/init.out" | sed -n 1p)"; L2="\$(tail -3 "$SCR/init.out" | sed -n 2p)"; L3="\$(tail -3 "$SCR/init.out" | sed -n 3p)"
printf '%s\n' "\$L1" "\$L2" "\$L3" > "$SCR/three"
python3 -c 'import sys,urllib.request; print(urllib.request.urlopen(sys.argv[1], timeout=5).status)' "\$L1" > "$SCR/l1.out" 2>&1; echo "l1 rc=\$?" >> "$SCR/rc"
eval "\$L2" > "$SCR/l2.out" 2>&1; echo "l2 rc=\$?" >> "$SCR/rc"
eval "\$L3" > "$SCR/l3.out" 2>&1; echo "l3 rc=\$?" >> "$SCR/rc"
pearde add "Ship the quickstart" > "$SCR/qs3.out" 2>&1; echo "qs3 rc=\$?" >> "$SCR/rc"
SH
env -i PATH="$PATH" HOME="$HOMED" PEARDE_PORT="$SPARE" bash --noprofile --norc "$SCR/shell1.sh"
has "F init exits 0" "$(cat "$SCR/rc")" "init rc=0"
has "F line 1 is the URL" "$(sed -n 1p "$SCR/three")" "http://127.0.0.1:$SPARE/board/example"
eq  "F line 2 is add, as printed" "$(sed -n 2p "$SCR/three")" 'pearde add "<title>"'
eq  "F line 3 is pearde" "$(sed -n 3p "$SCR/three")" "pearde"
eq  "F line 1 answers 200" "$(cat "$SCR/l1.out")" "200"
has "F line 2 exits 0" "$(cat "$SCR/rc")" "l2 rc=0"
has "F line 2 prints the progress line" "$(cat "$SCR/l2.out")" "▸ title: — → open"
eq  "F ...as engineer, from the export" "$([[ "$(cat "$SCR/l2.out")" == *" · as engineer" ]]; echo $?)" "0"
eq  "F ...and prds/title/prd.md exists" "$( [ -f "$PROJ/prds/title/prd.md" ] && echo yes )" "yes"
has "F line 3 exits 0" "$(cat "$SCR/rc")" "l3 rc=0"
has "F line 3 lists the PRD" "$(cat "$SCR/l3.out")" "title"
has "F the quickstart's third line runs without --as" "$(cat "$SCR/rc")" "qs3 rc=0"
has "F ...and files it" "$(cat "$SCR/qs3.out")" "ship-the-quickstart"

echo "G. a fresh shell with the alias only — the export skipped — still adds"
cat > "$SCR/shell2.sh" <<SH
shopt -s expand_aliases
$(printf '%s\n' "$CLINES" | sed -n 1p)
cd "$PROJ"
pearde add "Without the export" > "$SCR/g-add.out" 2>&1; echo "g-add rc=\$?" > "$SCR/g-rc"
pearde set without-the-export analyzing > "$SCR/g-set.out" 2>&1; echo "g-set rc=\$?" >> "$SCR/g-rc"
SH
env -i PATH="$PATH" HOME="$HOMED" PEARDE_PORT="$SPARE" bash --noprofile --norc "$SCR/shell2.sh"
has "G add exits 0" "$(cat "$SCR/g-rc")" "g-add rc=0"
eq  "G ...as engineer (default)" "$([[ "$(cat "$SCR/g-add.out")" == *" · as engineer (default)" ]]; echo $?)" "0"
has "G set exits 1" "$(cat "$SCR/g-rc")" "g-set rc=1"
has "G ...naming PEARDE_AS" "$(cat "$SCR/g-set.out")" "PEARDE_AS"
has "G ...and the install line" "$(cat "$SCR/g-set.out")" "export PEARDE_AS=engineer"
eq  "G state: open still" "$(awk -F'[: #]+' '/^state:/{print $2; exit}' "$PROJ/prds/without-the-export/prd.md")" "open"

echo "H. the prose says where the persona lives"
has "H handles: the add row says (default)" "$(grep '^| new PRD' "$ROOT/references/parts/handles.md")" '`· as engineer (default)`'
has "H handles: the add row says runs as printed" "$(grep '^| new PRD' "$ROOT/references/parts/handles.md")" "Runs as printed"
has "H handles: persona <id> is the export" "$(grep '^| who is working' "$ROOT/references/parts/handles.md")" 'export PEARDE_AS=<id>'
has "H personas: the variable is named" "$(cat "$ROOT/references/parts/personas.md")" "PEARDE_AS"
has "H personas: stored on no board file" "$(cat "$ROOT/references/parts/personas.md")" "stored on no board file"
has "H personas: the add exception" "$(cat "$ROOT/references/parts/personas.md")" '`· as engineer (default)`'
has "H personas: the way back is the export" "$(cat "$ROOT/references/parts/personas.md")" 'export PEARDE_AS=engineer'
has "H personas: a fresh shell is --as" "$(cat "$ROOT/references/parts/personas.md")" '`--as <id>` on the line'
has "H install.md: the export line" "$(cat "$ROOT/references/install.md")" 'export PEARDE_AS=engineer'
has "H install.md: two lines" "$(cat "$ROOT/references/install.md")" "**Two lines.**"
has "H install.md: the first run's lines run as printed" "$(cat "$ROOT/references/install.md")" "each runs as printed"
has "H transitions.py: the docstring names the exception" "$(sed -n '1,45p' "$T")" "(default)"
has "H transitions.py: the refusal names the install line" "$(sed -n '/^def persona_default/,/^def run/p' "$T")" "INSTALL_LINE"
eq  "H init.py is unchanged — measured, not restated" "$(cd "$ROOT" && git diff --stat -- resources/board/init.py | wc -l | tr -d ' ')" "0"

echo "I. the live daemon and the real board were never touched"
eq  "I the real registry is untouched" "$( [ -f "$REG" ] && cksum < "$REG" )" "$REG_BEFORE"
eq  "I no PRD filed on the real board" "$( [ -d "$ROOT/prds/a-first-title" ] || [ -d "$ROOT/prds/title" ] && echo yes || echo no )" "no"

echo
echo "$((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" = 0 ]
