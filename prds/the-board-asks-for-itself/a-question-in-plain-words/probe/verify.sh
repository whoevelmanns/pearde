#!/usr/bin/env bash
# "## Done when", as a harness. Builds its fixture board in a directory made at
# run time — never under prds/, where a dir holding prd.md is a PRD — and
# tears it down. Exit 0 when every line of the contract holds.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
DIR="$(mktemp -d)"; trap 'rm -rf "$DIR"' EXIT
fail=0
say() { printf '%s %s\n' "$1" "$2"; }
ok()  { say "ok  " "$1"; }
no()  { say "FAIL" "$1"; fail=1; }

bash "$HERE/fixture.sh" "$DIR" > "$DIR/out.txt" 2>&1
lines=$(grep -c '^a-fork: question' "$DIR/out.txt")

# 1 — five questions in, four lines out, each naming what it caught
[ "$lines" = "4" ] && ok "the checker reports exactly four lines" \
  || no "the checker reports $lines lines, want 4"
for want in "names a PRD" "says \`specced\`" "names a file" "over 60"; do
  grep -q -- "$want" "$DIR/out.txt" \
    && ok "it names the catch: $want" || no "no line says: $want"
done
grep -q 'question 1 ' "$DIR/out.txt" \
  && no "the clean question was reported" || ok "the clean question passes"
grep -q 'for the board:' "$DIR/out.txt" \
  && no "the technical anchor was checked" || ok "the anchor is never checked"

# 2 — release refuses the round and leaves the state alone
sed -i.bak 's/^state: question/state: analyzing/' "$DIR/prds/a-fork/prd.md"
python3 "$REPO/resources/board/transitions.py" release a-fork question \
  --board "$DIR/prds" --as engineer > "$DIR/rel.txt" 2>&1
rc=$?
[ "$rc" != "0" ] && ok "release <prd> question exits $rc" \
  || no "release <prd> question exited 0 on a round that fails"
grep -q '^state: analyzing' "$DIR/prds/a-fork/prd.md" \
  && ok "the state is unchanged" || no "the state moved"

# 3 — the view's asks card
node "$HERE/viewprobe.js" > "$DIR/view.txt" 2>&1 \
  && ok "the asks card shows no anchor and says: or write your own" \
  || { no "viewprobe"; cat "$DIR/view.txt"; }

# 4 — every round already on the real board still passes
python3 "$REPO/resources/questions.py" check "$REPO" > "$DIR/board.txt" 2>&1 \
  && ok "every round on this board passes" \
  || { no "a round on this board fails"; cat "$DIR/board.txt"; }

[ "$fail" -eq 0 ]
