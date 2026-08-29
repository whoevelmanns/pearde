#!/usr/bin/env bash
# one-predicate-for-dispatchable — the probe harness.
# `scan`'s ready band and `claim`'s gate read one function, `plan.dispatchable`;
# a parked child holds its parent; a container is collect's, never claim's.
# Every fixture is a copy of the example board under mktemp -d, removed at exit.
set -u
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SRC="$ROOT/resources/board"; PLAN="$SRC/plan.py"; TR="$SRC/transitions.py"
BRIEF="$SRC/brief.py"
PASS=0; FAIL=0
ok()    { PASS=$((PASS+1)); echo "  ok   $1"; }
bad()   { FAIL=$((FAIL+1)); echo "  FAIL $1"; }
has()   { if printf '%s\n' "$2" | grep -F -- "$3" >/dev/null; then ok "$1"; else bad "$1 — want [$3]"; fi; }
lacks() { if printf '%s\n' "$2" | grep -F -- "$3" >/dev/null; then bad "$1 — has [$3]"; else ok "$1"; fi; }
eq()    { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 — want [$3] got [$2]"; fi; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
export PEARDE_AS=engineer

fixture() {   # a fresh copy of the example board, its own git repo; echoes the board path
  local d; d=$(mktemp -d "$TMP/fx.XXXXXX")
  python3 "$PLAN" example "$d/b" >/dev/null 2>&1
  find "$d" -type f -exec touch {} +
  (cd "$d/b" && git init -q . && git add -A \
     && git -c user.email=p@p -c user.name=p commit -qm init)
  echo "$d/b/prds"
}
section() {   # $1 scan text, $2 heading word → that section's rows
  printf '%s\n' "$1" | awk -v h="^$2 " '$0 ~ h {f=1; next} /^$/ {f=0} f'
}
state_of() { sed -n 's/^state: //p' "$1/prd.md" | head -1; }
# every ready row must pass gate_claim; every gated row must be refused with
# the reason its line shows (or be an `after` edge, which is order, not a gate)
gate_check() {
python3 - "$1" "$SRC" <<'PY'
import sys, re, subprocess
board, src = sys.argv[1:3]; sys.path.insert(0, src)
import plan, transitions as tr
out = subprocess.run([sys.executable, src + "/plan.py", "scan", board],
                     capture_output=True, text=True).stdout
sec, rows = None, {"ready": [], "gated": []}
for l in out.splitlines():
    m = re.match(r"^(ready|gated) ", l)
    if m: sec = m.group(1); continue
    if not l.strip(): sec = None; continue
    if sec and l.startswith("  "): rows[sec].append(l)
prds = plan.scan(board); rok = rbad = gok = gbad = 0
for l in rows["ready"]:
    rel = l.split(" · ")[1]
    try: tr.gate_claim(board, prds, prds[rel]); rok += 1
    except tr.Refused as e: rbad += 1; print("ready-but-refused", rel, e)
for l in rows["gated"]:
    rel = l.split(" · ")[1]
    try: tr.gate_claim(board, prds, prds[rel]); why = None
    except tr.Refused as e: why = str(e)
    if why and (why in l or " · needs " in l or " · after " in l): gok += 1
    elif why is None and " · after " in l: gok += 1
    else: gbad += 1; print("gated-mismatch", rel, why, l)
print(f"ready-ok {rok} ready-bad {rbad} gated-ok {gok} gated-bad {gbad}")
PY
}

echo "# source — one predicate, three readers"
eq  "plan.py defines dispatchable once" "$(grep -c '^def dispatchable(' "$PLAN")" 1
has "gate_claim calls plan.dispatchable" "$(cat "$TR")" "planlib.dispatchable(prd, prds, board)"
lacks "the leaf wording left transitions.py" "$(cat "$TR")" "has children not done"
lacks "the footprint wording left transitions.py" "$(cat "$TR")" "is claimed and holds"
has "cmd_scan calls it on the free set" "$(cat "$PLAN")" "why = {x: dispatchable(prds[x], prds, board) for x in free}"
has "compute_plan holds what it refuses" "$(cat "$PLAN")" "why = dispatchable(todo[r], prds, board)"
has "plan_frontier reads the hold" "$(cat "$PLAN")" 'and x not in r["held"]'

echo "# untouched copy — the old shape stands"
B0=$(fixture); S0=$(python3 "$PLAN" scan "$B0" 2>/dev/null)
has "big/second is ready" "$(section "$S0" ready)" "big/second"
has "big is gated on its live child" "$(section "$S0" gated)" "big · p62 · w0 · needs second"
lacks "no leaf reason on the untouched copy" "$S0" "leaf:"
lacks "no container on the untouched copy" "$S0" "container:"
lacks "no unclaimed on the untouched copy" "$S0" "unclaimed:"
eq  "ready ⇒ claim accepts, gated ⇒ the shown reason" "$(gate_check "$B0" | tail -1)" "ready-ok 1 ready-bad 0 gated-ok 2 gated-bad 0"

echo "# big/second parked — the parent is held"
B1=$(fixture); sed -i.bak 's/^state: open$/state: later/' "$B1/big/second/prd.md"; rm -f "$B1/big/second/prd.md.bak"
(cd "$B1" && git -c user.email=p@p -c user.name=p commit -qam park)
S1=$(python3 "$PLAN" scan "$B1" 2>/dev/null)
has "parked line names the child" "$S1" "parked: big/second"
lacks "big is not ready" "$(section "$S1" ready)" "big"
has "big is gated, held by the parked child" "$(section "$S1" gated)" "big · p62 · w14 · leaf: big held by big/second (parked)"
ERR=$(python3 "$TR" claim big w --board "$B1" 2>&1 >/dev/null); RC=$?
eq  "claim big w exits 1" "$RC" 1
has "claim refuses with the same reason" "$ERR" "leaf: big held by big/second (parked)"
eq  "the refusal wrote nothing" "$(cd "$B1" && git status --short)" ""
eq  "big stays open" "$(state_of "$B1/big")" open
eq  "ready ⇒ claim accepts, gated ⇒ the shown reason" "$(gate_check "$B1" | tail -1)" "ready-ok 0 ready-bad 0 gated-ok 2 gated-bad 0"
P1=$(python3 "$PLAN" plan "$B1" 2>/dev/null)
lacks "plan's ready set holds no held PRD" "$(printf '%s\n' "$P1" | awk '/^ready now/{f=1;next} /^$/{f=0} f')" "big ["
has "plan lists big as gates clear, with the reason" "$P1" "big [open] p62"
has "plan names the hold" "$P1" "leaf: big held by big/second (parked)"
has "brief skips it under the leaf word" "$(python3 "$BRIEF" big --board "$B1" 2>&1)" "skipped big — leaf — leaf: big held by big/second (parked)"

echo "# big/second done, big has nothing of its own — a container"
B2=$(fixture); sed -i.bak 's/^state: open$/state: done/' "$B2/big/second/prd.md"; rm -f "$B2/big/second/prd.md.bak"
(cd "$B2" && git -c user.email=p@p -c user.name=p commit -qam land)
S2=$(python3 "$PLAN" scan "$B2" 2>/dev/null)
has "big is listed to collect" "$(section "$S2" collect)" "big · p62"
has "the line says why" "$(section "$S2" collect)" "container: every child done — pearde collect closes it"
lacks "big is not ready" "$(section "$S2" ready)" "big"
lacks "big is not gated" "$(section "$S2" gated)" "big"
ERR=$(python3 "$TR" claim big w --board "$B2" 2>&1 >/dev/null); RC=$?
eq  "claim big w exits 1" "$RC" 1
has "claim refuses: container" "$ERR" "container: every child done — pearde collect closes it"
eq  "big stays open — not the analyzing trap" "$(state_of "$B2/big")" open
eq  "the refusal wrote nothing" "$(cd "$B2" && git status --short)" ""
has "compute_plan holds the container in its collect list" "$(cd "$SRC" && python3 -c "import plan; print(','.join(plan.compute_plan('$B2')['collect']))")" "big"
has "plan lists big to collect off that one list" "$(python3 "$PLAN" plan "$B2" 2>/dev/null)" "✓ big [open]"
has "brief skips it under the collect word" "$(python3 "$BRIEF" big --board "$B2" 2>&1)" "skipped big — collect — container: every child done — pearde collect closes it"

echo "# children all done, but a spec of its own — not a container"
B3=$(fixture); sed -i.bak 's/^state: open$/state: done/' "$B3/big/second/prd.md"; rm -f "$B3/big/second/prd.md.bak"
mkdir -p "$B3/big/specs"
printf -- '---\ncomplexity: 3\nfootprint:\n  - src/big.py\n---\n\n# spec01 — the parent'"'"'s own unit\n\n## Acceptance\n\n- [ ] src/big.py exists\n\n## Verify and Proof\n\n```sh\ntest -f src/big.py\n```\n' > "$B3/big/specs/spec01.md"
(cd "$B3" && git add -A && git -c user.email=p@p -c user.name=p commit -qam spec)
S3=$(python3 "$PLAN" scan "$B3" 2>/dev/null)
has "big is ready" "$(section "$S3" ready)" "big · p62"
lacks "big is not to collect" "$(section "$S3" collect)" "big ·"
OUT=$(python3 "$TR" claim big w --board "$B3" 2>&1); RC=$?
eq  "claim big w exits 0" "$RC" 0
eq  "big moved open → analyzing" "$(state_of "$B3/big")" analyzing

echo "# children all done, but an open box in prd.md — not a container either"
B4=$(fixture); sed -i.bak 's/^state: open$/state: done/' "$B4/big/second/prd.md"; rm -f "$B4/big/second/prd.md.bak"
printf '\n## Acceptance\n\n- [ ] the tree reads as one\n' >> "$B4/big/prd.md"
(cd "$B4" && git -c user.email=p@p -c user.name=p commit -qam box)
S4=$(python3 "$PLAN" scan "$B4" 2>/dev/null)
has "big is ready" "$(section "$S4" ready)" "big · p62"
lacks "big is not to collect" "$(section "$S4" collect)" "big ·"
eq  "gate_claim accepts it" "$(gate_check "$B4" | tail -1)" "ready-ok 1 ready-bad 0 gated-ok 1 gated-bad 0"

echo "# parked child AND a spec of its own — the parked child still wins"
B5=$(fixture); sed -i.bak 's/^state: open$/state: later/' "$B5/big/second/prd.md"; rm -f "$B5/big/second/prd.md.bak"
mkdir -p "$B5/big/specs"; cp "$B3/big/specs/spec01.md" "$B5/big/specs/"
(cd "$B5" && git add -A && git -c user.email=p@p -c user.name=p commit -qam both)
S5=$(python3 "$PLAN" scan "$B5" 2>/dev/null)
has "big is gated on the parked child" "$(section "$S5" gated)" "leaf: big held by big/second (parked)"
lacks "big is not ready" "$(section "$S5" ready)" "big"

echo "# an open PRD carrying a stale claim — unclaimed, never ready"
B6=$(fixture); sed -i.bak 's/^state: open$/state: open\nclaim: worker-gone 2026-08-28 10:00/' "$B6/big/second/prd.md"; rm -f "$B6/big/second/prd.md.bak"
(cd "$B6" && git -c user.email=p@p -c user.name=p commit -qam stale)
S6=$(python3 "$PLAN" scan "$B6" 2>/dev/null)
lacks "big/second is not ready" "$(section "$S6" ready)" "big/second"
has "big/second is gated: unclaimed" "$(section "$S6" gated)" "unclaimed: big/second carries \`claim: worker-gone 2026-08-28 10:00\`"
ERR=$(python3 "$TR" claim big/second w --board "$B6" 2>&1 >/dev/null); RC=$?
eq  "claim refuses it" "$RC" 1
has "with the unclaimed prefix" "$ERR" "unclaimed: big/second carries"

echo "# the prose says it once each"
has "states.md: claim runs plan.dispatchable" "$(cat "$ROOT/references/parts/states.md")" '`claim` runs `plan.dispatchable`'
has "states.md: a parked child holds its parent" "$(cat "$ROOT/references/parts/states.md")" "A parked child holds its parent"
has "board.md: container is collect's" "$(cat "$ROOT/references/parts/board.md")" "is a container — \`collect\` closes it, \`claim\` refuses"
has "order.md: every child done, parked holds" "$(cat "$ROOT/references/parts/order.md")" "every child \`done\` — a parked
   child holds its parent"

echo
echo "$((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" -eq 0 ]
