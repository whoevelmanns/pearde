---
complexity: 19
workflow: implement-a-spec
footprint:
  - resources/board/render.py
  - resources/board/view.js
  - resources/board/view.css
  - resources/board/viewtest.js
  - references/parts/view.md
---

# spec03 — the page: the now strip, the round panel, the silent mark, the report view

A person opening `/board/<name>` sees in the first screenful what is
finished, what is waiting on them, what is in flight and whether its worker
is still moving, and what the session has written down. Four things on the
page, all Lit elements in the light DOM per `view-components`, all
replaceable through `pearde.replace`:

| on the page | is |
|---|---|
| `<pearde-now id="now">` under the title | three doors `to collect N` · `waiting on you N` · `in flight N` — the top three bands of `order.md`. Zero is dimmed, never absent. Doors: the timeline's collect filter, the list's `hot` band (question, blocked, refine, failed), the list's new `held` band (claimed, analyzing, not collect) |
| `<pearde-round id="round">` under the numbers | `prds/.round.md` read-only over `GET /round` on every swap: `## Owed` first, `## Asked`, the rest folded in a `details`. Absent file, absent panel |
| `silent 42m` beside `holding` | off `tasks[].silent` from `plan.py`; in amber in the tooltip, the inspector's facts, the names column's meta and the on-bar label. The page prints the number and never decides it |
| `<pearde-report id="report">`, ⌘7 | `prds/report.md` over `GET /report`, rendered as prose by a thirty-line `md()`: headings, paragraphs, lists, `code`, **bold**. No file, a line saying `pearde report` writes one |

## What already stands

The probe left it all in the tree: the three template hooks and the seventh
tab in `resources/board/render.py`; in `resources/board/view.js` the
`silentFor`/`fmtAge` pair beside `heldFor` (a `rich` flag — the tooltip sets
HTML, the inspector escapes its facts), the word in the column meta and the
label, `⌘1–7`, `drawNow()`/`drawRound()` off `drawHeader`, the `hot` and
`held` pseudo-states in `listRows`, `report` in `repaintView`, the three
element classes after the memos block, and `replace()` taking `report`,
`now` and `round`; the `#now`, `.silent`, `#round` and `#report` blocks in
`resources/board/view.css`; and in `references/parts/view.md` the report
row, the strip and panel paragraphs, the `silent` row, `⌘1–7`, the two
routes and the replace list.

**What is left:** `resources/board/viewtest.js` still asserts `six view
buttons` (`r.views === 6`) and walks a fixed six-view list for the switch
and snapshot checks. The matcher must read 7 and the two lists must include
`report`, so the harness reads what the page has. That is the one edit; it
is a matcher moved to the cell's text, and the rule it asserts — every tab
switches clean — is unchanged. The file carries another session's
uncommitted hunks at lines 184–216; the edit is at the check list and the
two view arrays, and must stay disjoint from them.

## Acceptance

The page half runs over the served URL of a registered copy of the example
board — `python3 resources/board/serve.py ensure $D/b/prds`, temp path,
unregistered at the end — with `claim-ttl: 1m` and mtimes two minutes back,
a `.round.md` and a `report.md` written into the copy. The probe's driver
`prds/the-board-runs-itself/the-page-shows-the-round/probe/page.js <url>
[<round-file>]` prints every reading below as one JSON.

- [x] the strip reads `1 · 1 · 1` on the example copy, three doors in the order `to collect · waiting on you · in flight`, its top edge inside the first 120px
- [x] the strip is `pearde-now`, no `shadowRoot`; the doors' `data-go` are `{collect:1}`, `{view:"list",state:"hot"}`, `{view:"list",state:"held"}`
- [x] a payload with `cpm.collect = []` applied through `pearde.apply` leaves three doors, one with class `dim`, reading `0 · 1 · 1`
- [x] the panel is `pearde-round`, no `shadowRoot`, and its `h5` heads read `owed asked established` in that order for a round file with those three sections in any order
- [x] rewriting `.round.md` while the page is open swaps the new `## Owed` line into the panel within two seconds, over the served URL, with no reload
- [x] the inspector on `building` says `holding <N>m · silent <N>m` as text and contains no `<span` — the escape path prints the plain form
- [x] `#views` has seven buttons ending in `report`; pressing ⌘7 shows `section[data-view="report"]` and the hash reads `#view=report`
- [x] the report view is `pearde-report`, no `shadowRoot`, and renders `report.md`'s `# ` line as its `h2`
- [x] `pearde.replace("now","my-now")` and `pearde.replace("round","my-round")` put the board's own elements in place and the page's `drawNow`/`drawRound` leave them alone on the next swap
- [~] ~~`node resources/board/viewtest.js --example --check <snapshot taken before this PRD>` reports every view's markup and text unchanged, and `47/47` once the button matcher reads 7~~ — **struck by the orchestrator at collect:** on a tree carrying another session's uncommitted `view.js` hunk (weights rendered as hours, `21w`→`0.4h`) a pre-PRD snapshot differs in every view for a reason outside this PRD, and this PRD's own strip sits in every view's header, so "unchanged" contradicts the contract's own Verify. The matcher fix is measured: `--example` reads `36/36`. The check is re-run honestly on a tree with one session's hunks, at the next snapshot
- [x] no page error on the served page or the `--example` file

## Verify and Proof

```sh
node resources/board/viewtest.js --example                 # 47/47 after the matcher edit
grep -c 'pearde-now\|pearde-round\|pearde-report\|data-v="report"' resources/board/render.py   # 4
grep -n 'PARTS_REPLACEABLE\|customElements.define("pearde-\(now\|round\|report\)"' resources/board/view.js
grep -n '^#now\|^\.silent\|^#round\|^#report' resources/board/view.css | head
grep -n 'silent 42m\|⌘1–7\|GET /round' references/parts/view.md
NODE_PATH=<where playwright-core is> bash prds/the-board-runs-itself/the-page-shows-the-round/probe/verify.sh   # 50/50 — drives resources/board/view.js over the served URL
```
