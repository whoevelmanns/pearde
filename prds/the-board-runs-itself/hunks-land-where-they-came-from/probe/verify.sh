#!/usr/bin/env bash
# hunks-land-where-they-came-from — the probe's harness.
#
# A board under its own `git init` in a temp dir, a JS file that another
# session edited above the worker's one-line hunk inside an if/else chain.
# Section A stages it the way step 3 used to (a `-U0` patch with the
# inherited hunk dropped, `git apply --cached --unidiff-zero`) and shows the
# line misplaced; the rest runs `resources/board/collect.py` and reads the
# committed blob. Scratch lives in a second temp dir, never in the fixture.
# One line per assertion, a count at the end.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
COLLECT="$ROOT/resources/board/collect.py"
PASS=0; FAIL=0
export PEARDE_PORT=1          # nothing listens there — the daemon is "down"
export GIT_AUTHOR_NAME=probe GIT_AUTHOR_EMAIL=probe@x \
       GIT_COMMITTER_NAME=probe GIT_COMMITTER_EMAIL=probe@x

ok()   { PASS=$((PASS+1)); echo "  ok   $1"; }
bad()  { FAIL=$((FAIL+1)); echo "  FAIL $1"; [ -n "${2:-}" ] && echo "       got:  $2"; [ -n "${3:-}" ] && echo "       want: $3"; }
eq()   { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "$2" "$3"; fi; }
has()  { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1" "$2" "contains: $3"; fi; }
lacks(){ if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1" "$2" "without: $3"; else ok "$1"; fi; }

TOP="$(mktemp -d)"; W="$(mktemp -d)"
trap 'rm -rf "$TOP" "$W"' EXIT

# ── the fixture ──────────────────────────────────────────────────────────────
# $D is a repo; $D/prds is the board; `finished` is claimed with footprint
# `src`, its one box ticked. `src/view.js` is HEAD's file.
fixture() {
  D="$TOP/$1"; mkdir -p "$D/src" "$D/prds/finished/specs"
  ( cd "$D" && git init -q -b main )
  cat > "$D/prds/settings.md" <<'EOF'
---
name: fixture
language: English
workers: 1
pipeline: 1
---
EOF
  cat > "$D/prds/finished/prd.md" <<'EOF'
---
state: claimed
origin: requested
claim: impl-1 2026-08-28 10:00
priority: 50
complexity: 5
repo: fixture
footprint:
  - src
---

# finished — the report view repaints
EOF
  cat > "$D/prds/finished/specs/spec01.md" <<'EOF'
---
complexity: 5
footprint:
  - src
---

# spec01 — the report view repaints

## Acceptance

- [ ] `src/view.js` repaints the report

## Verify and Proof

```sh
true
```
EOF
  cat > "$D/src/view.js" <<'EOF'
function drawBoard() {}
function drawPlan() {}
function drawReport() {}
function repaintView(view) {
  if (view === "board") drawBoard();
  else if (view === "plan") drawPlan();
}
function fetchPrd(cb) {
  load(function (r) {
    if (r.ok) cb(r);
  });
}
EOF
  ( cd "$D" && git add -A && git commit -q -m "fixture" )
}
# another session's block, above the chain — before the claim
foreign_above() {
  python3 - "$D/src/view.js" <<'EOF'
import sys; p = sys.argv[1]; L = open(p).read().splitlines(True)
L[3:3] = ["function drawNames() {\n", "  // the names column\n", "  return 1;\n", "}\n"]
open(p, "w").write("".join(L))
EOF
}
# the worker's line, inside the chain, and the box ticked
work() {
  python3 - "$D/src/view.js" <<'EOF'
import sys; p = sys.argv[1]; L = open(p).read().splitlines(True)
i = [n for n, l in enumerate(L) if 'view === "plan"' in l][0]
L[i + 1:i + 1] = ['  else if (view === "report") drawReport();\n']
open(p, "w").write("".join(L))
EOF
  sed -i '' 's/- \[ \] `src/- [x] `src/' "$D/prds/finished/specs/spec01.md"
}
run()    { ( cd "$D" && PEARDE_AS=engineer python3 "$COLLECT" --board "$D/prds" "$@" ) 2>&1; }
snap()   { run --snapshot finished > /dev/null; }
head_at(){ ( cd "$D" && git show HEAD:src/view.js | grep -n -F -- "$1" | cut -d: -f1 ); }
work_at(){ grep -n -F -- "$1" "$D/src/view.js" | cut -d: -f1; }
staged_at(){ ( cd "$D" && git show :src/view.js | grep -n -F -- "$1" | cut -d: -f1 ); }
HAVE_NODE=; command -v node > /dev/null && HAVE_NODE=1

# ── A. the old path, by hand: the line lands where `git apply` guesses ───────
echo "A. the old staging misplaces the line"
fixture a; foreign_above; snap; work
( cd "$D" && git diff HEAD -U0 --no-color -- src/view.js ) > "$W/all.diff"
python3 - "$W" "$D/prds/.claims/finished/diff" <<'EOF'
import re, sys
w, basefile = sys.argv[1], sys.argv[2]
def hunks(d):
    head, _, rest = d.partition("\n@@")
    return head + "\n", [h for h in re.split(r"(?m)^(?=@@ )", "@@" + rest) if h.strip()]
body = lambda h: h.split("\n", 1)[1]
head, hs = hunks(open(w + "/all.diff").read())
_, old = hunks(open(basefile).read()); old = {body(h) for h in old}
open(w + "/kept.patch", "w").write(head + "".join(h for h in hs if body(h) not in old))
EOF
has "A the kept patch is the one-line hunk at its working line" "$(cat "$W/kept.patch")" "@@ -6,0 +11 @@"
( cd "$D" && git apply --cached --unidiff-zero - < "$W/kept.patch" ); RC=$?
eq  "A git apply exits 0 — and that is the whole problem" "$RC" "0"
eq  "A the working file holds the line at 11" "$(work_at 'view === "report"')" "11"
eq  "A the old staging puts it at 11 of a blob four lines shorter — inside fetchPrd" "$(staged_at 'view === "report"')" "11"
eq  "A the line above it in the blob is the callback's if" "$( cd "$D" && git show :src/view.js | sed -n '10p' )" "    if (r.ok) cb(r);"
if [ -n "$HAVE_NODE" ]; then
  ( cd "$D" && git show :src/view.js ) > "$W/old.js"; node --check "$W/old.js" 2> /dev/null; RC=$?
  eq  "A node --check passes on the misplaced blob — parsing is not placement" "$RC" "0"
fi
( cd "$D" && git reset -q )

# ── B. the new path: rebuilt by reversal, checked, committed ─────────────────
echo "B. collect stages the line where the working file has it"
fixture b; foreign_above; snap; work
OUT="$(run finished)"; RC=$?
eq  "B exit 0" "$RC" "0"
has "B said by hunk on the line" "$(printf '%s\n' "$OUT" | grep '^▸')" "by hunk src/view.js"
eq  "B the line sits at 7 of HEAD — working 11 minus the four foreign lines" "$(head_at 'view === "report"')" "7"
eq  "B the line above it is the plan branch" "$( cd "$D" && git show HEAD:src/view.js | sed -n '6p' )" "  else if (view === \"plan\") drawPlan();"
lacks "B the foreign block is not in the commit" "$( cd "$D" && git show HEAD:src/view.js )" "drawNames"
has "B the foreign block is still in the tree" "$(cat "$D/src/view.js")" "drawNames"
eq  "B the file stays dirty by exactly the foreign hunk" "$( cd "$D" && git diff --numstat -- src/view.js | cut -f1,2 )" "$(printf '4\t0')"
eq  "B the working file is untouched" "$(work_at 'view === "report"')" "11"
if [ -n "$HAVE_NODE" ]; then
  ( cd "$D" && git show HEAD:src/view.js ) > "$W/new.js"; node --check "$W/new.js" 2> /dev/null; RC=$?
  eq  "B node --check passes on the committed blob" "$RC" "0"
fi

# ── C. every hunk shape reverses: a deletion above, a replacement below ──────
echo "C. deletion above, replacement below, no newline at the end"
fixture c
python3 - "$D/src/view.js" <<'EOF'
import sys; p = sys.argv[1]; L = open(p).read().splitlines(True)
del L[1:3]                                  # theirs: drawPlan and drawReport gone (-2,2 +1,0)
L[-1] = L[-1].rstrip("\n") + " // end"      # theirs: the last line changed, newline dropped
open(p, "w").write("".join(L))
EOF
snap; work
eq  "C the worker's line is at working 5" "$(work_at 'view === "report"')" "5"
OUT="$(run finished)"; RC=$?
eq  "C exit 0" "$RC" "0"
eq  "C committed at 7 — working 5 plus the two deleted lines above" "$(head_at 'view === "report"')" "7"
eq  "C HEAD still has drawPlan and drawReport" "$( cd "$D" && git show HEAD:src/view.js | grep -c 'function draw' )" "3"
eq  "C HEAD's last line is the original, newline restored" "$( cd "$D" && git show HEAD:src/view.js | tail -c 2 | od -An -c | tr -d ' ' )" '}\n'
eq  "C the file stays dirty by the two foreign hunks" "$( cd "$D" && git diff --numstat -- src/view.js | cut -f1,2 )" "$(printf '1\t3')"

# ── D. the offset check refuses a shifted blob, and the index is put back ────
echo "D. the check, on its own and end to end"
fixture d; foreign_above; snap; work
OUT="$( cd "$D" && python3 - "$COLLECT" "$D/prds" <<'EOF'
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location("collect", sys.argv[1])
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
root = os.getcwd()
diff = c.git_out(root, "diff", "HEAD", "-U0", "--no-color", "--", "src/view.js")
_, hunks = c.split_hunks(diff)["src/view.js"]
base = c.baseline(sys.argv[2], "finished")["hunks"]["src/view.js"]
kept = [h for h in hunks if c.hunk_body(h) not in base]
foreign = [h for h in hunks if c.hunk_body(h) in base]
work = open("src/view.js").read()
good = c.reverse_hunks(work, foreign)
n = len(work.splitlines(True))
print("good:", c.misplaced(good, kept, foreign, n))
L = good.splitlines(True); i = [k for k, l in enumerate(L) if "report" in l and "else" in l][0]
line = L.pop(i); L.insert(i + 4, line)
print("shifted:", c.misplaced("".join(L), kept, foreign, n))
print("short:", c.misplaced("".join(L[:-1]), kept, foreign, n))
try:
    c.reverse_hunks(work.replace("names column", "NAMES"), foreign); print("mismatch: passed")
except c.Stop as e:
    print("mismatch:", e)
EOF
)"
has "D a correct blob has no misplacement" "$OUT" "good: []"
has "D a blob with the line four lines down is refused, naming both lines" "$OUT" "shifted: ['hunk @@ +11,1: expected at line 7 of the staged blob, found at 11']"
has "D a blob of the wrong length is refused on its length" "$OUT" "the staged blob holds 12 lines, the working file minus the inherited hunks holds 13"
has "D a foreign hunk whose + lines are not in the file is a refusal" "$OUT" "mismatch: line 4 of the working file is not what its hunk says"
# end to end: a rebuild that misplaces is refused before the commit
N0="$( cd "$D" && git rev-list --count HEAD )"
OUT="$( cd "$D" && PEARDE_AS=engineer python3 - "$COLLECT" "$D/prds" <<'EOF' 2>&1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("collect", sys.argv[1])
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
real = c.reverse_hunks
def shifted(text, hunks):
    L = real(text, hunks).splitlines(True)
    i = [k for k, l in enumerate(L) if "report" in l and "else" in l][0]
    L.insert(i + 4, L.pop(i)); return "".join(L)
c.reverse_hunks = shifted
sys.exit(c.cmd_collect(["finished", "--board", sys.argv[2]]))
EOF
)"; RC=$?
eq  "D exit 1" "$RC" "1"
has "D the refusal names the hunk and both lines" "$OUT" "src/view.js: hunk @@ +11,1: expected at line 7 of the staged blob, found at 11"
has "D nothing committed" "$OUT" "nothing committed, nothing staged"
eq  "D no commit landed" "$( cd "$D" && git rev-list --count HEAD )" "$N0"
eq  "D the index is HEAD again" "$( cd "$D" && git diff --cached --stat | wc -l | tr -d ' ' )" "0"
eq  "D the PRD is still claimed" "$(grep -m1 '^state:' "$D/prds/finished/prd.md")" "state: claimed"

