#!/usr/bin/env bash
# tokens-per-transition — the guard counts, the transition hands the count
# over, status prints it, the analytics draw it. Every fixture is a copy of
# the example board in a temp dir; the guard's state dir is a temp dir too
# (`PEARDE_GUARD_STATE`), never resources/board/state/.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
R="$ROOT/resources"
D="$(mktemp -d)"; trap 'rm -rf "$D"' EXIT
pass=0; fail=0
ok()   { pass=$((pass+1)); echo "  ok    $1"; }
bad()  { fail=$((fail+1)); echo "  FAIL  $1 — $2"; }
chk()  { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "want [$3] got [$2]"; fi; }
has()  { if grep -q -- "$3" <<<"$2"; then ok "$1"; else bad "$1" "no /$3/ in: $(head -c 300 <<<"$2")"; fi; }

python3 "$R/board/plan.py" example "$D/ex" >/dev/null
find "$D/ex" -type f -exec touch {} +
B="$D/ex/prds"
export PEARDE_GUARD_STATE="$D/guard" PEARDE_AS=probe
T="$D/transcript.jsonl"
# three assistant lines, two of them one streamed message (same id) — 500 + 300
printf '%s\n' \
 '{"type":"assistant","message":{"id":"m1","usage":{"output_tokens":500}}}' \
 '{"type":"assistant","message":{"id":"m1","usage":{"output_tokens":500}}}' \
 '{"type":"user","message":{"content":"x"}}' \
 '{"type":"assistant","message":{"id":"m2","usage":{"output_tokens":300}}}' > "$T"

hook() {  # tool file -> the guard's stdout
  python3 -c 'import json,sys; print(json.dumps({"session_id":"s1","transcript_path":sys.argv[3],"cwd":sys.argv[4],"hook_event_name":"PreToolUse","tool_name":sys.argv[1],"tool_input":{"file_path":sys.argv[2]} if sys.argv[1]!="Bash" else {"command":sys.argv[2]}}))' "$1" "$2" "$T" "$D/ex" \
    | python3 "$R/guard.py" pre
}
blk() { python3 -c 'import json,os,sys; d=json.load(open(sys.argv[1])); b=d["boards"][os.path.realpath(sys.argv[2])]; print(b.get(sys.argv[3]))' "$D/guard/s1.json" "$B" "$1"; }
row() { [ -f "$B/.transitions.jsonl" ] && sed -n "${1}p" "$B/.transitions.jsonl" | python3 -c 'import json,sys; s=sys.stdin.read(); print(json.loads(s).get(sys.argv[1]) if s.strip() else "")' "$2"; }

