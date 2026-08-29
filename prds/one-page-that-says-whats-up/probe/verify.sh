#!/usr/bin/env bash
# one-page-that-says-whats-up — probe harness.
#
# The page assertions this PRD really wants (three sections in order, at a
# narrow width and a wide one) need a browser. `viewtest.js` is that harness
# and it needs `playwright-core`, which is NOT installed here, so those are
# recorded in the report as measured-by-hand and are NOT asserted below.
# Everything here is a source-level fact the specs depend on.
cd "$(dirname "$0")/../../.." || exit 1
P=0; F=0
ok(){ P=$((P+1)); }
no(){ F=$((F+1)); echo "FAIL: $1"; }
t(){ if eval "$2" >/dev/null 2>&1; then ok; else no "$1"; fi; }

R=resources/board/render.py
V=resources/board/view.js
C=resources/board/view.css
S=resources/board/serve.py
M=references/parts/view.md

# ── the defect this PRD exists to remove — now asserted gone ────────────
t "render.py mounts no <pearde-round>"           "! grep -q 'pearde-round' $R"
t "view.js defines no pearde-round"              "! grep -q 'pearde-round' $V"
t "nothing reads the /round endpoint"            "! grep -q '\"/round?board=' $V"
t "view.css carries no .rhd rule"                "! grep -q '\\.rhd' $C"
t "view.css carries no .sec.owed rule"           "! grep -q 'owed li' $C"
t ".round.md is still git-ignored"               "grep -qx 'prds/.round.md' .gitignore"
t "prds/report.md is NOT git-ignored"            "! git check-ignore -q prds/report.md"
t "view.md states the git-ignored rule on one line" "grep -q 'Nothing that is git-ignored is rendered for a person' $M"

# ── the source section 1 should render ──────────────────────────────────
t "report.md exists"                             "test -f prds/report.md"
t "report.md carries a dateline"                 "sed -n '3p' prds/report.md | grep -q '^\*.*\*$'"
t "report.md has an '## In work' section"        "grep -q '^## In work' prds/report.md"
t "report.md has a '## Planned' section"         "grep -q '^## Planned' prds/report.md"
t "GET /report already exists — no serve.py edit" "grep -q '/report' $S"
t "view.js already has an md() prose renderer"   "grep -q 'function md(text)' $V"

# ── what 'every tab becomes a section' turned into ──────────────────────
# Each of these was written the other way round, to prove the defect existed.
# The defect does not exist any more, so each is now its own mirror.
t "every section draws eagerly, none per-view"   "! grep -q 'if (view === \"board\") drawBoard();' $V"
t "...and drawAll is what does it"               "grep -q 'function drawAll()' $V"
t "...calling all six draws"                     "test \$(grep -c 'if (!replaced.has(' $V) -eq 6"
t "the plan toolbar is inside its own section"   "python3 - <<'PY'
import sys
s=open('resources/board/render.py').read()
i=s.index('<section data-view=\"timeline\"'); j=s.index('id=\"tcontrols\"')
sys.exit(0 if i<j else 1)
PY"
t "the vision line is inside it too"             "python3 - <<'PY'
import sys
s=open('resources/board/render.py').read()
i=s.index('<section data-view=\"timeline\"'); j=s.index('id=\"purpose\"')
sys.exit(0 if i<j else 1)
PY"
t "no tab buttons remain"                        "test \$(grep -c 'role=\"tab\"' $R) -eq 0"
t "the bar is seven anchors that jump"           "test \$(grep -c 'href=\"#s-' $R) -eq 7"
t "every anchor has the section it names"        "python3 - <<'PY'
import re,sys
s=open('resources/board/render.py').read()
a=set(re.findall(r'href=\"#s-([a-z]+)\"', s))
b=set(re.findall(r'<section data-view=\"([a-z]+)\" id=\"s-', s))
sys.exit(0 if a and a==b else 1)
PY"
t "no pane is hidden by display:none"            "! grep -q 'section\[data-view\]{display:none}' $C"
t "sections stack instead"                       "grep -q 'section\[data-view\]{display:block' $C"
t "the stage is no longer viewport-locked"       "! grep -q 'height:min(76vh,calc(100vh - 258px))' $C"
t "...and its height is a plain one"             "grep -A1 '^#stage{display:flex' $C | grep -q 'height:min(74vh,720px)'"
t "...with no viewport arithmetic left in it"    "! grep -A1 '^#stage{display:flex' $C | grep -q 'calc('"
t "the three archives fold, and only those"      "test \$(grep -c 'details class=\"fold\"' $R) -eq 3"
t "the plot still owns a nested scroller"        "grep -q '#scroll{position:absolute;inset:0;overflow:auto' $C"

# ── the rule this PRD leaves behind ─────────────────────────────────────
t "view.md exists"                               "test -f $M"

echo "$((P+F)) checks · $P pass · $F fail"
[ "$F" -eq 0 ] || exit 1
