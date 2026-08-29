---
complexity: 15
footprint:
  - resources/board/view.js
  - resources/board/viewtest.js
---

# spec04 — the frontier column is a component

`drawSide()` builds the column by concatenating strings into `innerHTML`.
Make it `<pearde-frontier>`, a Lit element holding the payload — the same
markup, the same behaviour, and a board can now replace it.

**Light DOM, not shadow.** `@resources/board/view.css` carries 41 rules
targeting `#land .cap`, `#land .lrow` and their kin, and states that the
stylesheet is the only place a colour is written down. A shadow root would cut
every one of them off and fragment the design system across two files.
`createRenderRoot()` returning the element keeps one stylesheet.

## Acceptance

- [x] `<pearde-frontier>` is defined and renders into `#land`
- [x] It renders into light DOM — `view.css` still styles it, no rule moved
- [x] It takes the payload as `data` and re-renders when that is swapped
- [x] The column shows the same three sections: to collect, ready now, to land
- [x] Every row is still a door — clicking one opens that PRD
- [x] The section heads still filter
- [x] `landOpen` still hides and shows the column
- [x] The harness is green on both boards, with a check that the column has rows
- [x] `node --check resources/board/view.js` exits 0

## Verify and Proof

```sh
node --check resources/board/view.js
node resources/board/viewtest.js prds/.view.html
node resources/board/viewtest.js /Users/feb/dev/infra/prds/.view.html
```
