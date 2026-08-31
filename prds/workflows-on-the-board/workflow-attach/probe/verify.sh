#!/usr/bin/env bash
# workflow-attach — the probe harness.
#
# Builds throwaway boards in a temp dir and asserts what `plan.py scan` and
# `workflows.py check` say about `workflow:` on a prd.md and on a spec.
#
# The fixtures are written at RUN TIME and never live under prds/: a file
# named prd.md anywhere below prds/ is picked up by `_scan_one` as a real PRD
# of this repo's own board, and a fixture that did that would put phantom PRDs
# on the board it is testing.
#
#   bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PLAN="$ROOT/resources/board/plan.py"
WF="$ROOT/resources/workflows.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ok()   { pass=$((pass+1)); printf '  ok   %s\n' "$1"; }
bad()  { fail=$((fail+1)); printf '  FAIL %s\n' "$1"; }
have() { # name haystack needle
  case "$2" in *"$3"*) ok "$1";; *) bad "$1 — no '$3' in:"; printf '%s\n' "$2" | sed 's/^/       /';; esac
}
lacks() {
  case "$2" in *"$3"*) bad "$1 — '$3' present in:"; printf '%s\n' "$2" | sed 's/^/       /';; *) ok "$1";; esac
}

# ── a board with a library ───────────────────────────────────────────────────
B="$TMP/solo/prds"
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
date: 2026-08-28
runs: 0
---

# fix-a-reported-break — a reported break, from the report to the verified fix

## Use when

- someone reports something broken and the tree is the only witness

## Steps

| # | atomic               | why                                   | on failure |
|---|----------------------|---------------------------------------|------------|
| 1 | reproduce-the-failure | nothing is fixed until it fails first | stop       |
EOF

cat > "$B/workflows/reproduce-the-failure.md" <<'EOF'
---
atomic: reproduce-the-failure
subject: turn a reported break into a command that fails on this tree
date: 2026-08-28
runs: 0
---

# reproduce-the-failure — a report into a command that fails here

## Do

1. Run the command the report names, from the repo root.

## Done when

- a command in the shell history exits non-zero for the reported reason

## Fails when

| seen | means | do |
|------|-------|----|
EOF

prd() { # dir  extra-frontmatter
  mkdir -p "$B/$1"
  { printf -- '---\nstate: open\norigin: requested\npriority: 10\n'
    [ -n "${2:-}" ] && printf '%s\n' "$2"
    printf -- '---\n\n# %s — a probe PRD\n\nBody.\n' "$1"
  } > "$B/$1/prd.md"
}

prd resolves  "workflow: fix-a-reported-break"
prd dangling  "workflow: no-such-route"
prd atomic    "workflow: reproduce-the-failure"
prd bare      ""
prd empty     "workflow:"

SCAN="$(python3 "$PLAN" scan "$B" 2>&1)"

have  "a resolving slug prints wf <slug>"      "$SCAN" "resolves · p10"
have  "  … with the slug, unmarked"            "$(printf '%s\n' "$SCAN" | grep ' resolves ')"  "wf fix-a-reported-break"
lacks "  … and no ?"                           "$(printf '%s\n' "$SCAN" | grep ' resolves ')"  "wf fix-a-reported-break?"
have  "a slug naming no file marks wf <slug>?" "$(printf '%s\n' "$SCAN" | grep ' dangling ')"  "wf no-such-route?"
have  "a slug naming an ATOMIC marks the same" "$(printf '%s\n' "$SCAN" | grep ' atomic ')"    "wf reproduce-the-failure?"
lacks "no workflow: prints no wf"              "$(printf '%s\n' "$SCAN" | grep ' bare ')"      "wf "
lacks "an empty workflow: prints no wf"        "$(printf '%s\n' "$SCAN" | grep ' empty ')"     "wf "

CHK="$(python3 "$WF" check "$B" 2>&1)"
have  "check names the dangling one"           "$CHK" "dangling/prd.md: \`workflow: no-such-route\` names no workflow"
have  "check names the atomic one apart"       "$CHK" "a route was asked for and a single step was found"
lacks "check is silent about the resolving one" "$CHK" "resolves/prd.md"
lacks "check is silent about the bare one"      "$CHK" "bare/prd.md"
lacks "check is silent about the empty one"     "$CHK" "empty/prd.md"

# ── the dispatch list carries the mark too ───────────────────────────────────
# `scan` is not the only list a round reads. `ready now` in `plan` IS the
# dispatch list, and step 5 of loop.md skips a dangling PRD — so the mark has
# to survive into that output or the planner silently contradicts the rule.
PLANOUT="$(python3 "$PLAN" plan "$B" 2>&1 | sed -n '/ready now/,/^≈/p')"
have  "plan's ready now marks a dangling slug" \
      "$(printf '%s\n' "$PLANOUT" | grep ' dangling ')" "wf no-such-route?"
