#!/usr/bin/env bash
# too-big-splits-itself — the probe's harness. Runs against a copy of the
# example board in a temp dir; one line per assertion, a count at the end.
set -u
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
pearde() { python3 "$ROOT/resources/pearde.py" "$@"; }
export PEARDE_AS=engineer
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "  ok   $1"; }
bad() { FAIL=$((FAIL+1)); echo "  FAIL $1"; }
has() { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1 — missing: $3"; fi; }
not() { if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1 — present: $3"; else ok "$1"; fi; }
eq()  { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 — got: $2 · want: $3"; fi; }
doc() { if grep -qF -- "$3" "$ROOT/$2"; then ok "$1"; else bad "$1 — $2 lacks: $3"; fi; }

python3 "$ROOT/resources/board/plan.py" example "$D/ex" >/dev/null || { echo "no example board"; exit 1; }
B="$D/ex/prds"
spec() { # spec <dir> <nn> <complexity>
  printf -- '---\ncomplexity: %s\nfootprint:\n  - src/a.py\n---\n# spec%s — a unit\n\n## Acceptance\n\n- [ ] it runs\n\n## Verify and Proof\n\n```sh\npython3 src/a.py\n```\n' "$3" "$2" > "$1/spec$2.md"
}

echo "── the two keys are documented"
doc "settings.md has split-above at 40" references/settings.md '| `split-above` | 40 '
doc "settings.md has specs-above at 6"  references/settings.md '| `specs-above` | 6 '
doc "the analyst block carries <split_above>" references/parts/workers.md '> A build whose specs would sum `complexity` above `<split_above>` or count'
doc "the analyst block carries <specs_above>"  references/parts/workers.md '> above `<specs_above>` returns REFINE with a `## Split` table, never'
doc "the table names <split_above>" references/parts/workers.md '| `<split_above>` |'
doc "the table names <specs_above>" references/parts/workers.md '| `<specs_above>` |'
doc "the prd template names the limit" references/templates/prd.md 'above `split-above`'
doc "the prd template says where a split lands" references/templates/prd.md 'under `## Children`'
eq "brief --check is silent" "$(python3 "$ROOT/resources/board/brief.py" --check 2>&1)" ""

echo "── the brief carries the numbers, from the copy's settings.md"
OUT=$(pearde brief big/second --board "$B" 2>&1); eq "brief big/second exits 0" "$?" 0
has "default split-above in the brief" "$OUT" 'above `40` or count'
has "default specs-above in the brief"  "$OUT" 'above `6` returns REFINE'
not "no unfilled <split_above>" "$OUT" '<split_above>'
not "no unfilled <specs_above>" "$OUT" '<specs_above>'
pearde settings split-above=50 --board "$B" >/dev/null; pearde settings specs-above=3 --board "$B" >/dev/null
OUT=$(pearde brief big/second --board "$B" 2>&1)
has "changed split-above changes the brief" "$OUT" 'above `50` or count'
has "changed specs-above changes the brief"  "$OUT" 'above `3` returns REFINE'
pearde settings split-above=40 --board "$B" >/dev/null; pearde settings specs-above=6 --board "$B" >/dev/null
LIM=$(cd "$ROOT/resources/board" && python3 -c "import specs; print(specs.limits('$B'))")
eq "limits() reads both keys" "$LIM" "{'split-above': 40, 'specs-above': 6}"
pearde settings split-above=many --board "$B" >/dev/null
LIM=$(cd "$ROOT/resources/board" && python3 -c "import specs; print(specs.limits('$B'))")
eq "a value that is not an integer reads at the default" "$LIM" "{'split-above': 40, 'specs-above': 6}"
pearde settings split-above=40 --board "$B" >/dev/null

echo "── specced refuses a set over either limit"
S="$B/big/second/specs"; mkdir -p "$S"
sed -i '' 's/^state: open/state: analyzing/' "$B/big/second/prd.md"
for i in 1 2 3 4 5 6 7; do spec "$S" "0$i" 10; done
ERR=$(pearde specced big/second --blast low --board "$B" 2>&1 >/dev/null); RC=$?
eq "seven specs of 10: exit 1" "$RC" 1
has "names specs-above" "$ERR" "over specs-above: 7 > 6 — REFINE it"
has "and split-above, both over" "$ERR" "over split-above: 70 > 40 — REFINE it"
eq "the PRD did not move" "$(grep -c '^state: analyzing' "$B/big/second/prd.md")" 1
ERR=$(pearde specced big/second --check --board "$B" 2>&1 >/dev/null); RC=$?
eq "--check refuses the same way" "$RC" 1
has "--check names the limit" "$ERR" "over specs-above: 7 > 6"
rm "$S"/*; spec "$S" 01 20; spec "$S" 02 20; spec "$S" 03 18
ERR=$(pearde specced big/second --blast low --board "$B" 2>&1 >/dev/null); RC=$?
eq "three specs summing 58: exit 1" "$RC" 1
has "names split-above" "$ERR" "over split-above: 58 > 40 — REFINE it"
not "and not specs-above" "$ERR" "specs-above"
pearde settings split-above=60 --board "$B" >/dev/null
OUT=$(pearde specced big/second --check --board "$B" 2>&1); RC=$?
eq "the limit is the board's: 58 under 60 passes --check" "$RC" 0
has "--check prints the sum" "$OUT" "complexity 58"
pearde settings split-above=40 --board "$B" >/dev/null
rm "$S"/*; spec "$S" 01 20; spec "$S" 02 20
OUT=$(pearde specced big/second --blast low --board "$B" 2>&1); RC=$?
eq "under both limits: specced lands" "$RC" 0
has "the progress line" "$OUT" "big/second: analyzing → specced"
sed -i '' 's/^state: specced/state: analyzing/' "$B/big/second/prd.md"
rm "$S"/*; spec "$S" 01 20; spec "$S" 02 20; spec "$S" 03 18

echo "── the split is a command: refine lands ## Children and scan gates the parent"
OUT=$(printf '## Split\n\n| child | contract | needs |\n|---|---|---|\n| left | the left half | — |\n| right | the right half | left |\n' | pearde refine big/second --board "$B" 2>&1); RC=$?
eq "refine exits 0" "$RC" 0
has "left is open" "$OUT" "big/second/left: open"
has "right needs left" "$OUT" "big/second/right: open · needs left"
has "the parent went analyzing → open" "$OUT" "big/second: analyzing → open"
eq "left/prd.md exists" "$(test -f "$B/big/second/left/prd.md" && echo y)" y
eq "right/prd.md exists" "$(test -f "$B/big/second/right/prd.md" && echo y)" y
eq "parent is open" "$(grep -c '^state: open' "$B/big/second/prd.md")" 1
eq "parent carries ## Children once" "$(grep -c '^## Children' "$B/big/second/prd.md")" 1
has "the row for left"  "$(sed -n '/^## Children/,$p' "$B/big/second/prd.md")" '| `left` | the left half | — |'
has "the row for right" "$(sed -n '/^## Children/,$p' "$B/big/second/prd.md")" '| `right` | the right half | left |'
has "the contract above it is untouched" "$(cat "$B/big/second/prd.md")" "# second — the child still open"
SCAN=$(pearde scan --board "$B" 2>&1)
has "scan gates the parent on its children" "$SCAN" "big/second · p62 · w0 · boxes 0/3 · needs right,left"
has "scan lists left as open" "$SCAN" "open      · big/second/left"
ERR=$(pearde brief big/second --board "$B" 2>&1 >/dev/null); RC=$?
eq "the parent is not dispatchable" "$RC" 1
has "brief names the children" "$ERR" "leaf: big/second has children not done"

echo "── depth is unbounded: a child over the limit is REFINEd in its turn"
L="$B/big/second/left"; mkdir -p "$L/specs"
sed -i '' 's/^state: open/state: analyzing/' "$L/prd.md"
for i in 1 2 3 4 5 6 7; do spec "$L/specs" "0$i" 1; done
ERR=$(pearde specced big/second/left --blast low --board "$B" 2>&1 >/dev/null); RC=$?
eq "the child is refused" "$RC" 1
has "on specs-above" "$ERR" "over specs-above: 7 > 6 — REFINE it"
rm -r "$L/specs"
OUT=$(printf '## Split\n\n| child | contract | needs |\n|---|---|---|\n| deeper | one more level | — |\n' | pearde refine big/second/left --board "$B" 2>&1); RC=$?
eq "the child splits again" "$RC" 0
eq "grandchild exists" "$(test -f "$L/deeper/prd.md" && echo y)" y
has "the child carries ## Children" "$(cat "$L/prd.md")" '| `deeper` | one more level | — |'

echo "── add says big and gates nothing"
OUT=$(python3 -c "print('\n'.join('line %d' % i for i in range(70)))" | pearde add a big one --body - --board "$B" 2>&1); RC=$?
eq "a 70-line body: exit 0" "$RC" 0
eq "first line is the warning" "$(printf '%s\n' "$OUT" | sed -n 1p)" "big — expect a split"
has "and the PRD is created" "$OUT" "a-big-one: — → open"
eq "created open" "$(grep -c '^state: open' "$B/a-big-one/prd.md")" 1
OUT=$(printf 'When this is done, x.\n\nWhen this is done, y.\n' | pearde add two contracts --body - --board "$B" 2>&1); RC=$?
eq "two When-this-is-done: exit 0" "$RC" 0
eq "first line is the warning" "$(printf '%s\n' "$OUT" | sed -n 1p)" "big — expect a split"
OUT=$(python3 -c "print('\n'.join('line %d' % i for i in range(60)))" | pearde add sixty --body - --board "$B" 2>&1)
not "60 lines is not over 60" "$OUT" "big — expect a split"
OUT=$(printf 'When this is done, z.\n' | pearde add small --body - --board "$B" 2>&1)
not "a small body says nothing" "$OUT" "big — expect a split"
eq "small created open" "$(grep -c '^state: open' "$B/small/prd.md")" 1

echo
echo "verify: $PASS/$((PASS+FAIL)) checks pass"
[ "$FAIL" -eq 0 ]