# ── E. a blob that does not parse is refused ────────────────────────────────
echo "E. the parse check"
fixture e
printf 'def a():\n    return 1\n\nX = 1\nG = 0\nY = 2\n' > "$D/src/tool.py"
( cd "$D" && git add src/tool.py && git commit -q -m "tool" )
sed -i '' '4s/.*/S = """/' "$D/src/tool.py"        # theirs: a string opened at line 4
snap
sed -i '' '6s/.*/"""/' "$D/src/tool.py"           # ours: closed at line 6 — one untouched line between, two hunks
sed -i '' 's/- \[ \] `src/- [x] `src/' "$D/prds/finished/specs/spec01.md"
python3 -m py_compile "$D/src/tool.py" 2> /dev/null; RC=$?
eq  "E the working tree parses" "$RC" "0"
OUT="$(run finished)"; RC=$?
eq  "E exit 1 — our closing quote without their opening one is a syntax error at HEAD" "$RC" "1"
has "E the refusal names the parser's line" "$OUT" "src/tool.py: the staged blob does not parse"
lacks "E the parser's path is the repo path, not the scratch file's" "$OUT" "/private"
has "E the parser's line is quoted" "$OUT" 'src/tool.py", line 6' 
eq  "E nothing committed" "$( cd "$D" && git rev-list --count HEAD )" "2"
eq  "E the index is HEAD again" "$( cd "$D" && git diff --cached --stat | wc -l | tr -d ' ' )" "0"

