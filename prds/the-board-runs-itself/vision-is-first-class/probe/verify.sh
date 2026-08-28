#!/bin/bash
# vision-is-first-class — the probe's harness.
#
# Builds one board in a temp dir, shaped like `an-example-board`'s contract
# (eight PRDs, one per band), and asserts what `plan.py` prints from a
# `prds/vision.md` beside it: the scan's axis line, the `off-axis` mark, the
# depths, `vision --json`, `vision --next` against `plan`'s ready set, the
# `--check` the doctor row reads, and the prose that names all of it. One
# line per assertion, a count at the end. Nothing is written under prds/.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PLAN="$ROOT/resources/board/plan.py"
D="$(mktemp -d)"
trap 'rm -rf "$D"' EXIT
PASS=0; FAIL=0
ok()   { PASS=$((PASS + 1)); echo "  ok   $1"; }
bad()  { FAIL=$((FAIL + 1)); echo "  FAIL $1"; }
has()  { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1 — wanted: $3"; fi; }
lacks(){ if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1 — found: $3"; else ok "$1"; fi; }

B="$D/prds"; mkdir -p "$B"
mk() { mkdir -p "$B/$1"; printf -- '---\nstate: %s\npriority: %s\n%s---\n\n# %s\n' "$2" "$3" "$4" "$1" > "$B/$1/prd.md"; }
mk landed   done     50 ""
mk building claimed  60 $'claim: worker 2026-08-28 13:00\n'
mk finished claimed  55 $'claim: worker 2026-08-28 12:00\n'
mk asking   question 40 ""
mk next     open     45 $'needs:\n  - building\n'
mk big      open     70 ""
mk big/first  done   30 ""
mk big/second open   30 ""
printf -- '---\nname: example\nlanguage: English\n---\n' > "$B/settings.md"

echo "## no vision.md — the scan as it always was"
S0="$(python3 "$PLAN" scan "$B" 2>/dev/null)"
lacks "no axis on the first line"  "$S0" "axis:"
lacks "no vision line"             "$S0" "vision:"
lacks "no off-axis mark"           "$S0" "off-axis"
C0="$(python3 "$PLAN" vision --check "$B" 2>&1)"; RC=$?
[ "$RC" = 0 ] && ok "--check exits 0 with no file" || bad "--check exit $RC with no file"
has "--check says no vision.md" "$C0" "no vision.md"
python3 "$PLAN" vision "$B" >/dev/null 2>&1 && bad "vision exits 0 with no file" || ok "vision exits 1 with no file"

echo "## terminals: [big] — the example board's axis"
printf -- '---\nvision: Every band of the pressure order has one row.\nterminals:\n  - big\n---\n\n# The destination\n' > "$B/vision.md"
S1="$(python3 "$PLAN" scan "$B" 2>/dev/null)"
has "first line carries the axis"  "$(printf '%s' "$S1" | head -1)" "axis: 2 on · 4 off"
has "second line is the vision"    "$(printf '%s' "$S1" | sed -n 2p)" "vision: Every band of the pressure order has one row."
has "next is off-axis"             "$(printf '%s' "$S1" | grep ' next ')" "off-axis"
lacks "big/second is on the axis"  "$(printf '%s' "$S1" | grep 'big/second')" "off-axis"
lacks "big is on the axis"         "$(printf '%s' "$S1" | grep ' big ')" "off-axis"
V1="$(python3 "$PLAN" vision "$B" 2>/dev/null)"
has "vision: the axis line"        "$V1" "axis: 2 on · 4 off · longest chain 1"
has "vision: the chain"            "$V1" "chain: big/second → big"
has "vision: big/second at 1"      "$(printf '%s' "$V1" | sed -n '/^depth 1/,/^$/p')" "big/second [open]"
has "vision: big at 0"             "$(printf '%s' "$V1" | sed -n '/^depth 0/,/^$/p')" "big [open]"
has "vision: the off-axis set"     "$V1" "off-axis — 4 with no path to a terminal"
J1="$(python3 "$PLAN" vision --json "$B" 2>/dev/null)"
JD="$(printf '%s' "$J1" | python3 -c '
import json,sys; d=json.load(sys.stdin)
print(" ".join("%s=%s" % (p["addr"], p["depth"]) for p in d["prds"]), "|", " ".join(sorted(d["off_axis"])), "| chain", d["longest_chain"])')"
has "--json: depths, deepest first"  "$JD" "@example/big/second=1 @example/big=0"
has "--json: off_axis by address"    "$JD" "@example/asking @example/building @example/finished @example/next"
has "--json: longest_chain"          "$JD" "chain 1"
N1="$(python3 "$PLAN" vision --next "$B" 2>/dev/null | sed -n 's/^  · \([^ ]*\) .*/\1/p' | tr '\n' ' ')"
P1="$(python3 "$PLAN" plan "$B" 2>/dev/null | sed -n '/^ready now/,/^$/p' | sed -n 's/^  · \([^ ]*\) .*/\1/p' | tr '\n' ' ')"
[ -n "$N1" ] && [ "$N1" = "$P1" ] && ok "--next is plan's ready set: $N1" || bad "--next '$N1' vs plan '$P1'"
has "--next marks depth"   "$(python3 "$PLAN" vision --next "$B" 2>/dev/null)" "big/second [open] depth 1"
C1="$(python3 "$PLAN" vision --check "$B" 2>&1)"; RC=$?
[ "$RC" = 0 ] && ok "--check exits 0" || bad "--check exit $RC"
has "--check summary" "$C1" "1 terminal · 2 on · 4 off · longest chain 1"
lacks ".plan.json not written by scan or vision" "$(ls -a "$B")" ".vision.json"

echo "## the rules copied from vision.py"
printf -- '---\nvision: x\nterminals:\n  - @example/big\n  - landed\nedges:\n  - "asking -> landed"\n  - "next -> big/second"\n---\n' > "$B/vision.md"
J2="$(python3 "$PLAN" vision --json "$B" 2>/dev/null | python3 -c '
import json,sys; d=json.load(sys.stdin); print(" ".join("%s=%s" % (p["rel"], p["depth"]) for p in d["prds"]))')"
has "own-name rule: @example/big resolves"      "$J2" " big=0"
has "a done terminal costs no hop: asking at 0"  "$J2" "asking=0"
has "an edge is a hop: next at 2"                "$J2" "next=2"
has "a needs: is a hop: building at 3"           "$J2" "building=3"
has "a parent lands after its children"          "$J2" "big/second=1"
S2="$(python3 "$PLAN" scan "$B" 2>/dev/null | head -1)"
has "scan counts live PRDs only — landed is done, not counted" "$S2" "axis: 5 on · 1 off"

echo "## dangling names — the doctor row"
printf -- '---\nvision: x\nterminals:\n  - big\n  - nowhere\nedges:\n  - "asking -> ghost"\n---\n' > "$B/vision.md"
C3="$(python3 "$PLAN" vision --check "$B" 2>&1)"; RC=$?
[ "$RC" = 1 ] && ok "--check exits 1" || bad "--check exit $RC on dangling names"
has "the terminal is named"  "$C3" "terminal nowhere names no PRD"
has "the edge end is named"  "$C3" "edge asking -> ghost: ghost names no PRD"
DOC="$(bash "$ROOT/resources/doctor.sh" "$D" 2>/dev/null)"
has "doctor: vision broken"          "$DOC" "vision      broken  2 names in vision.md resolve to no PRD"
has "doctor: names the terminal"     "$DOC" "terminal nowhere names no PRD"
printf -- '---\nvision: x\nterminals:\n  - big\n---\n' > "$B/vision.md"
has "doctor: vision ok"   "$(bash "$ROOT/resources/doctor.sh" "$D" 2>/dev/null)" "vision      ok      1 terminal · 2 on · 4 off"
rm "$B/vision.md"
has "doctor: vision off"  "$(bash "$ROOT/resources/doctor.sh" "$D" 2>/dev/null)" "vision      off     no vision.md"

echo "## a vision with no terminals prints neither"
printf -- '---\nvision: Only a sentence.\n---\n' > "$B/vision.md"
S4="$(python3 "$PLAN" scan "$B" 2>/dev/null)"
lacks "no axis count"   "$(printf '%s' "$S4" | head -1)" "axis:"
has   "the sentence"    "$(printf '%s' "$S4" | sed -n 2p)" "vision: Only a sentence."
lacks "no off-axis mark" "$S4" "off-axis"
python3 "$PLAN" vision "$B" >/dev/null 2>&1 && bad "vision exits 0 with no terminals" || ok "vision exits 1 with no terminals"
has "--check: declared, no axis" "$(python3 "$PLAN" vision --check "$B" 2>&1)" "vision declared · no terminals — no axis"

echo "## the template reads as a file with no terminals"
cp "$ROOT/references/templates/vision.md" "$B/vision.md"
T="$(cd "$ROOT/resources/board" && python3 -c "
import plan; v=plan.read_vision('$B'); print(v['vision'], '|', v['terminals'], '|', v['edges'])")"
has "template: the sentence parses"      "$T" "<one sentence — the destination> | [] | []"

echo "## registration and the prose"
R="$(cd "$ROOT/resources/board" && python3 -c "
import plan; print('vision' in plan.COMMANDS, plan.COMMANDS['vision'](['--check', '$B']))")"
has "COMMANDS exposes vision, callable(argv) -> exit code" "$R" "True 0"
[ "$(grep -c '"\.vision\.json"' "$PLAN")" = 0 ] && ok "no .vision.json path in plan.py" || bad ".vision.json path still in plan.py"
[ "$(grep -c 'plane_name\|\.plane\.env' "$PLAN")" = 0 ] && ok "plane_name gone" || bad "plane_name still in plan.py"
has "order.md: the axis is vision.md"      "$(cat "$ROOT/references/parts/order.md")" 'The axis is `prds/vision.md`'
lacks "order.md: vision.py sentence gone"  "$(cat "$ROOT/references/parts/order.md")" 'vision.py'
has "board.md: vision.md in the layout"    "$(cat "$ROOT/references/parts/board.md")" 'vision.md         # where the board is going'
has "master.md: the own-name rule"         "$(cat "$ROOT/references/parts/master.md")" '`@<name>/<rel>`, with the `name:`'
has "doctor.sh: the vision row"            "$(cat "$ROOT/resources/doctor.sh")" 'row vision broken'
[ -f "$ROOT/references/templates/vision.md" ] && ok "templates/vision.md exists" || bad "templates/vision.md missing"

echo
echo "verify: $PASS/$((PASS + FAIL)) checks pass"
[ "$FAIL" = 0 ]