have  "  … and an atomic the same way" \
      "$(printf '%s\n' "$PLANOUT" | grep ' atomic ')"   "wf reproduce-the-failure?"
lacks "plan does not mark a slug that resolves" \
      "$(printf '%s\n' "$PLANOUT" | grep ' resolves ')" "wf "
lacks "plan does not mark a PRD with no key" \
      "$(printf '%s\n' "$PLANOUT" | grep ' bare ')"     "wf "

# ── a spec's own workflow: ───────────────────────────────────────────────────
mkdir -p "$B/resolves/specs"
cat > "$B/resolves/specs/spec01.md" <<'EOF'
---
complexity: 10
workflow: no-such-route-either
footprint:
  - resources/board/plan.py
---

# spec01 — a probe spec

## Acceptance

## Verify and Proof

```sh
true
```
EOF
CHK2="$(python3 "$WF" check "$B" 2>&1)"
have "a spec's dangling workflow is reported too" "$CHK2" "resolves/specs/spec01.md: \`workflow: no-such-route-either\`"
SCAN2="$(python3 "$PLAN" scan "$B" 2>&1)"
have "a spec's workflow does not change the PRD's mark" \
     "$(printf '%s\n' "$SCAN2" | grep ' resolves ')" "wf fix-a-reported-break"
rm -rf "$B/resolves/specs"

# ── a master board: the member resolves against its own library first ────────
M="$TMP/master/prds"
mkdir -p "$M"
cat > "$M/settings.md" <<EOF
---
name: master
language: English
workers: 2
pipeline: 2
members:
  - solo: $B
---

# master
EOF
mkdir -p "$M/workflows"
cp "$B/workflows/fix-a-reported-break.md" "$M/workflows/"
cp "$B/workflows/reproduce-the-failure.md" "$M/workflows/"
cat > "$M/workflows/master-only.md" <<'EOF'
---
workflow: master-only
subject: a route only the master's library holds
date: 2026-08-28
runs: 0
---

# master-only — a route only the master's library holds

## Use when

- proving the fallback to the master's library

## Steps

| # | atomic               | why                        | on failure |
|---|----------------------|----------------------------|------------|
| 1 | reproduce-the-failure | the fallback needs a step | stop       |
EOF
# the member names a route only the MASTER holds: the fallback must find it
python3 - "$B/dangling/prd.md" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read().replace("workflow: no-such-route",
                                             "workflow: master-only")
open(p, "w", encoding="utf-8").write(s)
PY
MSCAN="$(python3 "$PLAN" scan "$M" 2>&1)"
have "a member's own library still resolves on a master" \
     "$(printf '%s\n' "$MSCAN" | grep 'solo/resolves ')" "wf fix-a-reported-break"
have "a member falls back to the master's library" \
     "$(printf '%s\n' "$MSCAN" | grep 'solo/dangling ')" "wf master-only"
lacks "  … unmarked" \
     "$(printf '%s\n' "$MSCAN" | grep 'solo/dangling ')" "wf master-only?"

# ── the shipped documents say it ─────────────────────────────────────────────
doc() { # name file needle
  if grep -qF -- "$3" "$ROOT/$2"; then ok "$1"; else bad "$1 — $2 lacks '$3'"; fi
}
doc "contract.md carries the prd.md row"      references/parts/contract.md '| `workflow`  | user ·'
doc "contract.md carries the spec row"        references/parts/contract.md '| `workflow`  | analyst    | overrides'
doc "contract.md defaults it to none"         references/parts/contract.md '| `workflow`   | none'
doc "the prd template carries the key"        references/templates/prd.md  '# workflow:'
doc "the spec template carries the key"       references/templates/spec.md '# workflow:'
doc "workers.md carries the block"            references/parts/workers.md  '> Follow the workflow `<slug>`'
doc "workers.md names the brief command"      references/parts/workers.md  'workflows.py brief <slug>'
doc "workers.md forbids editing the library"  references/parts/workers.md  'Never edit the workflow files'
doc "the analyst reports the workflow"        references/parts/workers.md  '`workflow: none fit`'
doc "drill.md attaches on the tree it writes" references/drill.md          'write `workflow: <slug>` on that child'
doc "parts/workflows.md has the attach rows"  references/parts/workflows.md '## Attached'
doc "parts/workflows.md names the scan mark"  references/parts/workflows.md 'marks the line `wf <slug>?`'
doc "contract.md says who may write a spec" references/parts/contract.md 'the-orchestrator-may-write-a-spec.md'

