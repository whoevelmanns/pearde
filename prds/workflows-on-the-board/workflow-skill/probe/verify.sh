#!/usr/bin/env bash
# workflow-skill probe — `pearde-workflow` is a real skill file, and every
# place a skill is registered names it.
#
# Nothing here writes in the repo. The fixture is a copy of the skill root
# in a temp dir made at run time; scratch lives in a second temp dir outside it, so the fixture's
# own `git status` is never dirtied by this harness.
set -u
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd -P)"
P="$ROOT/prds/workflows-on-the-board/workflow-skill/probe"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); printf '  ok   %s\n' "$1"; }
no()  { FAIL=$((FAIL+1)); printf '  FAIL %s\n' "$1"; }
is()  { if [ "$2" = "$3" ]; then ok "$1"; else no "$1 — got [$2] want [$3]"; fi; }
has() { if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else no "$1 — no [$3]"; fi; }
hasnt(){ if printf '%s' "$2" | grep -qF -- "$3"; then no "$1 — found [$3]"; else ok "$1"; fi; }

SCRATCH="$(mktemp -d)"; D="$(mktemp -d)"
trap 'rm -rf "$SCRATCH" "$D"' EXIT

echo "== the skill file =="
S="$P/pearde-workflow.md"
[ -f "$S" ] && ok "probe/pearde-workflow.md exists" || { no "probe/pearde-workflow.md exists"; exit 1; }
NM=$(awk 'NR==1 && $0 !~ /^---/ {exit} /^---/ {n++; if (n==2) exit; next}
          n==1 && $1=="name:" {sub(/^[[:space:]]*name:[[:space:]]*/,""); print; exit}' "$S")
is "name: is the file name doctor would install" "$NM" "pearde-workflow"
case "$NM" in *:*) no "the name is kebab, no colon — @references/install.md" ;;
              *)   ok "the name is kebab, no colon — @references/install.md" ;; esac