echo "## the guard counts"
files=$(ls "$B"/*/prd.md | head -5)
for f in $files; do hook Read "$f" >/dev/null; hook Read "$f" >/dev/null; done
chk "ten reads → calls 10" "$(blk calls)" "10"
chk "ten reads → reads 10" "$(blk reads)" "10"
chk "no refusal yet" "$(blk refused)" "0"
chk "bash 0" "$(blk bash)" "0"
has "since is set" "$(blk since)" '^[0-9]'
chk "transcript path kept" "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["transcript"])' "$D/guard/s1.json")" "$T"
[ -d "$R/board/state/guard" ] && n0=$(ls "$R/board/state/guard" | wc -l | tr -d ' ') || n0=0

echo "## the transition hands it over"
python3 "$R/board/transitions.py" set next specced --force --board "$B" >/dev/null 2>"$D/err" || bad "set --force ran" "$(cat "$D/err")"
chk "one row" "$(wc -l < "$B/.transitions.jsonl" | tr -d ' ')" "1"
chk "row 1 calls 10" "$(row 1 calls)" "10"
chk "row 1 reads 10" "$(row 1 reads)" "10"
chk "row 1 refused 0" "$(row 1 refused)" "0"
chk "row 1 tokens 800 — a streamed message counted once" "$(row 1 tokens)" "800"
chk "row keeps t/prd/from/to" "$(row 1 to)" "specced"
chk "mark moved" "$(blk mark | tr -d ' ')" "{'calls':10,'reads':10,'bash':0,'edits':0,'refused':0,'tokens':800}"
chk "transitions 1" "$(blk transitions)" "1"
[ ! -f "$B/.history.jsonl" ] && ok ".history.jsonl untouched" || bad ".history.jsonl untouched" "written"

echo "## a refusal counts, a bash call counts, the window is the delta"
first=$(echo "$files" | head -1)
out=$(hook Read "$first")
has "third read refused" "$out" '"deny"'
chk "refused 1" "$(blk refused)" "1"
hook Bash "cat $B/settings.md" >/dev/null
chk "bash 1" "$(blk bash)" "1"
hook Edit "$B/next/prd.md" >/dev/null
chk "edits 1" "$(blk edits)" "1"
chk "calls 13" "$(blk calls)" "13"
printf '%s\n' '{"type":"assistant","message":{"id":"m3","usage":{"output_tokens":150}}}' >> "$T"
python3 "$R/board/transitions.py" set next open --force --board "$B" >/dev/null 2>&1
chk "row 2 calls 3 — the calls between" "$(row 2 calls)" "3"
chk "row 2 refused 1" "$(row 2 refused)" "1"
chk "row 2 tokens 150 — the delta" "$(row 2 tokens)" "150"

echo "## status prints the same numbers"
st=$(python3 "$R/board/plan.py" status "$B")
has "this session line" "$st" '^this session: 13 calls · 1 refused · 2 transitions · 6.5 per transition$'
st2=$(PEARDE_GUARD_STATE="$D/none" python3 "$R/board/plan.py" status "$B")
has "no state dir → no guard" "$st2" '^this session: no guard$'

echo "## no guard records nothing"
rm -f "$B/.transitions.jsonl"
PEARDE_GUARD_STATE="$D/none" python3 "$R/board/transitions.py" set next specced --force --board "$B" >/dev/null 2>&1
chk "row calls null" "$(row 1 calls)" "None"
chk "row tokens null" "$(row 1 tokens)" "None"
PEARDE_GUARD_STATE="$D/guard" python3 "$R/board/transitions.py" set next open --force --board "$B" >/dev/null 2>&1
chk "unreadable transcript → tokens null" "$( rm -f "$T"; PEARDE_GUARD_STATE="$D/guard" python3 "$R/board/transitions.py" set next specced --force --board "$B" >/dev/null 2>&1; row 3 tokens)" "None"

echo "## the payload carries the series"
python3 "$R/board/plan.py" gantt "$B" >/dev/null 2>&1
html="$B/.view.html"
pay() { python3 - "$html" "$1" <<'PY'
import json,re,sys
h=open(sys.argv[1],encoding="utf-8").read()
m=re.search(r'(?s)window\.__PAYLOAD__ = (\{.*?\});(window\.__REPORTMTIME__|</script>)',h)
d=json.loads(m.group(1)); print(json.dumps(eval("d"+sys.argv[2])))
PY
}
chk "transitions in the payload" "$(pay '["transitions"].__len__()')" "3"
chk "guard sessions in the payload" "$(pay '["guard"]["sessions"][0]["refused"]')" "1"
PEARDE_GUARD_STATE="$D/none" python3 "$R/board/plan.py" gantt "$B" >/dev/null 2>&1
chk "no state dir → guard null" "$(pay '["guard"]')" "null"

echo "## the analytics view draws the two series"
NP="${NODE_PATH:-/Users/feb/gstack/node_modules}"
if NODE_PATH="$NP" node -e 'require("playwright-core")' 2>/dev/null; then
  # with the guard's state: the last three transitions, two of them counted
  PEARDE_GUARD_STATE="$D/guard" python3 "$R/board/plan.py" gantt "$B" >/dev/null 2>&1
  v=$(NODE_PATH="$NP" node "$HERE/viewcheck.js" "$html")
  j() { python3 -c 'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' "$1" <<<"$v"; }
  chk "no page error" "$(j errors)" "[]"
  has "calls-per-transition chart is there" "$(j calls)" "^Calls per transition"
  has "calls named as the proxy" "$(j calls)" "calls are the proxy for tokens"
  chk "one dot per counted transition" "$(j callsDots)" "2"
  has "refusals-per-session chart is there" "$(j refusals)" "^Refusals per session"
  chk "one bar per session" "$(j refusalRows)" "1"
  has "the bar carries the refusal" "$(j refusals)" "1 · 13 calls · 4 transitions"
  # without: both read `no guard`
  PEARDE_GUARD_STATE="$D/none" python3 "$R/board/plan.py" gantt "$B" >/dev/null 2>&1
  v=$(NODE_PATH="$NP" node "$HERE/viewcheck.js" "$html")
  has "no state file → calls chart reads no guard" "$(j calls)" "no guard"
  has "no state file → refusals chart reads no guard" "$(j refusals)" "no guard"
else
  echo "  skip  playwright-core not under NODE_PATH — the view checks did not run"
fi

echo "## nothing leaked"
[ -d "$R/board/state/guard" ] && n1=$(ls "$R/board/state/guard" | wc -l | tr -d ' ') || n1=0
chk "no session file written under resources/board/state" "$n1" "$n0"
chk "no fixture prd.md under the real board" "$(find "$ROOT/prds" -path '*/probe/*' -name prd.md | wc -l | tr -d ' ')" "0"

echo
echo "$((pass+fail)) checks · $pass pass · $fail fail"
[ "$fail" = 0 ]
