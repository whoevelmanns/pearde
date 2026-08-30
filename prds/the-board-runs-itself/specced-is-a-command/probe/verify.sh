#!/usr/bin/env bash
# specced-is-a-command — the harness. Copies the example board to a temp dir
# (never under prds/, never run in place), adds the PRDs the checks need, and
# drives specs.py against it. One line per assertion, a count at the end.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
SPECS="${SPECS_PY:-$ROOT/resources/board/specs.py}"
PLAN="$ROOT/resources/board/plan.py"
TR="$ROOT/resources/board/transitions.py"
EX="$ROOT/resources/board/example/prds"
D="$(mktemp -d)"; trap 'rm -rf "$D"' EXIT
B="$D/prds"
export PEARDE_AS=engineer                # the persona term, as every transition takes it
pass=0; fail=0
ok()  { pass=$((pass+1)); echo "  ok   $1"; }
bad() { fail=$((fail+1)); echo "  FAIL $1"; }
check() { if eval "$2"; then ok "$1"; else bad "$1"; fi; }
tree_sum() { (cd "$B" && find . -type f -not -name '.*.jsonl' | sort | while read -r f; do cat "$f"; printf '\0%s\0' "$f"; done | cksum); }
HF="$B/$(python3 -c "import sys; sys.path.insert(0,'$ROOT/resources/board'); import transitions as t; print(getattr(t,'TRANSITIONS_FILE',None) or getattr(t,'HISTORY_FILE'))")"
hist() { if [ -f "$HF" ]; then wc -l < "$HF" | tr -d ' '; else echo 0; fi; }
run() { python3 "$SPECS" "$@" --board "$B"; }
force() { python3 "$TR" set "$1" "$2" --force --board "$B" >/dev/null; }

[ -d "$EX" ] || { echo "no example board at $EX"; exit 1; }
[ -f "$TR" ] || { echo "no transitions.py at $TR — specs.py imports it"; exit 1; }
cp -R "$EX" "$B"

# ── the PRDs the checks add to the copy ──────────────────────────────────────
prd() { # dir state [extra-frontmatter-lines]
  mkdir -p "$B/$1"
  printf -- '---\nstate: %s\norigin: requested\npriority: 50\ncomplexity: 0\nblast-radius:\nrepo: example\n%s---\n\n# %s — a fixture\n\nWhat exists when it is done.\n' "$2" "${3:-}" "$1" > "$B/$1/prd.md"
}
spec() { # dir file complexity footprint-lines acceptance verify-block [fm-extra]
  mkdir -p "$B/$1/specs"
  printf -- '---\ncomplexity: %s\n%s%s---\n\n# %s — a unit\n\n## Acceptance\n\n%s\n\n## Verify and Proof\n\n%s\n' "$3" "$4" "${7:-}" "$2" "$5" "$6" > "$B/$1/specs/$2"
}
FP=$'footprint:\n  - src/a.py\n'
VER=$'```sh\npython3 -m pytest src/a.py\n```'
BOX='- [ ] `a.py` prints one line'
WF="$(ls "$B/workflows" | while read -r f; do grep -l '^workflow:' "$B/workflows/$f" >/dev/null && echo "${f%.md}"; done | head -1)"
AT="$(ls "$B/workflows" | while read -r f; do grep -l '^atomic:' "$B/workflows/$f" >/dev/null && echo "${f%.md}"; done | head -1)"
check "the example board has a workflow and an atomic" "[ -n '$WF' ] && [ -n '$AT' ]"

