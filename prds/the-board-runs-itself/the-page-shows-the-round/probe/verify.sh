#!/usr/bin/env bash
# the-page-shows-the-round — probe harness. Fixture: a copy of the example
# board in a temp dir, git-initialised, claim-ttl 1m, every mtime two minutes
# back. Never under prds/. Needs the daemon for the served half and
# playwright-core (NODE_PATH) for the page half; each says so when absent.
set -u
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
PLAN="$ROOT/resources/board/plan.py"
SERVE="$ROOT/resources/board/serve.py"
PAGE="$(cd "$(dirname "$0")" && pwd)/page.js"
PORT="${PEARDE_PORT:-8443}"
D="$(mktemp -d)"; trap 'cleanup' EXIT
NAME=""
cleanup() {
  [ -n "$NAME" ] && curl -s -X POST "http://127.0.0.1:$PORT/unregister" \
    -d "{\"board\":\"$NAME\"}" >/dev/null 2>&1
  rm -rf "$D"
}
pass=0; fail=0
ok()  { pass=$((pass+1)); echo "  ok    $1"; }
bad() { fail=$((fail+1)); echo "  FAIL  $1${2:+  — $2}"; }
check() { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "want [$3] got [$2]"; fi; }
has()   { if printf '%s' "$2" | grep -qE -- "$3"; then ok "$1"; else bad "$1" "no /$3/ in: $(printf '%s' "$2" | head -c 160)"; fi; }
lacks() { if printf '%s' "$2" | grep -qE -- "$3"; then bad "$1" "found /$3/"; else ok "$1"; fi; }

python3 "$PLAN" example "$D/b" >/dev/null
B="$D/b/prds"
( cd "$D/b" && git init -q . )
printf 'claim-ttl: 1m\n' | sed -i '' -e '/^gantt-day: 8h$/r /dev/stdin' "$B/settings.md"
python3 "$PLAN" plan "$B" >/dev/null 2>&1      # .plan.json — the payload schedules off it
OLD="$(date -v-2M +%Y%m%d%H%M 2>/dev/null || date -d '2 minutes ago' +%Y%m%d%H%M)"
back() { find "$D/b" -path "$D/b/.git" -prune -o -type f -exec touch -t "$OLD" {} + ; }
back

# ── plan.py: the one rule ────────────────────────────────────────────────
py() { python3 - "$B" "$@" <<'PY'
import sys, os
sys.path.insert(0, os.path.join(os.environ["ROOT"], "resources", "board"))
import plan
board = sys.argv[1]; prds = plan.scan(board); st = plan.board_settings(board)
q = sys.argv[2]
if q == "silent":
    for rel in ("building", "finished", "asking", "next"):
        v = plan.silent_of(prds[rel], st) if rel in prds else "absent"
        print(rel, "silent" if isinstance(v, float) else v)
elif q == "ttl":
    for v in ("1m", "2h", "1d", "30", "", "junk"):
        print(v or "none", plan.claim_ttl({"claim-ttl": v} if v else {}))
elif q == "age":
    print(plan.fmt_age(42.4), plan.fmt_age(100), plan.fmt_age(0.2))
elif q == "payload":
    mp, _ = plan.load_map(board)
    p = plan.gantt_payload(board, prds, mp, st)
    t = {x["rel"]: x for x in p["tasks"]}
    print("building", "num" if isinstance(t["building"]["silent"], float) else t["building"]["silent"])
    print("finished", t["finished"]["silent"])
    print("vision", repr(p["vision"]["purpose"]))
elif q == "repo":
    print(plan.prd_repo(prds["building"]))
PY
}
export ROOT
out="$(py silent)"
has   "silent_of: building (claimed, in flight) is silent past the ttl" "$out" "^building silent"
has   "silent_of: finished (to collect) is never silent" "$out" "finished None"
has   "silent_of: asking (question, no claim) is not silent" "$out" "asking None"
has   "silent_of: next (open) is not silent" "$out" "next None"
check "prd_repo: a board in its own repo resolves to that repo" "$(py repo)" "$D/b"
out="$(py ttl)"
has   "claim_ttl: 1m is one minute" "$out" "^1m 1.0"
has   "claim_ttl: 2h is 120" "$out" "^2h 120.0"
has   "claim_ttl: 1d is a day of hours" "$out" "^1d 480.0"
has   "claim_ttl: a bare number is minutes" "$out" "^30 30.0"
has   "claim_ttl: missing reads 30" "$out" "^none 30.0"
has   "claim_ttl: junk reads 30" "$out" "^junk 30.0"
check "fmt_age: the page's own spelling" "$(py age)" "42m 1.7h 0m"
out="$(py payload)"
has   "payload: the held row carries silent as minutes" "$out" "^building num"
has   "payload: the collect row carries null" "$out" "^finished None"
has   "payload: vision.purpose is empty with no vision.md" "$out" "vision ''"
printf -- '---\nvision: Ship the line.\n---\n' > "$B/vision.md"
has   "payload: vision.purpose is the vision sentence" "$(py payload)" "vision 'Ship the line.'"
rm -f "$B/vision.md"