DS=$(awk 'NR==1 && $0 !~ /^---/ {exit} /^---/ {n++; if (n==2) exit; next}
          n==1 && $1=="description:" {print "y"; exit}' "$S")
is "description: is present — it is what decides when the skill fires" "$DS" "y"
DESC=$(grep -m1 '^description:' "$S")
for t in "workflow" "how do we do X" "attach a workflow" "improve the workflow" "check the workflows"; do
  has "the description carries the trigger \"$t\"" "$DESC" "$t"
done
BODY=$(sed '1,/^---$/d;1,/^---$/d' "$S")
has "the body names @references/workflow.md — the format"      "$BODY" "@references/workflow.md"
has "the body names @references/parts/workflows.md — the part" "$BODY" "@references/parts/workflows.md"
has "the body names the scope @@workflows"                     "$BODY" '`@@workflows`'
if printf '%s\n' "$BODY" | grep -q '^## '; then
  no "the body has no section of its own — the knowledge is in the references"
else
  ok "the body has no section of its own — the knowledge is in the references"
fi

echo
echo "== the fixture: the skill root with the file placed =="
( cd "$ROOT" && git ls-files --cached --others --exclude-standard ) \
  > "$SCRATCH/files.txt"
( cd "$ROOT" && rsync -a --files-from="$SCRATCH/files.txt" . "$D" ) 2>/dev/null \
  || ( cd "$ROOT" && while IFS= read -r f; do
         mkdir -p "$D/$(dirname "$f")"; cp "$f" "$D/$f"; done < "$SCRATCH/files.txt" )
cp "$ROOT/.gitignore" "$D/.gitignore" 2>/dev/null
git -C "$D" init -q 2>/dev/null
cp "$S" "$D/skills/pearde-workflow.md"
N=$(ls "$D"/skills/*.md | wc -l | tr -d ' ')
is "the fixture holds twelve skill files" "$N" "12"

echo
echo "== the map check is what makes the registration load-bearing =="
# The fixture is copied from the live tree with `git ls-files --cached
# --others`, so once this contract has landed the copy already carries the
# skills row. Construct the unregistered state rather than inherit it: strip
# the row, measure, put it back. The rule is unchanged — the file alone,
# with no row, reddens the map.
cp "$D/references/files.md" "$SCRATCH/files.md.registered"
grep -v '^| @skills/pearde-workflow.md |' "$D/references/files.md" > "$SCRATCH/files.md.stripped"
cp "$SCRATCH/files.md.stripped" "$D/references/files.md"
BEFORE=$(cd "$D" && python3 resources/index.py check 2>&1)
cp "$SCRATCH/files.md.registered" "$D/references/files.md"
has "before the rows: the map names the unregistered file" "$BEFORE" "skills/pearde-workflow.md is on disk with no row"

APPLY=$(cd "$D" && python3 "$P/apply.py" "$D" 2>&1); ARC=$?
is "apply.py exits 0"                "$ARC" "0"
has "apply.py applied every hunk"    "$APPLY" "apply: 15 hunks"
AFTER=$(cd "$D" && python3 resources/index.py check 2>&1)
is "after the rows: index.py check is silent" "$AFTER" ""

SUM1=$(cd "$D" && cat SKILL.md index.md README.md references/files.md references/system.md references/parts/handles.md | cksum)
(cd "$D" && python3 "$P/apply.py" "$D" >/dev/null 2>&1)
SUM2=$(cd "$D" && cat SKILL.md index.md README.md references/files.md references/system.md references/parts/handles.md | cksum)
is "apply.py is idempotent — a second run doubles no hunk" "$SUM1" "$SUM2"

echo
echo "== every place a skill is registered =="
has "SKILL.md names it in the description's list"  "$(cat "$D/SKILL.md")" "pearde-workflow"
has "SKILL.md also names pearde-report"            "$(cat "$D/SKILL.md")" "pearde-report"
H=$(cat "$D/references/parts/handles.md")
has "handles.md: it is one of the skills of their own" "$H" '`pearde-workflow`'
for r in "the workflow library" "one, as a worker sees it" "a new atomic" "a new workflow" "attach a workflow to a PRD" "check the library"; do
  has "handles.md carries the row \"$r\"" "$H" "| $r"
done
has "handles.md: the library row names a command that runs"  "$H" '`pearde workflow list`'
has "handles.md: the check row names a command that runs"    "$H" '`pearde workflow check`'
I=$(cat "$D/index.md")
has "index.md: @@skills gains the file" "$I" "@skills/pearde-workflow.md · @references/install.md"
has "index.md: @@workflows gains it as its first anchor" "$I" "| @skills/pearde-workflow.md · @references/workflow.md"
has "files.md: the row is in the skills table" "$(cat "$D/references/files.md")" "| @skills/pearde-workflow.md |"
R=$(cat "$D/README.md")
has "README: the doing-the-work row gains @@workflows" "$R" '`@@specs` · `@@workflows`'
has "README: the lookup table gains the workflows row" "$R" "what a worker follows, and how a run improves it"
RN=$(printf '%s' "$R" | grep -c 'for the twelve skills')
is "README: the install line counts twelve, and skills/ holds twelve" "$RN" "1"
SY=$(cat "$D/references/system.md")
has "system.md: the Following bullet" "$SY" "- **Following** —"
has "system.md: workflow is in the handles line" "$SY" '`workflow [<slug>]`'

echo
echo "== install and doctor discover it with no list to edit =="
DEST="$SCRATCH/dest"; mkdir -p "$DEST"
DRY=$(cd "$D" && bash resources/install.sh "$DEST" 2>&1)
has "install.sh lists pearde-workflow with no --apply" "$DRY" "pearde-workflow"
APP=$(cd "$D" && bash resources/install.sh --apply "$DEST" 2>&1)
[ -e "$DEST/pearde-workflow/SKILL.md" ] && ok "install --apply built <dest>/pearde-workflow/SKILL.md" \
                                        || no "install --apply built <dest>/pearde-workflow/SKILL.md"
LNK=$(readlink "$DEST/pearde-workflow/SKILL.md" 2>/dev/null)
is "the built SKILL.md links to the repo's skill file" "$LNK" "$D/skills/pearde-workflow.md"
DOC=$(cd "$D" && bash resources/doctor.sh 2>&1 </dev/null | grep '^ *skills')
has "doctor reports skills ok"                 "$DOC" "ok"
has "doctor names pearde-workflow in the row"  "$DOC" "pearde-workflow"
has "doctor counts twelve well-formed skills"  "$DOC" "12 well-formed"

echo
echo "== the one committed harness whose literals this contract moves =="
git -C "$D" add -A >/dev/null 2>&1
git -C "$D" -c user.email=p@p -c user.name=p commit -qm base >/dev/null 2>&1
RM=$(cd "$D" && bash prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh </dev/null 2>&1 | tail -1)
is "readme-in-three-rings holds its baseline once the four literals move" \
   "$RM" "72 checks · 72 pass · 0 fail"

echo
echo "== the command behind the handle already runs (read-only, real repo) =="
L=$(cd "$ROOT" && python3 resources/pearde.py workflow list 2>&1); LRC=$?
is "pearde workflow list exits 0" "$LRC" "0"
has "pearde workflow list prints the library" "$L" "probe-then-spec"
(cd "$ROOT" && python3 resources/pearde.py workflow brief probe-then-spec >/dev/null 2>&1)
is "pearde workflow brief <workflow> exits 0" "$?" "0"
(cd "$ROOT" && python3 resources/pearde.py workflow brief read-the-contract >/dev/null 2>&1)
is "pearde workflow brief <atomic> exits 1 — an atomic is shown, not briefed" "$?" "1"
(cd "$ROOT" && python3 resources/pearde.py workflow check >/dev/null 2>&1)
is "pearde workflow check exits 0 on a clean library" "$?" "0"
HELP=$(cd "$ROOT" && python3 resources/pearde.py help 2>/dev/null)
has "pearde help lists the four verbs" "$HELP" "pearde workflow brief"

echo
echo "== the two gaps this build found (asserted so the spec is backed) =="
BARE=$(cd "$ROOT" && python3 resources/pearde.py workflow 2>&1)
is "GAP 1 — bare \`pearde workflow\` prints nothing: it runs check, not list" "$BARE" ""
ADD=$(cd "$ROOT" && python3 resources/pearde.py workflow add atomic zzz-probe 2>&1)
has "GAP 2 — \`workflow add\` reads its verb as a board path" "$ADD" "no prds/ board at atomic"
[ -e "$ROOT/prds/workflows/zzz-probe.md" ] && no "\`workflow add\` wrote nothing" || ok "\`workflow add\` wrote nothing"
ATT=$(cd "$ROOT" && python3 resources/pearde.py workflow attach zzz-probe probe-then-spec 2>&1)
has "GAP 2 — \`workflow attach\` reads its verb as a board path" "$ATT" "no prds/ board at zzz-probe"

echo
echo "$((PASS+FAIL)) checks · $PASS pass · $FAIL fail"
[ "$FAIL" -eq 0 ]
