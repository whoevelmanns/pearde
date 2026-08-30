#!/usr/bin/env bash
# a-quoted-walk-is-data — the Bash hook refuses the walk the shell would run,
# not a walk carried as data. Runs against the repo's guard.py with the
# guard's state in a scratch dir; writes nothing under resources/board/state/.
set -u
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
GUARD="$ROOT/resources/guard.py"
D="$(mktemp -d)"; export PEARDE_GUARD_STATE="$D/state"
pass=0; fail=0
ok()  { if [ "$2" -eq 0 ]; then pass=$((pass+1)); echo "  ok   $1"; else fail=$((fail+1)); echo "  FAIL $1${3:+ — $3}"; fi; }
has() { case "$2" in *"$3"*) ok "$1" 0 ;; *) ok "$1" 1 "missing: $3" ;; esac; }
lacks() { case "$2" in *"$3"*) ok "$1" 1 "found: $3" ;; *) ok "$1" 0 ;; esac; }

# a project with a board, so the walk rule is in scope
mkdir -p "$D/proj/prds/one"; printf -- '---\nstate: open\n---\n# one\n' > "$D/proj/prds/one/prd.md"
# the command goes in as JSON via python, so quotes and newlines survive
bash_hook() { # command → guard's stdout
  python3 - "$D/proj" "$1" <<'PY' | python3 "$GUARD" pre 2>&1
import json, sys
print(json.dumps({"tool_name": "Bash", "session_id": "walk-probe", "cwd": sys.argv[1],
                  "tool_input": {"command": sys.argv[2]}}))
PY
}
W='find prds -name prd.md'

echo "— the walk the shell runs is still refused"
out=$(bash_hook "$W");                                   has "R1 a bare walk is refused" "$out" '"deny"'
out=$(bash_hook "grep -rn 'state:' prds");               has "R2 grep -r with its quoted pattern is refused — the walker runs its string" "$out" '"deny"'
out=$(bash_hook "ls prds/*/prd.md");                     has "R3 the ls glob is refused" "$out" '"deny"'
out=$(bash_hook "sh -c '$W'");                           has "R4 sh -c runs its string — refused" "$out" '"deny"'
out=$(bash_hook "bash -lc \"$W\"");                      has "R5 bash -lc runs its string — refused" "$out" '"deny"'
out=$(bash_hook "env X=1 grep -rn 'state:' prds");       has "R6 an env prefix does not hide the walker" "$out" '"deny"'
out=$(bash_hook "python3 -c 'x=1'; $W");                 has "R7 a walk after a quoted command and a ; is refused" "$out" '"deny"'
out=$(bash_hook "$(printf "cat <<EOF\nx\nEOF\n%s" "$W")"); has "R8 a walk after a heredoc is refused" "$out" '"deny"'
out=$(bash_hook "$W | python3 -c 'print(1)'");           has "R9 a walk piped into a quoted python is refused" "$out" '"deny"'

echo "— a walk carried as data is not a walk"
out=$(bash_hook "$(printf "python3 - <<'PY'\nold='%s'\nPY\necho done" "$W")"); lacks "D1 a heredoc body quoting the walk passes" "$out" '"deny"'
out=$(bash_hook "python3 -c 'print(\"$W\")'");           lacks "D2 a python -c string quoting the walk passes" "$out" '"deny"'
out=$(bash_hook "echo \"$W\"");                          lacks "D3 an echo of the walk passes" "$out" '"deny"'
out=$(bash_hook "python3 -c \"print('grep -rn state: prds')\""); lacks "D4 grep -r state: inside a quoted string passes" "$out" '"deny"'
out=$(bash_hook "sed -i '' 's/$W/x/' f.sh");             lacks "D5 an edit whose sed script quotes the walk passes" "$out" '"deny"'
out=$(bash_hook "python3 $D/walkfix.py");                lacks "D6 a script run by path passes" "$out" '"deny"'
out=$(bash_hook "echo \"a \\\" $W\"");                   lacks "D7 an escaped quote inside the string does not end it" "$out" '"deny"'

echo "— the rule is written"
has "T1 guard.md says a walk carried as data is not a walk" "$(cat "$ROOT/references/parts/guard.md")" 'carried as data'
has "T2 guard.py names the exception — the string a walker or sh -c runs" "$(cat "$GUARD")" 'RUNS_ITS_STRING'
[ -z "$(ls "$ROOT/resources/board/state/guard" 2>/dev/null | grep walk-probe)" ]; ok "T3 nothing written under the real state dir" $?

echo; echo "$((pass+fail)) checks · $pass pass · $fail fail"
rm -rf "$D"
[ "$fail" -eq 0 ]