# ── F. the dry run still says by hunk ────────────────────────────────────────
echo "F. dry"
fixture f; foreign_above; snap; work
OUT="$(run finished --dry)"; RC=$?
eq  "F exit 0" "$RC" "0"
has "F by hunk named" "$OUT" "by hunk:   src/view.js"
eq  "F nothing staged" "$( cd "$D" && git diff --cached --stat | wc -l | tr -d ' ' )" "0"
# ── G. the worker's hunk is a deletion, under a foreign block ────────────────
echo "G. a kept deletion"
fixture g; foreign_above; snap
sed -i '' '/if (r.ok) cb(r);/d' "$D/src/view.js"    # ours: -10,1 +13,0 — the callback's body goes
sed -i '' 's/- \[ \] `src/- [x] `src/' "$D/prds/finished/specs/spec01.md"
OUT="$(run finished)"; RC=$?
eq  "G exit 0" "$RC" "0"
lacks "G the callback's line is gone from HEAD" "$( cd "$D" && git show HEAD:src/view.js )" 'if (r.ok) cb(r);'
lacks "G the foreign block is not in HEAD" "$( cd "$D" && git show HEAD:src/view.js )" "drawNames"
eq  "G HEAD is the original minus one line" "$( cd "$D" && git show HEAD:src/view.js | wc -l | tr -d ' ' )" "11"
eq  "G line 10 of HEAD closes the callback" "$( cd "$D" && git show HEAD:src/view.js | sed -n '10p' )" "  });"
OUT="$( cd "$D" && python3 - "$COLLECT" <<'EOF2'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("collect", sys.argv[1])
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
kept = ["@@ -10 +13,0 @@\n-    if (r.ok) cb(r);\n"]
foreign = ["@@ -3,0 +4,4 @@\n+function drawNames() {\n+  // the names column\n+  return 1;\n+}\n"]
undone = open("src/view.js").read().replace("function drawNames() {\n  // the names column\n  return 1;\n}\n", "")
L = undone.splitlines(True); L.insert(9, "    if (r.ok) cb(r);\n")
print("undone:", c.misplaced("".join(L), kept, foreign, 15))
EOF2
)"
has "G the check sees a kept deletion that did not happen" "$OUT" "hunk @@ +13,0: its removed lines still sit after line 9 of the staged blob"

echo "$((PASS + FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" = 0 ]
