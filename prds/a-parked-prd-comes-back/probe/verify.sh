#!/usr/bin/env bash
# a-parked-prd-comes-back — `release <prd> open` un-parks; every other parked
# transition names that way out. Runs on a copy of the example board under
# mktemp; never the real board. One line per assertion, a count at the end.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
D="$(mktemp -d)"; SCR="$(mktemp -d)"; trap 'rm -rf "$D" "$SCR"' EXIT
export PEARDE_AS=engineer PEARDE_PORT=1
python3 "$ROOT/resources/board/plan.py" example "$D" >/dev/null
find "$D" -type f -exec touch {} +
B="$D/prds"; P="$B/big/second/prd.md"; J="$B/.transitions.jsonl"
pass=0; fail=0
ok()  { pass=$((pass+1)); echo "  ok   $1"; }
bad() { fail=$((fail+1)); echo "  FAIL $1"; [ -n "${2:-}" ] && echo "       ▸ $2"; }
t()   { python3 "$ROOT/resources/board/transitions.py" "$@" --board "$B" >"$SCR/out" 2>"$SCR/err"; echo $? >"$SCR/rc"; }
rc()  { cat "$SCR/rc"; }
has() { if grep -qF -- "$3" "$SCR/$2"; then ok "$1"; else bad "$1" "$(cat "$SCR/$2")"; fi; }
lacks() { if grep -qF -- "$3" "$SCR/$2"; then bad "$1" "$(cat "$SCR/$2")"; else ok "$1"; fi; }
eq()  { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "got '$2' want '$3'"; fi; }
state() { sed -n 's/^state: //p' "$P"; }

echo "A. the refusal today, and the edge"
t set big/second later --force;            eq "set --force parks on a user word" "$(state)" "later"
rows0=$(wc -l <"$J" | tr -d ' ')
t release big/second open;                 eq "release <parked> open exits 0" "$(rc)" 0
has "the line reads later → open" out "big/second: later → open"
lacks "the line is not forced" out "forced"
eq "state is open" "$(state)" "open"
eq "claim: absent" "$(grep -c '^claim:' "$P")" 0
eq "one transition row written" "$(wc -l <"$J" | tr -d ' ')" "$((rows0+1))"
has "the row names the edge" out "later → open"

echo "B. the one target"
t set big/second later --force
t release big/second specced;              eq "release <parked> specced exits 1" "$(rc)" 1
has "…naming the state as parked" err 'big/second is `later` (parked)'
has "…and the one way out" err '`release big/second open` brings it back'
eq "nothing written" "$(state)" "later"

echo "C. defer round-trips"
t release big/second open
t defer big/second;                        eq "defer parks" "$(state)" "deferred"
t release big/second open;                 eq "release deferred open exits 0" "$(rc)" 0
has "the line reads deferred → open" out "deferred → open"
eq "state is open" "$(state)" "open"

echo "D. a live state is not parked"
t set big/second specced --force
t release big/second open;                 eq "release specced open still refuses" "$(rc)" 1
has "…with today's wording" err "analyzing → refine|question|open, claimed → blocked|failed"
lacks "…and no parked line" err "(parked)"
t set big/second analyzing --force
t release big/second open;                 eq "release analyzing open is today's edge, unchanged" "$(rc)" 0

echo "E. every other parked transition names the way out"
t set big/second later --force
t claim big/second w;      eq "claim refuses" "$(rc)" 1;   has "  …naming the way out" err '`release big/second open` brings it back'
t set big/second specced;  eq "set (unforced) refuses" "$(rc)" 1; has "  …naming the way out" err '`release big/second open` brings it back'
lacks "  …not the escape hatch" err "no command moves"
t retry big/second;        eq "retry refuses" "$(rc)" 1;   has "  …naming the way out" err '`release big/second open` brings it back'
t unblock big/second;      eq "unblock refuses" "$(rc)" 1; has "  …naming the way out" err '`release big/second open` brings it back'
t defer big/second;        eq "defer refuses" "$(rc)" 1;   has "  …naming the way out" err '`release big/second open` brings it back'
eq "state untouched throughout" "$(state)" "later"
t set big/second later --force; eq "already-there says so, not parked" "$(rc)" 1; has "  …already" err 'already `later`'

echo "F. a parked container is collect's"
C=big   # two children, no specs, no open box: every child done makes it a container
t set big/second done --force
echo "       container under test: $C"
t set "$C" later --force;                  eq "the container parks" "$(sed -n 's/^state: //p' "$B/$C/prd.md")" "later"
t release "$C" open;                       eq "release <container> open exits 1" "$(rc)" 1
has "…pointing at collect" err "pearde collect closes it"
has "…with the one predicate's words" err "container: every child done"
eq "…and writes nothing" "$(sed -n 's/^state: //p' "$B/$C/prd.md")" "later"

echo "G. a parked state that names a person goes through answer's gate"
t set big/second hitl --force
t release big/second open;                 eq "release hitl open runs answer's gate" "$(rc)" 1
has "…and names the round" err "answer:"

echo "H. prose"
has_file() { if grep -qF -- "$3" "$ROOT/$2"; then ok "$1"; else bad "$1"; fi; }
has_file "states.md: the parked paragraph names the way back" references/parts/states.md 'release <prd> open'
has_file "handles.md: the defer row names its inverse" references/parts/handles.md 'release <prd> open'
eq "no fixture prd.md under this PRD's probe" "$(find "$ROOT/prds/a-parked-prd-comes-back/probe" -name prd.md | wc -l | tr -d ' ')" 0

echo "$((pass+fail)) checks · $pass pass · $fail fail"
[ "$fail" -eq 0 ]