# ── the block is ONE text in two files ───────────────────────────────────────
# workers.md holds the copy every dispatch pastes; prd.md holds the contract
# it was agreed as. Four needles above prove the block is present, and none of
# them would notice a word changed in the middle of it. This compares them.
blk() { awk '/^> Follow the workflow/ {on=1} on { if ($0 !~ /^>/) exit; print }' "$1"; }
BLK_PRD="$(blk "$ROOT/prds/workflows-on-the-board/workflow-attach/prd.md")"
BLK_WRK="$(blk "$ROOT/references/parts/workers.md")"
if [ -z "$BLK_PRD" ] || [ -z "$BLK_WRK" ]; then
  bad "the block is extractable from both files — prd.md $(printf '%s' "$BLK_PRD" | wc -l) lines, workers.md $(printf '%s' "$BLK_WRK" | wc -l) lines"
else
  ok "the block is extractable from both files"
  if [ "$BLK_PRD" = "$BLK_WRK" ]; then
    ok "the block is byte-identical in prd.md and workers.md"
  else
    bad "the block has DRIFTED between prd.md and workers.md:"
    diff <(printf '%s\n' "$BLK_PRD") <(printf '%s\n' "$BLK_WRK") | sed 's/^/       /'
  fi
fi

# ── the loop refuses the dispatch ────────────────────────────────────────────
nodoc() { # name file needle — the file must NOT carry it any more
  if grep -qF -- "$3" "$ROOT/$2"; then bad "$1 — $2 still carries '$3'"; else ok "$1"; fi
}
# The three dispatch skips left loop.md for `pearde claim`'s gate: each is
# asserted as behaviour — a fixture PRD, and `transitions.gate_claim` refusing it.
G="$TMP/gate/prds"; mkdir -p "$G"; cp "$B/settings.md" "$G/"; cp -R "$B/workflows" "$G/"
gprd() { # dir state extra-frontmatter
  mkdir -p "$G/$1"
  { printf -- '---\nstate: %s\norigin: requested\npriority: 10\n' "$2"
    [ -n "${3:-}" ] && printf '%s\n' "$3"
    printf -- '---\n\n# %s — a probe PRD\n\nBody.\n' "$1"
  } > "$G/$1/prd.md"
}
gprd dangling specced "workflow: no-such-route"
gprd waits    specced $'needs:\n  - pending'
gprd pending  open    ""
gprd clash    specced $'footprint:\n  - src/x.py'
gprd holder   claimed $'claim: impl-holder 2026-08-28 10:00\nfootprint:\n  - src/x.py'
gate() { # rel — what transitions.gate_claim says about it on the gate board
  python3 - "$ROOT/resources/board" "$G" "$1" <<'PYG'
import sys; sys.path.insert(0, sys.argv[1])
import transitions as t, plan as p
board, rel = sys.argv[2], sys.argv[3]; prds = p.scan(board)
try:
    t.gate_claim(board, prds, prds[rel]); print("NOT REFUSED")
except t.Refused as e:
    print(f"refused — {e}")
PYG
}
have 'claim refuses a `workflow:` naming nothing'   "$(gate dangling)" 'refused — workflow: `no-such-route` names no workflow'
have 'claim refuses a `needs:` that is not done'     "$(gate waits)"    'refused — needs: pending is `open`, not done'
have "claim refuses a footprint a claimed PRD holds" "$(gate clash)"    'refused — footprint: holder is claimed and holds `src/x.py`'
doc   "loop says claim names the gate that holds it" references/parts/loop.md \
      'and names the gate'
doc   "loop says what to do instead"               references/parts/loop.md \
      'fix the slug or remove the key'
doc   "loop names the scan mark"                   references/parts/loop.md \
      'marks the PRD'"'"'s line `wf <slug>?`'
doc   "loop names the checker"                     references/parts/loop.md \
      '`pearde workflow check` names the file'
# The master limit is asserted as TEXT, not as behaviour: asserting that
# `check` stays silent on a master would lock in the defect that
# prds/check-crosses-member-boundaries exists to remove.
doc   "loop names check's one-board limit"         references/parts/loop.md \
      'never reaches a member'
doc   "loop says where to run check instead"       references/parts/loop.md \
      'Run `check` on the board the PRD lives on'
nodoc "loop no longer says two skips"              references/parts/loop.md \
      'Both skips are real work'
nodoc "loop no longer says which of the two"       references/parts/loop.md \
      'which of the two holds it'

printf '\n%d/%d checks pass\n' "$pass" "$((pass+fail))"
[ "$fail" -eq 0 ]