# ── scan: the same word on the same line ─────────────────────────────────
scan="$(python3 "$PLAN" scan "$B")"
has   "scan: the building line ends in silent <age>" "$scan" "building .* · silent [0-9]+m$"
lacks "scan: the finished line carries no silent word" "$scan" "finished .*silent"
check "scan: exactly one silent word on the board" "$(printf '%s' "$scan" | grep -c 'silent')" "1"
mkdir -p "$D/b/src" && touch "$D/b/src/app.py"
lacks "scan: touching a footprint path in the repo flips building to held" "$(python3 "$PLAN" scan "$B")" "silent"
back
has   "scan: setting it back flips it to silent again" "$(python3 "$PLAN" scan "$B")" "building .*silent"
touch "$B/building/specs/spec01.md"
lacks "scan: touching a file under the PRD dir flips it to held" "$(python3 "$PLAN" scan "$B")" "silent"
back
# a fresh-mtime copy with the default ttl: not one silent word, nothing added
python3 "$PLAN" example "$D/c" >/dev/null; find "$D/c" -type f -exec touch {} +
lacks "scan: a fresh copy at the default ttl prints no silent word" "$(python3 "$PLAN" scan "$D/c/prds")" "silent"
lacks "scan: nor a claim-ttl line of any kind" "$(python3 "$PLAN" scan "$D/c/prds")" "claim-ttl"

# ── serve.py: the two routes, live ───────────────────────────────────────
if ! curl -s "http://127.0.0.1:$PORT/status" >/dev/null 2>&1; then
  echo "  skip  no daemon on :$PORT — the served half was not run"
