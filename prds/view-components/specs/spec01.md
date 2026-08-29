---
complexity: 10
footprint:
  - resources/board/viewtest.js
  - resources/board/render.py
  - index.md
---

# spec01 — the page is a module, and the harness is the gate

Lit is an ES module, so the page's script becomes `type="module"`. Nothing
else in the page can verify that: jsdom silently skips a module script and
reports a blank page as a pass.

Ship the harness that can. It opens a rendered page in real Chrome, counts
canvas draws, switches every view and asserts each section is actually shown.

## Acceptance

- [x] `resources/board/viewtest.js` exists and runs a rendered page
- [x] It reports one line per check and exits non-zero when any fails
- [x] It says what to install when `playwright-core` is absent, and exits 2
      rather than throwing
- [x] `TEMPLATE` emits `<script type="module">`
- [x] The harness is green on a 2-PRD board
- [x] The harness is green on the 206-PRD master board
- [x] `index.md` has a row for the harness, in the `@@view` scope
- [x] `resources/index.py check` and `resources/doctor.sh` both exit 0

## Verify and Proof

```sh
node resources/board/viewtest.js prds/.view.html
node resources/board/viewtest.js /Users/feb/dev/infra/prds/.view.html
python3 resources/index.py check && bash resources/doctor.sh >/dev/null && echo green
```
