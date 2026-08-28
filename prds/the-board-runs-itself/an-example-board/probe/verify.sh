#!/usr/bin/env bash
# an-example-board — the probe harness.
#
# Copies resources/board/example to a temp dir and asserts what every reader
# says about the copy: `plan.py scan` finds a row in every band, the memo,
# the workflow and the round parse, no generated file sits in the example
# itself, `index.py check` reads a directory row in both directions, and
# `viewtest.js --example` renders and snapshots six views keyed `example`.
#
# Fixtures are built at RUN TIME under a temp dir and never under prds/. The
# manifest check runs against a temp manifest through `index.FILES`, so it
# needs no row in references/files.md to be measured.
#
#   bash prds/the-board-runs-itself/an-example-board/probe/verify.sh
#   NODE_PATH=<dir holding playwright-core> bash …/verify.sh   (runs viewtest too)
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PLAN="$ROOT/resources/board/plan.py"
EX="$ROOT/resources/board/example"
D="$(mktemp -d)"
trap 'rm -rf "$D"' EXIT

pass=0; fail=0; skip=0
ok()   { pass=$((pass+1)); printf '  ok   %s\n' "$1"; }
bad()  { fail=$((fail+1)); printf '  FAIL %s\n' "$1"; }
skipped() { skip=$((skip+1)); printf '  skip %s\n' "$1"; }
have() { case "$2" in *"$3"*) ok "$1";; *) bad "$1 — no '$3' in:"; printf '%s\n' "$2" | sed 's/^/       /';; esac; }
lacks() { case "$2" in *"$3"*) bad "$1 — '$3' present in:"; printf '%s\n' "$2" | sed 's/^/       /';; *) ok "$1";; esac; }

# ── the copy ─────────────────────────────────────────────────────────────────
OUT="$(python3 "$PLAN" example "$D/copy" 2>&1)"; rc=$?
[ $rc -eq 0 ] && ok "example <dir> exits 0" || bad "example <dir> exits 0 (got $rc): $OUT"
have "it prints the board path" "$OUT" "example: $D/copy/prds"
[ -f "$D/copy/prds/settings.md" ] && ok "settings.md is in the copy" || bad "settings.md is in the copy"
[ -f "$D/copy/README.md" ] && ok "README.md is in the copy" || bad "README.md is in the copy"
OUT="$(python3 "$PLAN" example "$D/copy" 2>&1)"; rc=$?
[ $rc -ne 0 ] && ok "a non-empty dir is refused" || bad "a non-empty dir is refused (exited 0)"
have "and the refusal says so" "$OUT" "is not empty"
mkdir -p "$D/empty"; python3 "$PLAN" example "$D/empty" >/dev/null 2>&1 && ok "an empty dir is filled" || bad "an empty dir is filled"
OUT="$(python3 "$PLAN" example 2>&1)"; [ $? -eq 2 ] && ok "no dir is usage, exit 2" || bad "no dir is usage, exit 2: $OUT"
python3 - "$ROOT" <<'PY' && ok "plan.py exposes COMMANDS['example']" || bad "plan.py exposes COMMANDS['example']"
import sys, os
sys.path.insert(0, os.path.join(sys.argv[1], "resources", "board"))
import plan
assert callable(plan.COMMANDS["example"])
PY

# ── the example itself carries nothing generated ─────────────────────────────
GEN="$(find "$EX" \( -name '.plan.json' -o -name '.round.md' -o -name '.history.jsonl' -o -name '.view.html' \) | wc -l | tr -d ' ')"
[ "$GEN" = "0" ] && ok "no generated file inside the example" || bad "no generated file inside the example ($GEN found)"
N="$(find "$EX/prds" -name prd.md | wc -l | tr -d ' ')"
[ "$N" = "8" ] && ok "eight prd.md files" || bad "eight prd.md files (got $N)"

# ── every reader, on the copy ────────────────────────────────────────────────
SCAN="$(python3 "$PLAN" scan "$D/copy" 2>&1)"
have "scan counts 8 PRDs"                     "$SCAN" "8 PRDs"
have "collect has one"                        "$SCAN" "collect — 1 finished"
have "and it is finished"                     "$SCAN" "· finished · "
have "waiting on you has one"                 "$SCAN" "waiting on you — 1"
have "and it is asking"                       "$SCAN" "question  · asking"
have "in flight has one"                      "$SCAN" "in flight — 1 held"
have "building shows 3/5 boxes"               "$SCAN" "· building · p60 · w8 · wf fix-a-line · boxes 3/5"
have "its claim is the written timestamp"     "$SCAN" "claim worker-building since 2026-08-28 13:49"
have "ready has one"                          "$SCAN" "ready — 1 dispatchable"
have "and it is big/second"                   "$SCAN" "open      · big/second"
have "gated has at least one"                 "$SCAN" "gated — 2"
have "next is gated on building"              "$SCAN" "· next · p58 · w12 · needs building"
have "the parent weighs zero"                 "$SCAN" "· big · p62 · w0"
lacks "no fixture leaks .round.md"            "$SCAN" "round: $D/copy/prds/.round.md
"
WF="$(python3 "$ROOT/resources/workflows.py" check "$D/copy/prds" 2>&1)"
[ -z "$WF" ] && ok "workflows.py check is silent on the copy" || bad "workflows.py check is silent on the copy: $WF"
BR="$(python3 "$ROOT/resources/workflows.py" brief fix-a-line "$D/copy/prds" 2>&1)"
have "brief inlines the first atomic"  "$BR" "find-the-line"
have "brief inlines the second atomic" "$BR" "change-the-line"
MM="$(python3 "$ROOT/resources/memos.py" check "$D/copy/prds" 2>&1)"
[ -z "$MM" ] && ok "memos.py check is silent on the copy" || bad "memos.py check is silent on the copy: $MM"
QL="$(python3 "$ROOT/resources/questions.py" list "$D/copy/prds" 2>&1)"
have "questions.py lists asking in question" "$QL" "question"

