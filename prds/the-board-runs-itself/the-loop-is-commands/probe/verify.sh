#!/usr/bin/env bash
# the-loop-is-commands — the probe's harness. One line per assertion, a count
# at the end. Every fixture is a copy of the example board in a temp dir.
set -u
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
P="python3 $ROOT/resources/pearde.py"
GUARD="$ROOT/resources/guard.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export PEARDE_GUARD_STATE="$TMP/guardstate"   # the hook fixtures' session block lands here, not under resources/board/state/
pass=0; fail=0
ok()  { pass=$((pass+1)); printf '  ok   %s\n' "$1"; }
bad() { fail=$((fail+1)); printf '  FAIL %s\n' "$1"; }
eq()  { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 — got '$2', want '$3'"; fi; }
has() { if grep -qF -- "$3" <<< "$2"; then ok "$1"; else bad "$1 — lacks '$3'"; fi; }
lacks() { if grep -qF -- "$3" <<< "$2"; then bad "$1 — still carries '$3'"; else ok "$1"; fi; }
export PEARDE_AS=engineer

echo "── the pages"
L="$(wc -l < "$ROOT/references/parts/loop.md" | tr -d ' ')"
S="$(wc -l < "$ROOT/references/parts/solo.md" | tr -d ' ')"
[ "$L" -le 120 ] && ok "loop.md is $L lines, ≤ 120" || bad "loop.md is $L lines"
[ "$S" -le 25 ] && ok "solo.md is $S lines, ≤ 25" || bad "solo.md is $S lines"
eq "loop.md carries the seven-row table" "$(grep -c '^| [1-7] ' "$ROOT/references/parts/loop.md")" "7"
eq "README carries the same seven rows" "$(grep -c '^| [1-7] ' "$ROOT/README.md")" "7"
for c in $(grep -oE 'pearde [a-z]+' "$ROOT/references/parts/loop.md" | awk '{print $2}' | sort -u); do
  if $P "$c" --help >/dev/null 2>&1; then ok "pearde $c --help exits 0"; else bad "pearde $c --help failed"; fi
done
eq "no part says never take a worker's word" "$(grep -ci 'never take a worker' "$ROOT"/references/parts/*.md "$ROOT/README.md" | awk -F: '{s+=$2} END{print s}')" "0"
eq "handles.md carries no pending mark" "$(grep -c 'pending ·' "$ROOT/references/parts/handles.md")" "0"
lacks "pearde help prints no not-yet line" "$($P help 2>&1)" "not yet"
has "states.md names sweep on the claimed row" "$(grep '^| `claimed`' "$ROOT/references/parts/states.md")" 'sweep --apply'
has "guard.md wires the Edit|Write matcher" "$(cat "$ROOT/references/parts/guard.md")" '"matcher": "Edit|Write"'
has "drill.md writes the tree through refine" "$(sed -n '/^## Output/,$p' "$ROOT/references/drill.md")" 'pearde refine <prd> < split'
has "system.md sends the first run to init" "$(cat "$ROOT/references/system.md")" '`pearde init` — English by default'
lacks "workers.md names no verify: key" "$(cat "$ROOT/references/parts/workers.md")" '`verify:` command'

echo "── the guard: a state written by hand"
G="$TMP/proj"; python3 "$ROOT/resources/board/plan.py" example "$G" >/dev/null
F="$G/prds/next/prd.md"
hook() { # tool json — the hook payload built from the environment, so no quoting can eat it
  J="$(TOOL="$1" CWD="$G" INPUT="$2" python3 -c 'import json,os; print(json.dumps({"tool_name":os.environ["TOOL"],"cwd":os.environ["CWD"],"session_id":"probe","tool_input":json.loads(os.environ["INPUT"])}))' 2>&1)" || { echo "builder failed: $J"; return; }
  printf "%s" "$J" | python3 "$GUARD" pre; }
wjson() { # file — a Write payload whose tool_input is the JSON in file
  J="$(CWD="$G" F="$1" python3 -c 'import json,os; print(json.dumps({"tool_name":"Write","cwd":os.environ["CWD"],"session_id":"probe","tool_input":json.load(open(os.environ["F"]))}))' 2>&1)" || { echo "builder failed: $J"; return; }
  printf "%s" "$J" | python3 "$GUARD" pre; }
O="$(hook Edit "{\"file_path\":\"$F\",\"old_string\":\"state: open\",\"new_string\":\"state: specced\"}")"
has "Edit changing state: is denied" "$O" '"permissionDecision": "deny"'
has "  …naming pearde set with the PRD and state" "$O" 'pearde set next specced'
IN="{\"file_path\":\"$F\",\"old_string\":\"# next\",\"new_string\":\"# next!\"}"
eq "Edit of a body line passes" "$(hook Edit "$IN")" ""
python3 - "$F" > "$TMP/w1.json" <<'PY'
import json,sys; t=open(sys.argv[1]).read(); print(json.dumps({"file_path":sys.argv[1],"content":t.replace("# next","# next!")}))
PY
eq "Write keeping state: passes" "$(wjson "$TMP/w1.json")" ""
python3 - "$F" > "$TMP/w2.json" <<'PY'
import json,sys; t=open(sys.argv[1]).read(); print(json.dumps({"file_path":sys.argv[1],"content":t.replace("state: open","state: done")}))
PY
has "Write changing state: is denied" "$(wjson "$TMP/w2.json")" 'pearde set next done'
IN="{\"file_path\":\"$G/prds/fresh/prd.md\",\"content\":\"---\\nstate: open\\n---\\n# fresh\\n\"}"
has "Write of a new prd.md with a state: is denied naming add" "$(hook Write "$IN")" 'pearde add'
IN="{\"file_path\":\"$G/prds/next/specs/x.md\",\"old_string\":\"state: open\",\"new_string\":\"state: done\"}"
eq "a spec file is not matched" "$(hook Edit "$IN")" ""
IN="{\"file_path\":\"$TMP/prd.md\",\"old_string\":\"state: open\",\"new_string\":\"state: done\"}"
eq "a prd.md outside a board is not matched" "$(hook Edit "$IN")" ""
IN="{\"command\":\"python3 $ROOT/resources/pearde.py set next open --board $G/prds\"}"
eq "pearde set through Bash passes the hook" "$(hook Bash "$IN")" ""
IN="{\"command\":\"python3 $ROOT/resources/pearde.py set next open --board $G/prds\"}"
eq "  …and passes again — a transition is never a repeated read" "$(hook Bash "$IN")" ""
eq "the state file still says open — the hook wrote nothing" "$(grep '^state:' "$F")" "state: open"

echo "── sweep"
W="$TMP/w"; python3 "$ROOT/resources/board/plan.py" example "$W" >/dev/null
git -C "$W" init -q && git -C "$W" add -A && git -C "$W" -c user.email=a@b -c user.name=t commit -qm base
B="$W/prds"
python3 "$ROOT/resources/board/init.py" settings claim-ttl=1m --board "$B" >/dev/null
age() { T="$(python3 -c 'import time; print(time.strftime("%Y%m%d%H%M.%S", time.localtime(time.time()-120)))')"; find "$W" -not -path '*/.git*' -exec touch -t "$T" {} +; }
age
O="$($P sweep --board "$B")"; RC=$?
eq "sweep exits 0" "$RC" "0"
has "sweep lists building" "$O" "building · claimed · claim worker-building"
lacks "  …not finished — a PRD to collect is never silent" "$O" "finished"
has "  …with the age word the scan prints" "$O" "silent 2m"
mkdir -p "$W/src"; touch "$W/src/app.py"
eq "touching a footprint path in repo clears it" "$($P sweep --board "$B")" "sweep: no claim silent past claim-ttl 1m"
rm "$W/src/app.py"
$P set next analyzing --force --board "$B" >/dev/null 2>&1
$P set big/second analyzing --force --board "$B" >/dev/null 2>&1
python3 - "$B" "$ROOT/resources/board" <<'PY'
import sys, os; sys.path.insert(0, sys.argv[2]); import edit
b = sys.argv[1]
edit.set_key(os.path.join(b, "next/prd.md"), "claim", "worker-next 2026-08-28 10:00")
edit.set_key(os.path.join(b, "big/second/prd.md"), "claim", "worker-second 2026-08-28 10:00")
os.makedirs(os.path.join(b, "next/specs"), exist_ok=True)
open(os.path.join(b, "next/specs/spec01.md"), "w").write("---\ncomplexity: 3\n---\n# spec01\n\n## Acceptance\n\n- [ ] x\n")
open(os.path.join(b, ".round.md"), "w").write("# Round\n\n## Established\n- big/second is mine · 10:00\n")
PY
age
O="$($P sweep --apply --board "$B")"; RC=$?
eq "sweep --apply exits 0" "$RC" "0"
has "an analyst with specs on disk is sent to specced, not moved" "$O" 'specs on disk — an analyst that finished: `pearde specced next`'
eq "  …and stays analyzing" "$(grep '^state:' "$B/next/prd.md")" "state: analyzing"
has "a claim the round file names is left" "$O" "big/second · analyzing · claim worker-second 2026-08-28 10:00 · silent 2m · named in prds/.round.md"
eq "  …and stays analyzing" "$(grep '^state:' "$B/big/second/prd.md")" "state: analyzing"
has "the stale implementer's line is printed" "$O" "▸ building: claimed → failed"
has "  …and ends round file owed before as" "$O" "· round file owed · as engineer"
eq "  …and the state is failed" "$(grep '^state:' "$B/building/prd.md")" "state: failed"
has "  …with a ## Failure saying it was swept" "$(cat "$B/building/prd.md")" "swept "
eq "  …and the claim cleared" "$(grep -c '^claim:' "$B/building/prd.md")" "0"
sed -i.bak 's/^- big\/second is mine.*$/- nothing/' "$B/.round.md"; age
O="$($P sweep --apply --board "$B")"
eq "unnamed in the round file, the analyst without specs goes open" "$(grep '^state:' "$B/big/second/prd.md")" "state: open"
$P sweep x --board "$B" >/dev/null 2>&1; eq "sweep with an argument is refused" "$?" "1"

echo "── claim records, answer owes"
$P retry building --board "$B" >/dev/null 2>&1
$P set building specced --force --board "$B" >/dev/null 2>&1
O="$($P claim building w2 --board "$B" 2>&1)"
has "claim prints the line with round file owed" "$O" "▸ building: specced → claimed"
has "  …round file owed before as" "$O" "· round file owed · as engineer"
[ -f "$B/.claims/building/diff" ] && ok "claim wrote prds/.claims/building/diff" || bad "no .claims/building/diff"
[ -f "$B/.claims/building/gate" ] && ok "  …and the gate record" || bad "no .claims/building/gate"
$P answer asking Q1 "the first answer" --board "$B" >/dev/null 2>&1
has "answer owes prds/asking/prd.md in .claims/riders" "$(cat "$B/.claims/riders" 2>/dev/null)" "prds/asking/prd.md"
N="$TMP/nogit"; python3 "$ROOT/resources/board/plan.py" example "$N" >/dev/null
$P set big/second specced --force --board "$N/prds" >/dev/null 2>&1
O="$($P claim big/second w3 --board "$N/prds" 2>&1)"; RC=$?
eq "claim outside a git repo still moves the state" "$RC" "0"
has "  …and says there is no baseline" "$O" "claim: no baseline"

echo "── fixtures"
eq "no fixture prd.md under prds/" "$(find "$ROOT/prds" -path '*/probe/*' -name prd.md | wc -l | tr -d ' ')" "0"
printf '\n%d checks · %d pass · %d fail\n' "$((pass+fail))" "$pass" "$fail"
[ "$fail" -eq 0 ]
