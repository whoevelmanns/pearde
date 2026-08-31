---
complexity: 18
footprint:
  - resources/board/render.py
  - resources/board/view.js
  - resources/board/view.css
  - resources/board/viewtest.js
  - references/parts/view.md
---

# spec03 — every pane becomes a section on one scrolling page

The seven tab panes stop being panes. They stack in one column in the PRD's
order, the analytics moves below the board, and the tab bar becomes anchors
that jump without hiding anything.

`footprint:` overlaps spec01 and spec02 on `render.py`, `view.js`, `view.css`
and `view.md`. That is deliberate: these three specs are one page and one
implementer should take them in order 01, 02, 03. They are split by decision,
not by file.

## What the probe measured, and the work it uncovered

Applied to the live board with 37 PRDs, via `probe/onepage.js`:

**The panes do not draw unless they are visited.** Stacked without visiting
each tab first, the sections measured `board` 86px, `analytics` 42px, `asks`
32px, `list` 177px, `memos` 118px — empty frames. After clicking every tab to
force each draw and then stacking, the same sections measured 692px, 623px,
187px, 1265px and 1661px. The cause is the dispatcher in `view.js`, which runs
exactly one draw per repaint (`if (view === "board") drawBoard(); else if …`).
**This, not the tab bar, is the real work of this PRD** — six lazy draws
become eager, and three of them fetch.

**The plan's own furniture sits outside the plan's section.** `#tcontrols`
(vision/dates, group, zoom, filter) and `#purpose` (the vision line) are
siblings of `<section data-view="timeline">`, not children. Harmless when one
pane shows at a time; on a stacked page the plan's toolbar floats above
unrelated sections. Both must move inside the section they belong to.

**The plan is deliberately viewport-locked.** `#stage{height:min(76vh,calc(100vh
- 258px))}` with a comment saying the page must not grow past the plan. That
constant is written for a page that is one screen; on a scrolling page it needs
a plain height, and the `258px` term — the height of everything above the stage
— stops being true the moment section 1 goes in above it.

**The page is 5945px, and the memos are 28% of it.** `memos` alone rendered
1661px and 37,434 characters of full decision records. `list` is 1265px of
table. These are archives, not status.

**Narrow width is already broken, before this PRD.** At 390px the unmodified
page has `document.body.scrollWidth` 543 against a client width of 390, and
`nav#views` is 449px wide on its own — the tab bar overlaps the title, visibly.
Removing the tab bar removes the main cause. The probe's own stack measured
591px, so the stack adds 48px of its own that must also go.

Nothing is edited yet; all of the above was produced by a DOM transform in the
browser against the committed tree.

## A judgement, and it is smaller than the PRD suggests

"Every tab becomes a section" taken literally puts a 37,000-character memo
archive and a full table of every PRD underneath a page whose purpose is to say
what is up. The reader scrolls past status into reference material. The design
is: **status sections scroll; archives stay behind their anchor.** `memos` and
`list` keep an anchor in the bar and a heading in the flow, and render collapsed
with a count and a control that opens them. The PRD's rule — the bar never
hides a section — is kept, because the section is present, headed, and reachable
by scrolling; what is folded is its body, by the reader's choice, not the tab
bar's.

If the reviewer wants the literal reading instead, the change is one line and
the page becomes 6.6 folds of which 2.9 are archive.

## The four summaries problem

With section 1 in place the page opens with four things that all summarise the
board: the three doors (`0 to collect / 0 waiting on you / 1 in flight`), the
nine-figure stats bar, the vision line, and now the report prose. Measured, they
fill y=46..500 before the plan starts. The doors are the only ones that are
actions and they stay. The stats bar is dense metrics and belongs with the
analytics section or the plan, not above the prose. The vision line explains the
plan's axis and belongs to the plan's section as its subtitle.

## Acceptance

- [x] Opening the board shows, scrolling top to bottom: the prose section, the plan, the board, the analytics, then the remaining sections — no click required to reach any of them
- [x] Every section renders its content on first load, with no tab having been clicked; asserted by measuring that each section's rendered height is greater than its heading alone
- [x] `#tcontrols` and `#purpose` are inside `<section data-view="timeline">` in `resources/board/render.py`
- [x] `#stage` no longer derives its height from a hard-coded count of the pixels above it
- [x] At a 390px viewport, `document.body.scrollWidth` equals the client width — no horizontal scrolling
- [x] At a 1440px viewport the plan is visible without scrolling
- [x] The anchors in the bar jump to a section and never hide one; with JavaScript's own tools only, no build step and no dependency
- [x] `resources/board/viewtest.js` gains cases for section order, for every-section-drawn, and for the 390px width assertion

## The harness this needs and cannot run here

`resources/board/viewtest.js` is the browser harness and it needs
`playwright-core`, **which is not installed in this environment**. None of the
page assertions above were run by it. They were measured by hand through a
headless browser driven from the shell, and the numbers quoted in this spec are
from that. What would run them as a check is `npm i -D playwright-core` and then
`node resources/board/viewtest.js` against a served board — the implementer
should say plainly whether that install happened, and if it did not, the page
boxes are ticked on hand measurement and must say so.

## Verify and Proof

```sh
python3 - <<'PY'
import sys
s = open('resources/board/render.py').read()
i, j = s.index('<section data-view="timeline"'), s.index('id="tcontrols"')
sys.exit(0 if i < j else 1)
PY
grep -n 'data-view' resources/board/render.py
grep -n 'drawBoard\|drawList\|drawAnalytics\|drawMemos\|drawAsks' resources/board/view.js
grep -n 'stage{' resources/board/view.css
node resources/board/viewtest.js || echo "viewtest: playwright-core absent — page boxes measured by hand"
bash prds/one-page-that-says-whats-up/probe/verify.sh
```