# ── the manifest reads a directory row, both directions ──────────────────────
# Through a temp manifest: the real one is the orchestrator's to edit. The
# lines about anything else on disk are somebody else's and are filtered out.
IDX="$(python3 - "$ROOT" "$D" <<'PY'
import sys, os, re
root, d = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(root, "resources"))
import index
real = open(index.FILES, encoding="utf-8").read()
base = re.sub(r"^\|\s*@resources/scout/snapshots/[^|]*\|[^\n]*\n", "", real, flags=re.M)
base += "\n| @resources/scout/snapshots/ | the sweep's dated star counts |\n"
base += "| @resources/board/example/ | the example board |\n"
def run(extra, mark):
    m = os.path.join(d, "files-" + mark + ".md")
    open(m, "w", encoding="utf-8").write(base + extra)
    index.FILES = m
    return [p for p in index.check() if "example" in p or "snapshots" in p or "nosuchdir" in p or "nope.tsv" in p]
print("A:" + "|".join(run("", "a")))
nope = os.path.join(root, "resources", "scout", "nope.tsv")
open(nope, "w").close()
try:
    print("B:" + "|".join(run("", "b")))
finally:
    os.remove(nope)
print("C:" + "|".join(run("| @resources/nosuchdir/ | nothing |\n", "c")))
PY
)"
A="$(printf '%s\n' "$IDX" | sed -n 's/^A://p')"; B="$(printf '%s\n' "$IDX" | sed -n 's/^B://p')"; C="$(printf '%s\n' "$IDX" | sed -n 's/^C://p')"
[ -z "$A" ] && ok "two directory rows, both snapshots and the example covered — silent" || bad "two directory rows — silent, got: $A"
have  "a file beside the covered dir still prints" "$B" "resources/scout/nope.tsv is on disk with no row"
lacks "and the covered files stay covered"          "$B" "2026-08-28.tsv"
have  "a directory row naming nothing prints"       "$C" "lists @resources/nosuchdir/ — no such directory"
[ ! -e "$ROOT/resources/scout/nope.tsv" ] && ok "nope.tsv removed after" || bad "nope.tsv removed after"

# ── the view's gate on a copy ────────────────────────────────────────────────
VT="$ROOT/resources/board/viewtest.js"
if node -e 'require("playwright-core")' >/dev/null 2>&1; then
  V="$(node "$VT" --example --snap "$D/snap" 2>&1)"; rc=$?
  [ $rc -eq 0 ] && ok "viewtest --example exits 0" || bad "viewtest --example exits 0 (got $rc)"
  have "every check passed" "$V" "35/35 passed"
  have "the round is on the page" "$V" "no ask card failed to read its PRD  (0 of 1)"
  NS="$(ls "$D/snap" 2>/dev/null | grep -c '^example\.')"
  [ "$NS" = "12" ] && ok "six views snapshotted, keyed example" || bad "six views snapshotted, keyed example (got $NS files)"
  C2="$(node "$VT" --example --check "$D/snap" 2>&1)"
  have "a second copy compares equal" "$C2" "47/47 passed"
  NL="$(ls -d "${TMPDIR:-/tmp}"/pearde-example-* 2>/dev/null | wc -l | tr -d ' ')"
  [ "$NL" = "0" ] && ok "no scratch copy left behind" || bad "no scratch copy left behind ($NL)"
else
  skipped "viewtest --example — playwright-core not resolvable; set NODE_PATH to run it"
fi

# ── nothing ran in place ─────────────────────────────────────────────────────
ST="$(git -C "$ROOT" status --porcelain resources/board/example | grep -v '^??' || true)"
[ -z "$ST" ] && ok "no tracked file under the example moved" || bad "no tracked file under the example moved: $ST"
GEN="$(find "$EX" \( -name '.plan.json' -o -name '.round.md' -o -name '.history.jsonl' -o -name '.view.html' \) | wc -l | tr -d ' ')"
[ "$GEN" = "0" ] && ok "still nothing generated inside the example" || bad "still nothing generated inside the example ($GEN)"

printf '\n%d checks · %d pass · %d fail · %d skipped\n' $((pass+fail)) $pass $fail $skip
[ $fail -eq 0 ]
