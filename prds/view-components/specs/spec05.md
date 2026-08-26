---
complexity: 18
footprint:
  - resources/board/view.js
  - resources/board/render.py
  - references/parts/view.md
---

# spec05 — the views that pay, and the seam that makes one replaceable

Four views become components: the frontier column, memos, the list, the board.
Each keeps its markup — the harness proves the text a reader sees is unchanged
and the only markup delta is the mount tag.

Analytics and asks stay as they are. A custom element name is unique per
document, so `customElements.define("pearde-analytics", …)` in the page is the
*only* definition that name can have — converting a view to an element does
not let a board replace it. What does is `pearde.replace(view, tag)`: a board
registers an element of its own and the page hands it the whole view.

Analytics builds four SVG generators as strings and asks carries live form
state. Neither gains replaceability from a port, and both carry the regression
risk. They are reachable through `pearde.replace` like every other view.

## Acceptance

- [x] `<pearde-frontier>`, `<pearde-memos>`, `<pearde-list>`, `<pearde-board>`
      are defined and mounted
- [x] Each renders into light DOM — no rule moved out of `view.css`
- [x] Every one of the six views' text is unchanged against its snapshot
- [x] The only markup delta is the mount tag and Lit's marker comments
- [x] `pearde.replace(view, tag)` swaps a view for a board's own element
- [x] The built-in draw for a replaced view stops running — no null node
- [x] Switching through every view with one replaced raises no error
- [x] An unreplaceable view name is ignored, not an error
- [x] A board with no `view.user.js` is unaffected
- [x] The harness is green on both boards
- [x] `references/parts/view.md` documents `pearde.replace` and what it covers

## Verify and Proof

```sh
node resources/board/viewtest.js prds/.view.html --check <snapshots>
node resources/board/viewtest.js /Users/feb/dev/infra/prds/.view.html --check <snapshots>
```