spec landed spec01.md 4 "$FP" "- [x] landed" "$VER"
prd msg analyzing
spec msg spec01.md 4 "$FP" $'- [ ] the test passes\n- [ ] write the commit message from the template' "$VER"
prd gitc analyzing
spec gitc spec01.md 4 "$FP" $'- [ ] `git commit -m "done"` succeeds' "$VER"
prd prose analyzing
spec prose spec01.md 4 "$FP" $'- [ ] `commit:` on prd.md names the landed sha\n- [ ] the committed harnesses still print 47/47\n- [ ] `commits.md` says the changed files ride the PRD\'s commit' "$VER"
prd smell analyzing
spec smell spec01.md 3 "$FP" "$BOX" $'```sh\nmake test\n```'
prd ticked analyzing
spec ticked spec01.md 3 "$FP" $'- [x] already ticked\n- [ ] open' "$VER"
prd nofoot analyzing $'footprint:\n  - src\n'
spec nofoot spec01.md 3 "" "$BOX" $'```sh\npython3 -m pytest src\n```'

SPLIT=$'Some prose.\n\n## Split\n\n| child | contract | needs |\n|---|---|---|\n| `one` | the first thing exists | — |\n| two | the second thing exists | one |\n| three | the third thing exists | one, two |\n'

# ── specced: refusals ────────────────────────────────────────────────────────
echo "specced — refusals"
force big/second analyzing
check "big/second is analyzing (forced)"          "grep -q '^state: analyzing' $B/big/second/prd.md"
spec big/second spec01.md 8 "$FP" $'- [ ] the test passes\n- [ ] commit the change' "$VER"
prd weird analyzing
spec weird spec01.md 0 "$FP" "$BOX" "$VER"
spec weird spec02.md 8 "$FP" "" ""                       # no box, no sh block
spec weird spec03.md 8 "$FP" "$BOX" "$VER" $'workflow: nope\n'
spec weird spec04.md 8 "$FP" "$BOX" "$VER" "workflow: $AT"$'\n'
spec weird spec05.md x "$FP" "$BOX" "$VER"
S0=$(tree_sum)
ERR=$(run specced big/second 2>&1 >/dev/null); rc=$?
check "commit the change → exit 1"                "[ $rc = 1 ]"
check "…naming file and line"                     "grep -q 'big/second/specs/spec01.md:12: a box asks the worker to commit' <<<\"\$ERR\""
check "…nothing written"                          "[ \"\$(tree_sum)\" = \"$S0\" ]"
ERR=$(run specced msg 2>&1 >/dev/null); rc=$?
check "commit message → exit 1"                   "[ $rc = 1 ] && grep -q 'msg/specs/spec01.md:12: a box asks' <<<\"\$ERR\""
ERR=$(run specced gitc 2>&1 >/dev/null); rc=$?
check "git commit → exit 1"                       "[ $rc = 1 ] && grep -q 'gitc/specs/spec01.md:11: a box asks' <<<\"\$ERR\""
OUT=$(run specced prose --check 2>&1); rc=$?
check "a box checking commit: passes the gate"    "[ $rc = 0 ] && grep -q 'prose: ok · complexity 4' <<<\"\$OUT\""
ERR=$(run specced next 2>&1 >/dev/null); rc=$?
check "no specs/ → exit 1 naming specs/"          "[ $rc = 1 ] && grep -q 'next/specs/: no spec file' <<<\"\$ERR\""
ERR=$(run specced weird 2>&1 >/dev/null); rc=$?
check "the weird set → exit 1"                    "[ $rc = 1 ]"
check "complexity 0 outside 1-100, line 2"        "grep -q 'spec01.md:2: complexity 0 outside 1-100' <<<\"\$ERR\""
check "acceptance holds no box, at its heading"   "grep -q 'spec02.md:9: .## Acceptance. holds no box' <<<\"\$ERR\""
check "verify holds no sh block, at its heading"  "grep -q 'spec02.md:13: .## Verify and Proof. holds no fenced' <<<\"\$ERR\""
check "workflow naming nothing, at its line"      "grep -q 'spec03.md:5: workflow .nope. names no workflow' <<<\"\$ERR\""
check "workflow naming an atomic"                 "grep -q \"spec04.md:5: workflow .$AT. names an atomic\" <<<\"\$ERR\""
check "complexity not an integer"                 "grep -q 'spec05.md:2: complexity .x. is not an integer' <<<\"\$ERR\""
check "…one line per refusal, six"                "[ \$(grep -c 'specs/spec0' <<<\"\$ERR\") = 6 ]"
check "…nothing written"                          "[ \"\$(tree_sum)\" = \"$S0\" ]"
# `weird` leaves here: plan.py's `spec_data` does float() on a spec's
# complexity, so `x` crashes every scan and progress line after it (a finding
# on plan.py, outside this footprint), and `workflows.py check` reports the
# dangling `workflow:` — both by design, neither this harness's.
rm -rf "$B/weird"; S0=$(tree_sum)
ERR=$(run specced landed 2>&1 >/dev/null); rc=$?
check "a done PRD → exit 1 naming the state"      "[ $rc = 1 ] && grep -q 'landed is .done.' <<<\"\$ERR\""
ERR=$(run specced big/second --blast huge 2>&1 >/dev/null); rc=$?
check "--blast huge → exit 1"                     "[ $rc = 1 ] && grep -q 'high|mid|low' <<<\"\$ERR\""
ERR=$(run specced big/second --workflow nope 2>&1 >/dev/null); rc=$?
check "--workflow nope → exit 1"                  "[ $rc = 1 ] && grep -q 'names no workflow' <<<\"\$ERR\""
ERR=$(run specced nosuch 2>&1 >/dev/null); rc=$?
check "no such PRD → exit 1"                      "[ $rc = 1 ] && grep -q 'no PRD named .nosuch.' <<<\"\$ERR\""
ERR=$(run specced 2>&1 >/dev/null); rc=$?
check "no PRD named → exit 1"                     "[ $rc = 1 ] && grep -q 'which PRD' <<<\"\$ERR\""
ERR=$(PEARDE_AS= run specced big/second 2>&1 >/dev/null); rc=$?
check "no persona → exit 1 naming --as"           "[ $rc = 1 ] && grep -q 'persona: .--as <id>. or PEARDE_AS' <<<\"\$ERR\""
check "…still nothing written"                    "[ \"\$(tree_sum)\" = \"$S0\" ]"

