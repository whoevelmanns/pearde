#!/usr/bin/env bash
# workflow-improve — the probe harness.
#
# The PRD's `## Verify` is a dry run: one worker report with two edits, one the
# atomic's fault and one the code's; the collect applies one, refuses one, moves
# `runs` 0 → 1 on the files that ran, and `check` stays silent.
#
# That dry run cannot happen on this board — `prds/workflows/` does not exist
# yet (workflow-seed writes it, and is still `open`). So the library is built in
# a temp dir at RUN TIME, and never under prds/: a file named prd.md anywhere
# below prds/ is picked up as a real PRD of this repo's own board, and a fixture
# that did that would move the counts of the board it is testing.
#
# The collect itself is performed by `collect.py` beside this file — the
# orchestrator's five actions, written down as code so the dry run can be RUN
# rather than described. Nothing in the shipped tree calls it; see the census at
# the end, which is the honest answer to "what enforces this".
#
#   bash prds/workflows-on-the-board/workflow-improve/probe/verify.sh
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
WF="$ROOT/resources/workflows.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ok()   { pass=$((pass+1)); printf '  ok   %s\n' "$1"; }
bad()  { fail=$((fail+1)); printf '  FAIL %s\n' "$1"; }
have() { case "$2" in *"$3"*) ok "$1";; *) bad "$1 — no '$3' in:"; printf '%s\n' "$2" | sed 's/^/       /';; esac; }
lacks(){ case "$2" in *"$3"*) bad "$1 — '$3' present in:"; printf '%s\n' "$2" | sed 's/^/       /';; *) ok "$1";; esac; }
eq()   { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 — expected '$3', got '$2'"; fi; }

TODAY="$(date +%Y-%m-%d)"

# ── a library at runs: 0 ─────────────────────────────────────────────────────
B="$TMP/board/prds"
mkdir -p "$B/workflows"
cat > "$B/settings.md" <<'EOF'
---
name: probe
language: English
workers: 1
pipeline: 1
---

# probe board
EOF

cat > "$B/workflows/fix-a-reported-break.md" <<'EOF'
---
workflow: fix-a-reported-break
subject: a reported break, from the report to the verified fix
date: 2026-08-20
runs: 0
---

# fix-a-reported-break — a reported break, from the report to the verified fix

## Use when

- someone reports something broken and the tree is the only witness

## Steps

| # | atomic                | why                                            | on failure |
|---|-----------------------|------------------------------------------------|------------|
| 1 | reproduce-the-failure | nothing is fixed until it fails first          | stop       |
| 2 | write-the-check       | a fix with no failing check is a guess         | → 1        |
| 3 | run-the-gate          | the node's work is not the tree's worst neighbour | → 2     |
EOF

cat > "$B/workflows/reproduce-the-failure.md" <<'EOF'
---
atomic: reproduce-the-failure
subject: turn a reported break into a command that fails on this tree
date: 2026-08-20
runs: 0
---

# reproduce-the-failure — a report into a command that fails here

## Do

1. Run the command the report names, from the repo root.

## Done when

- the command exits non-zero, and the output matches the report

## Fails when
EOF

cat > "$B/workflows/write-the-check.md" <<'EOF'
---
atomic: write-the-check
subject: a check that fails on the break and passes on the fix
date: 2026-08-20
runs: 0
---

# write-the-check — a check that fails before the fix

## Do

1. Add the case to `tests/run.sh`.
2. Run it and watch it fail.

## Done when

- the check fails on the unfixed tree

## Fails when
EOF

cat > "$B/workflows/run-the-gate.md" <<'EOF'
---
atomic: run-the-gate
subject: the repo's own gate over the changed node
date: 2026-08-20
runs: 0
---

# run-the-gate — the repo's gate, scoped to this node

## Do

1. Run the repo's gate over the paths this node changed.

## Done when

- the gate is green on every path in the footprint

## Fails when
EOF

CHECK0="$(python3 "$WF" check "$B" 2>&1)"
eq "the fixture library starts clean" "$CHECK0" ""
LIST0="$(python3 "$WF" list "$B" 2>&1)"
eq "every file starts at runs 0" "$(printf '%s\n' "$LIST0" | awk '{s+=$3} END{print s+0}')" "0"

# ── the worker report: two edits, one the atomic's fault, one the code's ─────
cat > "$TMP/report.md" <<'EOF'
## Workflow fix-a-reported-break

| # | atomic                | outcome             | note                                                        |
|---|-----------------------|---------------------|-------------------------------------------------------------|
| 1 | reproduce-the-failure | passed              |                                                             |
| 2 | write-the-check       | failed → 1 · passed | `## Do` says `tests/run.sh`; this repo's checks are `verify.sh` |
| 3 | run-the-gate          | stopped             | the gate is red on a break another PRD owns                 |

### Edits

**write-the-check** — `## Do` — 1. Add the case to the node's own `verify.sh`.
2. Run it and watch it fail.

**run-the-gate** — `## Done when` — - the gate is green, except on failures another PRD owns
EOF

# The library as it stands before the collect. A refused edit has to leave its
# atomic byte-for-byte as it was, and two greps would both pass on a file that
# had been reflowed around them — so keep the bytes and diff them.
cp -R "$B/workflows" "$TMP/before"

# Edit 1 is the atomic's fault: a stale path, one of the four shapes
# @references/parts/workflows.md lists as applied.
# Edit 2 is the code's: the tree was red for a reason the route did not cause,
# and applying it would leave `## Done when` unable to fail.
python3 "$HERE/collect.py" "$B" "$TMP/report.md" \
        --apply  write-the-check:'## Do' \
        --refuse run-the-gate:'## Done when':"the code's" \
        --today "$TODAY" > "$TMP/collect.out" 2>&1
RC=$?
COUT="$(cat "$TMP/collect.out")"
eq "the collect runs clean" "$RC" "0"
eq "the report carries exactly two edits" \
   "$(awk '/^### Edits/,0' "$TMP/report.md" | grep -c '^\*\*')" "2"

have "it says which edit it applied"  "$COUT" "applied  write-the-check"
have "it says which it refused"       "$COUT" "refused  run-the-gate"
have "it says whose fault the refusal was" "$COUT" "the code's"

# ── runs 0 → 1 on the files that ran ─────────────────────────────────────────
runs() { python3 - "$B/workflows/$1.md" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^runs:\s*(\S+)\s*$", s, re.M)
print(m.group(1) if m else "-")
PY
}
upd() { python3 - "$B/workflows/$1.md" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^updated:\s*(\S+)\s*$", s, re.M)
print(m.group(1) if m else "-")
PY
}

eq "the workflow counts the run"                "$(runs fix-a-reported-break)" "1"
eq "an atomic that ran counts it"               "$(runs reproduce-the-failure)" "1"
eq "the edited atomic counts it"                "$(runs write-the-check)" "1"
eq "an atomic that STOPPED still ran"           "$(runs run-the-gate)" "1"
# The back-edge at step 2 sent the run through step 1 a second time. The PRD's
# rule 3 is `runs` +1 per atomic that ran, not per traversal — one collect, one
# count — and @references/parts/workflows.md is where that is written down.
eq "a back-edge does not double-count step 1"   "$(runs reproduce-the-failure)" "1"

eq "updated moves on the file whose text changed" "$(upd write-the-check)" "$TODAY"
eq "updated does not move on an unchanged atomic" "$(upd reproduce-the-failure)" "-"
eq "updated does not move on a refused edit"      "$(upd run-the-gate)" "-"
eq "updated does not move on the workflow"        "$(upd fix-a-reported-break)" "-"

# ── the edit landed, and the refusal did not ─────────────────────────────────
W="$(cat "$B/workflows/write-the-check.md")"
have  "the applied edit replaced the stale path" "$W" "the node's own \`verify.sh\`"
lacks "the stale path is gone, not appended"     "$W" "tests/run.sh"
lacks "no dated log line was written"            "$W" "$TODAY —"
G="$(cat "$B/workflows/run-the-gate.md")"
have  "the refused edit left the atomic as it was" "$G" "the gate is green on every path in the footprint"
lacks "  … and did not land"                       "$G" "except on failures another PRD owns"
# Byte-for-byte apart from the one line rule 3 requires: this atomic `stopped`,
# so it ran, so `runs` moves. Everything else — body, `date`, the absence of an
# `updated:` line — has to be the same bytes. Masking only `runs` is what makes
# "unchanged" falsifiable; cmp on the whole file would fail on rule 3 itself.
mask() { sed 's/^runs: .*/runs: <masked>/' "$1"; }
if diff -q <(mask "$TMP/before/run-the-gate.md") \
           <(mask "$B/workflows/run-the-gate.md") >/dev/null; then
  ok "  … the refused atomic is byte-for-byte what it was, but for \`runs\`"
else
  bad "  … the refused atomic changed beyond \`runs\`:"
  diff -u <(mask "$TMP/before/run-the-gate.md") \
          <(mask "$B/workflows/run-the-gate.md") | sed 's/^/       /'
fi

# ── rule 4: check before the commit ──────────────────────────────────────────
CHECK1="$(python3 "$WF" check "$B" 2>&1)"
eq "check is silent after the collect" "$CHECK1" ""

LIST1="$(python3 "$WF" list "$B" 2>&1)"
eq "list totals four runs over four files" "$(printf '%s\n' "$LIST1" | awk '{s+=$3} END{print s+0}')" "4"
have "list prints runs beside the slug" "$LIST1" "write-the-check"

# ── rule 4 has teeth: a format-breaking edit is refused, not repaired ────────
D="$TMP/broken/prds"; mkdir -p "$D"; cp -R "$B/settings.md" "$D/"; cp -R "$B/workflows" "$D/"
# a run proposes a step row whose atomic nobody wrote — the shape rule 4 catches
python3 - "$D/workflows/fix-a-reported-break.md" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read().rstrip("\n")
s += "\n| 4 | tidy-the-branch       | the tree is left as it was found               | → 3        |\n"
open(p, "w", encoding="utf-8").write(s)
PY
CHECKB="$(python3 "$WF" check "$D" 2>&1)"
have "a format-breaking edit is caught before the commit" "$CHECKB" "names \`tidy-the-branch\`"
if [ -n "$CHECKB" ]; then ok "check exits loud on it"; else bad "check exits silent on a broken library"; fi

# `updated: <today>` on a file dated today is the same day, not an earlier one
E="$TMP/sameday/prds"; mkdir -p "$E/workflows"; cp "$B/settings.md" "$E/"
sed -e "s/^date: .*/date: $TODAY/" -e "s/^runs: .*/runs: 1/" \
    -e "/^runs:/a\\
updated: $TODAY
" "$B/workflows/reproduce-the-failure.md" > "$E/workflows/reproduce-the-failure.md"
CHECKE="$(python3 "$WF" check "$E" 2>&1)"
eq "a file edited on the day it was written still checks out" "$CHECKE" ""

# ── the shipped documents say it ─────────────────────────────────────────────
doc() { if grep -qF -- "$3" "$ROOT/$2"; then ok "$1"; else bad "$1 — $2 lacks '$3'"; fi; }
# A table row asserted with a fixed-width needle breaks the next time a row is
# added and the columns are re-padded. Match the cells, not the spacing.
row() { if grep -qE -- "$3" "$ROOT/$2"; then ok "$1"; else bad "$1 — $2 has no row matching /$3/"; fi; }

doc "loop step 6 opens the block on the report section" references/parts/loop.md \
    'A report carrying `## Workflow <slug>` followed a route'
doc "loop rule 1: the verdict decides the transition"   references/parts/loop.md \
    'a `stopped` row changes nothing about it'
doc "loop rule 2: applied when the atomic caused it"    references/parts/loop.md \
    'Apply an edit when the failure was the atomic'
doc "loop rule 2: refused, and say which"               references/parts/loop.md \
    'Refuse it when the failure was the code'
doc "loop rule 2: paste or refuse, never rewrite"       references/parts/loop.md \
    'refuse it, never rewrite it'
doc "loop rule 3: runs and updated"                     references/parts/loop.md \
    '`runs` +1** on the workflow and on every atomic that ran'
doc "loop rule 4: check before the commit"              references/parts/loop.md \
    'check` before the commit.** An edit that'
doc "loop rule 5: the footprint does not grow"          references/parts/loop.md \
    "The PRD's own \`footprint:\` does not change"
doc "loop names one writer"                             references/parts/loop.md \
    '**One writer: the orchestrator.**'
doc "loop step 1 collects a swept worker's rows"        references/parts/loop.md \
    "A swept worker's \`## Workflow\` rows are read with its report"

doc "commits.md widens the scope sentence"    references/parts/commits.md \
    'plus any workflow file'
doc "commits.md names it in the message"      references/parts/commits.md \
    'and named in the'
doc "commits.md has the message line"         references/parts/commits.md \
    'workflow: <slug> — <what the run taught>'
doc "commits.md keeps the footprint out of it" references/parts/commits.md \
    'no `footprint:` declares'
doc "commits.md sends a foreign library to its own repo" references/parts/commits.md \
    'its edits commit'

doc "solo.md writes the edit at the step"     references/parts/solo.md \
    'you write the'
# solo.md keeps the lead clause and pins the four collect-edit rules by their
# own words, so the paragraph cannot be rewritten around the lead and stay green.
docall() { # name file needle...
  local name="$1" file="$2"; shift 2
  for n in "$@"; do grep -qF -- "$n" "$ROOT/$file" || { bad "$name — $file lacks '$n'"; return; }; done
  ok "$name"
}
docall "solo.md names the same rules"          references/parts/solo.md \
    'Apply or refuse per whose fault' \
    "applied for the atomic's fault" \
    "the code's or the PRD's" \
    'every atomic that ran' \
    'never rewrite it'

doc "round.md carries the Edits section"      references/parts/round.md \
    '## Edits'
doc "round.md's row is applied or refused"    references/parts/round.md \
    'applied | refused'
doc "round.md says why a refusal is recorded" references/parts/round.md \
    'A refusal is the half that has to be'

doc "workers.md has the on-return rule"       references/parts/workers.md \
    '**On return, either brief.**'
doc "workers.md's table row"                  references/parts/workers.md \
    'any of the three, plus `## Workflow <slug>`'
doc "workers.md points at loop step 6"        references/parts/workers.md \
    'The five actions are'

doc "parts/workflows.md has the Improved section" references/parts/workflows.md \
    '## Improved'
row "  … a stale path is applied"                 references/parts/workflows.md \
    '^\| a stale path +\| applied +\|'
row "  … a wrong command is applied"              references/parts/workflows.md \
    '^\| a wrong command +\| applied +\|'
row "  … a check that cannot fail is applied"     references/parts/workflows.md \
    '^\| a check that cannot fail +\| applied +\|'
row "  … an unlisted failure shape is applied"    references/parts/workflows.md \
    '^\| a shape .* does not list +\| applied +\|'
row "  … the code's is refused"                   references/parts/workflows.md \
    "^\\| the code's +\\| refused +\\|"
row "  … the PRD's is refused"                    references/parts/workflows.md \
    "^\\| the PRD's +\\| refused +\\|"
doc "  … the four rules"                          references/parts/workflows.md \
    '**From a run, never from reading.**'
doc "  … fold, do not log"                        references/parts/workflows.md \
    '**Fold, do not log.**'
doc "  … an atomic stays one unit"                references/parts/workflows.md \
    '**An atomic stays one unit.**'
doc "  … the order may change from a run"         references/parts/workflows.md \
    '**The order may change from a run.**'
doc "  … runs is evidence, not a score"           references/parts/workflows.md \
    '**`runs` is evidence, not a score:**'
doc "  … the back-edge counts once"               references/parts/workflows.md \
    'a step taken twice'
doc "  … the collect row in the when-written table" references/parts/workflows.md \
    '| a run ends          |'

# ── the claim lives in more than one file, and the files agree ───────────────
# `runs` +1 and the refusal rule are stated in loop.md, workers.md and
# parts/workflows.md. Four needles above prove each is present; none would
# notice one file saying +1 per atomic and another +1 per traversal.
agree() { # name needle file file...
  n="$1"; shift; needle="$1"; shift
  miss=""
  for f in "$@"; do grep -qF -- "$needle" "$ROOT/$f" || miss="$miss $f"; done
  if [ -z "$miss" ]; then ok "$n"; else bad "$n — missing from:$miss"; fi
}
agree "two files count runs the same way" \
      'on the workflow and every atomic that ran' \
      references/parts/workers.md references/parts/workflows.md
agree "two files send the refusal to the round file" \
      'prds/.round.md' \
      references/parts/workflows.md references/parts/round.md
agree "two files say an edit is refused, not repaired" \
      'refused, not repaired' \
      references/parts/loop.md references/parts/workflows.md
agree "two files say the worker never writes the library" \
      'never writes' \
      references/parts/workers.md references/parts/workflows.md

# the on-return summary in workers.md and the numbered block in loop.md must
# not disagree about the order of the five actions. Each file phrases them its
# own way, so both are reduced to the same five tokens and the SEQUENCES are
# compared — asserting each phrase is present would pass on either order.
canon() { tr '\n' ' ' | tr -s ' ' \
         | sed -E 's/[Rr]ead the rows/@rows/g
                  s/Apply an edit|apply the edits/@apply/g
                  s/`runs` \+1/@runs/g
                  s/check` before the commit/@check/g
                  s/ride the PRD|on the PRD.s commit/@commit/g' \
          | grep -oE '@rows|@apply|@runs|@check|@commit' | tr '\n' '|'; }
ORDER_LOOP="$(awk '/^\*\*A report carrying/,/^\*\*One writer/' \
  "$ROOT/references/parts/loop.md" | canon)"
ORDER_WORKERS="$(awk '/^\*\*On return, either brief\./,/^\*\*Analyst\*\*/' \
  "$ROOT/references/parts/workers.md" | canon)"
eq "loop states the five actions in order" "$ORDER_LOOP" \
   "@rows|@apply|@runs|@check|@commit|"
eq "workers.md's summary gives the same order" "$ORDER_WORKERS" "$ORDER_LOOP"

# ── the census: which of these rules a command can fail ──────────────────────
# @references/parts/loop.md step 6 now carries five rules. A rule with no
# mechanism is a note, so this enumerates all five rather than the ones that
# happen to be checkable, and marks each.
printf '\n  census — what fails when the collect skips a rule\n'
printf '    %-46s %s\n' "rule" "the command that catches it"
printf '    %-46s %s\n' "1 read the rows / the verdict decides the state" "— nothing"
printf '    %-46s %s\n' "2 apply the atomic's, refuse the code's"         "— nothing"
printf '    %-46s %s\n' "3 runs +1, updated moved"                        "— nothing"
printf '    %-46s %s\n' "4 workflows.py check before the commit"          "workflows.py check · doctor's workflows row"
printf '    %-46s %s\n' "5 the changed files on the PRD's commit"         "— nothing"
printf '    four of five are prose the orchestrator follows or does not.\n'
printf '    the harness above measures rule 4, and measures that rules 1-3\n'
printf '    and 5 are stated where the collect reads — not that they ran.\n'

printf '\n%d/%d checks pass\n' "$pass" "$((pass+fail))"
[ "$fail" -eq 0 ]
