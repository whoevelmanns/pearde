---
complexity: 6
footprint:
  - resources/board/view.js
  - prds/the-board-asks-for-itself/a-question-in-plain-words/probe/
---

# spec03 — the asks card hides the anchor and shows the open door

The view's asks page and the inspector strip the technical anchor before
anything is rendered, and the own-answer box is headed *or write your own* —
the words `references/drill.md` says the open door in.

**What already stands** (built during the analysis, uncommitted):
`stripAnchor()` in `resources/board/view.js`, called at the top of
`parseQuestions()` and on the raw `<pre>` fallback in the inspector, and the
own-answer header changed from *your own answer* to *or write your own*.
`probe/viewprobe.js` pulls those three functions out of `view.js` and runs them
without a browser, so the check needs neither playwright-core nor a Chrome.

**What is left**: the browser path. `resources/board/viewtest.js` drives a real
Chrome and is the honest end-to-end check; it needs `npm i playwright-core` and
was not run during the analysis. Run it if the driver is available on the
machine that lands this; `viewprobe.js` is the gate that always runs.

## Acceptance

- [x] `node --check resources/board/view.js` passes.
- [x] `node probe/viewprobe.js` exits 0: the clean question parses to one
      question with three answers, the recommended one marked.
- [x] No part of the rendered card contains the anchor comment — not the text
      `for the board:`, not the file it names, not an escaped `<!--`.
- [x] The rendered card contains the string `or write your own`.
- [x] `stripAnchor` is applied to the raw fallback too, so a section that does
      not parse into a pickable card still hides the anchor.

## Verify and Proof

```sh
node --check resources/board/view.js && echo "syntax ok"
node prds/the-board-asks-for-itself/a-question-in-plain-words/probe/viewprobe.js
grep -n "or write your own" resources/board/view.js
```