# ── specced: --check and success ─────────────────────────────────────────────
echo "specced — check and success"
spec big/second spec01.md 8 "$FP" "$BOX" "$VER"
spec big/second spec02.md 12 "$FP" "$BOX" "$VER"
S0=$(tree_sum)
OUT=$(run specced big/second --check 2>&1); rc=$?
check "--check exits 0 and prints the sum"        "[ $rc = 0 ] && grep -q 'big/second: ok · complexity 20 · footprint src/a.py' <<<\"\$OUT\""
check "…writes nothing"                           "[ \"\$(tree_sum)\" = \"$S0\" ]"
H0=$(hist)
OUT=$(run specced big/second --blast mid --workflow "$WF" 2>/dev/null); rc=$?
check "big/second with 8 and 12 → exit 0"         "[ $rc = 0 ]"
check "…one progress line"                        "[ \$(wc -l <<<\"\$OUT\") = 1 ]"
check "…▸ big/second: analyzing → specced"        "grep -q '^▸ big/second: analyzing → specced · done' <<<\"\$OUT\""
check "…as engineer last"                         "grep -q ' · as engineer\$' <<<\"\$OUT\""
check "…ready/blocked/workers terms"              "grep -q ' · ready [0-9]* · blocked [0-9]*.* @1 workers' <<<\"\$OUT\""
check "state: specced"                            "grep -q '^state: specced' $B/big/second/prd.md"
check "complexity: 20"                            "grep -q '^complexity: 20' $B/big/second/prd.md"
check "blast-radius: mid"                         "grep -q '^blast-radius: mid' $B/big/second/prd.md"
check "workflow: set from --workflow"             "grep -q \"^workflow: $WF\" $B/big/second/prd.md"
check "claim: cleared"                            "! grep -q '^claim:' $B/big/second/prd.md"
check "the title and body untouched"              "grep -q '^# second — the child still open' $B/big/second/prd.md"
check "the transitions log gained one row"        "[ \$(hist) = \$((H0+1)) ] && tail -1 $HF | grep -q '\"from\": \"analyzing\".*\"prd\": \"big/second\".*\"to\": \"specced\"'"
check "scan agrees: specced big/second w20"       "python3 $PLAN scan $B | grep -q '^  specced *· big/second · p62 · w20 · wf $WF · boxes 0/2'"
ERR=$(run specced big/second 2>&1 >/dev/null); rc=$?
check "specced again → exit 1 naming the state"   "[ $rc = 1 ] && grep -q 'big/second is .specced.' <<<\"\$ERR\""
spec next spec01.md 5 "$FP" "$BOX" "$VER"
ERR=$(run specced next 2>&1 >/dev/null); rc=$?
check "next (still open) → exit 1 naming open"    "[ $rc = 1 ] && grep -q 'next is .open. — .specced. is set from .analyzing.' <<<\"\$ERR\""
check "…and next is still open"                   "grep -q '^state: open' $B/next/prd.md"
OUT=$(run specced smell 2>"$D/err"); rc=$?
check "the smell → exit 0, specced"               "[ $rc = 0 ] && grep -q '^state: specced' $B/smell/prd.md"
check "…warns on stderr, names the smell"         "grep -q 'warn: spec01.md:13: the verify block names no path under the footprint' $D/err"
OUT=$(run specced ticked 2>"$D/err"); rc=$?
check "a pre-ticked box → exit 0 with a warning"  "[ $rc = 0 ] && grep -q 'warn: spec01.md:9: 1 of 2 boxes already ticked' $D/err"
OUT=$(run specced nofoot --as designer 2>"$D/err"); rc=$?
check "no footprint → warned, the PRD's own stands" "[ $rc = 0 ] && grep -q 'warn: spec01.md:1: no footprint — the PRD.s own stands' $D/err && ! grep -q 'whole-workspace' $D/err"
check "…as designer on the line"                  "grep -q '^▸ nofoot: analyzing → specced .* · as designer\$' <<<\"\$OUT\""
OUT=$(run specced nofoot --check 2>&1)
check "--check runs on a specced PRD (the memo)"  "grep -q 'nofoot: ok · complexity 3 · footprint src' <<<\"\$OUT\""
printf -- '---\nstate: analyzing\nworkflow: %s\n---\n\n# w\n' "$WF" > "$B/prose/prd.md"
run specced prose --workflow none >/dev/null 2>&1
check "--workflow none removes the key"           "! grep -q '^workflow:' $B/prose/prd.md && grep -q '^state: specced' $B/prose/prd.md"