else
  # the copy declares `name: example`; the daemon keys it by that when free
  python3 "$SERVE" ensure "$B" >/dev/null 2>&1
  NAME="$(curl -s "http://127.0.0.1:$PORT/status" | python3 -c "import json,sys;print([b['name'] for b in json.load(sys.stdin)['boards'] if b['path']=='$B'][0])")"
  check "serve: the fixture registered under its own name" "$NAME" "example"
  # /round was removed (9a8f6ac — the page dropped the panel, nothing fetches
  # it); the endpoint stays gone, and the probe asserts the removal
  check "/round is gone — 404, not a route to a file nothing reads" "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/round?board=$NAME")" "404"
  check "GET /report: absent file is null" "$(curl -s "http://127.0.0.1:$PORT/report?board=$NAME" | python3 -c 'import json,sys;print(json.load(sys.stdin)["text"])')" "None"
  check "/round stays gone with a .round.md on disk" "$(printf '# Round — probing\n' > "$B/.round.md"; curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/round?board=$NAME")" "404"
  printf '# Where the example stands\n\n*today*\n\nOne worker is **building**.\n\n## In work\n\n- `building` — half done\n' > "$B/report.md"
  check "GET /report: the file, read on the call" "$(curl -s "http://127.0.0.1:$PORT/report?board=$NAME" | python3 -c 'import json,sys;print(json.load(sys.stdin)["text"].splitlines()[0])')" "# Where the example stands"
  back
  if ! node -e 'require("playwright-core")' 2>/dev/null; then
    echo "  skip  no playwright-core on NODE_PATH — the page half was not run"
  else
    sleep 1.2   # the daemon settles the two writes above before the page opens
    J="$(node "$PAGE" "http://127.0.0.1:$PORT/board/$NAME" "$B/.round.md" 2>&1)"
    printf '%s' "$J" | python3 -c 'import json,sys;json.load(sys.stdin)' 2>/dev/null \
      || { echo "  FAIL  page.js did not return JSON:"; printf '%s\n' "$J" | head -5; }
    jq_() { printf '%s' "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print($1)"; }
    check "page: no page error" "$(jq_ 'len(d["errors"])')" "0"
    check "page: the strip reads 1 · 1 · 1 on the example" "$(jq_ 'd["strip"]["text"]')" "1 · 1 · 1"
    check "page: three doors, in the pressure order" "$(jq_ '" · ".join(d["strip"]["labels"])')" "to collect · waiting on you · in flight"
    check "page: the strip is a pearde-now element in the light DOM" "$(jq_ 'd["strip"]["tag"]+" "+str(d["strip"]["light"])')" "pearde-now True"
    check "page: the strip sits under the title, in the first screenful" "$(jq_ 'd["strip"]["top"] < 120')" "True"
    check "page: to collect is a door into the collect filter" "$(jq_ 'd["strip"]["dests"][0]["collect"]')" "1"
    check "page: waiting on you is a door into the hot band" "$(jq_ 'd["strip"]["dests"][1]["state"]')" "hot"
    check "page: in flight is a door into the held band" "$(jq_ 'd["strip"]["dests"][2]["state"]')" "held"
    check "page: a zero is dimmed, never absent" "$(jq_ 'str(d["dimmed"]["n"])+" "+str(d["dimmed"]["dim"])+" "+d["dimmed"]["text"]')" "3 1 0 · 1 · 1"
    check "page: the round panel is a pearde-round element in the light DOM" "$(jq_ 'd["round"]["tag"]+" "+str(d["round"]["light"])')" "pearde-round True"
    check "page: the panel renders Owed first, then Asked, then the rest" "$(jq_ '" ".join(d["round"]["heads"])')" "owed asked established"
    check "page: a rewritten .round.md swaps into the panel within two seconds" "$(jq_ 'str(d["swap"]["got"])+" "+str(d["swap"]["ms"] <= 2000)')" "True True"
    check "page: the held row's payload carries silent" "$(jq_ 'isinstance(d["silent"]["field"], float)')" "True"
    has   "page: the inspector says silent <age> beside holding" "$(jq_ 'd["pane"]')" "holding [0-9]+m · silent [0-9]+m"
    lacks "page: the inspector prints no raw markup for it" "$(jq_ 'd["pane"]')" "<span"
    check "page: seven view buttons, report last" "$(jq_ '" ".join(d["buttons"])')" "timeline board asks list analytics memos report"
    check "page: ⌘7 opens the report view and the URL follows" "$(jq_ 'd["report"]["view"]+" "+str(d["report"]["shown"])')" "#view=report True"
    check "page: the report view is a pearde-report element in the light DOM" "$(jq_ 'd["report"]["tag"]+" "+str(d["report"]["light"])')" "pearde-report True"
    check "page: the report renders report.md's title as prose" "$(jq_ 'd["report"]["h2"][0]')" "Where the example stands"
    check "page: pearde.replace takes the strip and the panel" "$(jq_ 'd["replaced"]["now"]+" "+d["replaced"]["round"]')" "MINE-NOW MINE-ROUND"
  fi
fi

echo
echo "$pass/$((pass+fail)) checks pass"
[ "$fail" -eq 0 ]