# ── refine ───────────────────────────────────────────────────────────────────
echo "refine"
force next refine
rm -rf "$B/next/specs"
S1=$(tree_sum)
ERR=$(printf '%s' "$SPLIT" | run refine landed 2>&1 >/dev/null); rc=$?
check "a done parent → exit 1 naming the state"   "[ $rc = 1 ] && grep -q 'landed is .done.' <<<\"\$ERR\""
ERR=$(printf 'no table here\n' | run refine next 2>&1 >/dev/null); rc=$?
check "no ## Split → exit 1"                      "[ $rc = 1 ] && grep -q 'no .## Split. table' <<<\"\$ERR\""
ERR=$(printf '## Split\n\n| child | contract | needs |\n|---|---|---|\n' | run refine next 2>&1 >/dev/null); rc=$?
check "an empty table → exit 1"                   "[ $rc = 1 ] && grep -q 'table is empty' <<<\"\$ERR\""
ERR=$(printf '## Split\n\n| child | contract | needs |\n|---|---|---|\n| a | x | zz |\n' | run refine next 2>&1 >/dev/null); rc=$?
check "needs naming no sibling → exit 1"          "[ $rc = 1 ] && grep -q 'child .a. needs .zz., which is no sibling' <<<\"\$ERR\""
ERR=$(printf '## Split\n\n| child | contract | needs |\n|---|---|---|\n| Bad Name | x | — |\n' | run refine next 2>&1 >/dev/null); rc=$?
check "a child that is no directory name → exit 1" "[ $rc = 1 ] && grep -q 'not a directory name' <<<\"\$ERR\""
ERR=$(printf '## Split\n\n| child | contract | needs |\n|---|---|---|\n| a | x | — |\n| a | y | — |\n' | run refine next 2>&1 >/dev/null); rc=$?
check "a child named twice → exit 1"              "[ $rc = 1 ] && grep -q 'named twice' <<<\"\$ERR\""
check "…nothing written by any refusal"           "[ \"\$(tree_sum)\" = \"$S1\" ]"
H0=$(hist)
OUT=$(printf '%s' "$SPLIT" | run refine next 2>"$D/err"); rc=$?
check "three rows → exit 0"                       "[ $rc = 0 ]"
check "three directories"                         "[ -f $B/next/one/prd.md ] && [ -f $B/next/two/prd.md ] && [ -f $B/next/three/prd.md ]"
check "one line per child, then the progress line" "[ \$(wc -l <<<\"\$OUT\") = 4 ] && grep -q '^next/one: open\$' <<<\"\$OUT\" && grep -q '^next/three: open · needs one, two\$' <<<\"\$OUT\""
check "▸ next: refine → open"                     "grep -q '^▸ next: refine → open · ' <<<\"\$OUT\""
check "child: open, origin and priority inherited" "grep -q '^state: open' $B/next/two/prd.md && grep -q '^origin: requested' $B/next/two/prd.md && grep -q '^priority: 58' $B/next/two/prd.md"
check "child: no repo or workflow when the parent has none" "! grep -q '^repo: *[^ #]' $B/next/two/prd.md && ! grep -q '^workflow: *[^ #]' $B/next/two/prd.md"
check "child: needs as given"                     "grep -q '^needs:' $B/next/three/prd.md && grep -q '^  - one' $B/next/three/prd.md && grep -q '^  - two' $B/next/three/prd.md"
check "child with no needs carries no needs:"     "! grep -q '^needs:' $B/next/one/prd.md"
check "child: the title"                          "grep -q '^# two — the second thing exists' $B/next/two/prd.md"
check "child: the contract is the first paragraph" "[ \"\$(awk '/^# two /{f=1;next} f && NF {print; exit}' $B/next/two/prd.md)\" = 'the second thing exists' ]"
check "child: no template placeholder left"       "! grep -q '<The request' $B/next/two/prd.md && ! grep -q '<Title' $B/next/two/prd.md"
check "parent: open, claim cleared, body kept"    "grep -q '^state: open' $B/next/prd.md && ! grep -q '^claim:' $B/next/prd.md && grep -q '^# next — one PRD gated on another' $B/next/prd.md"
check "parent: ## Children with the three rows"   "grep -q '^## Children' $B/next/prd.md && grep -q '^| child | contract | needs |' $B/next/prd.md && [ \$(grep -c '^| .*| the .* thing exists |' $B/next/prd.md) = 3 ]"
check "parent: needs: building kept"              "grep -q '^  - building' $B/next/prd.md"
check "the transitions log gained the parent's row" "[ \$(hist) = \$((H0+1)) ] && tail -1 $HF | grep -q '\"from\": \"refine\".*\"prd\": \"next\".*\"to\": \"open\"'"
SCAN="$(python3 $PLAN scan $B 2>/dev/null)"
check "scan: parent gated on all three"           "grep '^  open *· next · ' <<<\"\$SCAN\" | grep 'needs ' | grep -q 'one' && grep '^  open *· next · ' <<<\"\$SCAN\" | grep -q 'two' && grep '^  open *· next · ' <<<\"\$SCAN\" | grep -q 'three'"
check "scan: children open, three needs one,two"  "grep -q '^  open *· next/three · .*needs one,two' <<<\"\$SCAN\""
check "workflows.py check stays silent"           "[ -z \"\$(python3 $ROOT/resources/workflows.py check $B)\" ]"
S2=$(tree_sum)
ERR=$(printf '%s' "$SPLIT" | run refine next 2>&1 >/dev/null); rc=$?
check "the same table again → exit 1"             "[ $rc = 1 ]"
check "…naming the three existing children"       "grep -q '3 child(ren) already exist, left as they are: one, two, three' <<<\"\$ERR\""
check "…tree unchanged"                           "[ \"\$(tree_sum)\" = \"$S2\" ]"
OUT=$(printf '## Split\n\n| child | contract | needs |\n|---|---|---|\n| one | again | — |\n| four | a fourth | one |\n' | run refine next 2>"$D/err"); rc=$?
check "a second split: the new row lands"         "[ -f $B/next/four/prd.md ] && grep -q '^  - one' $B/next/four/prd.md"
check "…the old row is refused by name, exit 1"   "[ $rc = 1 ] && grep -q 'left as they are: one' $D/err"
check "…the old child is untouched"               "grep -q '^# one — the first thing exists' $B/next/one/prd.md"
check "…## Children gained one row, one header"   "[ \$(grep -c '^| child | contract | needs |' $B/next/prd.md) = 1 ] && grep -q '^| .four. | a fourth | one |' $B/next/prd.md"
check "…an already-open parent prints no transition" "! grep -q '^▸' <<<\"\$OUT\""
OUT=$(printf '## Split\n\n| child | contract | needs |\n|---|---|---|\n| kid | asked and split | — |\n' | run refine asking 2>/dev/null); rc=$?
check "a question PRD can be split"               "[ $rc = 0 ] && grep -q '^▸ asking: question → open' <<<\"\$OUT\""
printf -- '---\nstate: refine\norigin: derived\nfrom: landed\npriority: 7\nrepo: example\nworkflow: %s\n---\n\n# p\n' "$WF" > "$B/smell/prd.md"
OUT=$(printf '## Split\n\n| child | contract | needs |\n|---|---|---|\n| kid | inherits | — |\n' | run refine smell 2>/dev/null); rc=$?
check "child inherits origin, from, repo, workflow" "[ $rc = 0 ] && grep -q '^origin: derived' $B/smell/kid/prd.md && grep -q '^from: landed' $B/smell/kid/prd.md && grep -q '^repo: example' $B/smell/kid/prd.md && grep -q \"^workflow: $WF\" $B/smell/kid/prd.md && grep -q '^priority: 7' $B/smell/kid/prd.md"

# ── the module's surface ─────────────────────────────────────────────────────
echo "surface"
check "COMMANDS exposes specced and refine"       "python3 -c \"import sys; sys.path.insert(0,'$(dirname "$SPECS")'); import specs; assert set(specs.COMMANDS)=={'specced','refine'}; assert all(c.__doc__ for c in specs.COMMANDS.values())\""
check "no command → usage, exit 2"                "python3 $SPECS >/dev/null 2>&1; [ \$? = 2 ]"
check "no fixture prd.md under the real board"    "! find $ROOT/prds -path '*/probe/*' -name prd.md | grep -q ."
check "the example board is untouched"            "[ -z \"\$(cd $ROOT && git status --porcelain resources/board/example)\" ] || [ -z \"\$(cd $ROOT && git diff --stat resources/board/example)\" ]"
check "stdlib only"                               "! grep -E '^(import|from) ' $SPECS | grep -vE '^(import|from) (os|re|sys|edit|plan|transitions|workflows)\b' | grep -q ."

echo
echo "verify: $pass/$((pass+fail)) checks pass"
[ $fail = 0 ]
