---
complexity: 8
footprint:
  - resources/board/lit-core.min.js
  - resources/board/render.py
  - index.md
---

# spec02 — Lit is vendored and inlined

`lit-core.min.js` from the Lit 3 CDN build: one self-contained ES module, no
bare imports, BSD-3-Clause. Commit it and inline it ahead of `view.js`, so the
page still opens over `file://` with nothing fetched.

## Acceptance

- [x] `resources/board/lit-core.min.js` is in the repo, licence header intact
- [x] It declares no bare import — nothing to resolve at runtime
- [x] `render()` inlines it before `view.js` in the same module scope
- [x] A rendered page defines `LitElement` and `html` without a network fetch
- [x] A trivial Lit element renders text into the page, proved in the harness
- [x] The page still opens over `file://`
- [x] The harness is green on both boards
- [x] `index.md` has a row for it, in the `@@view` scope

## Verify and Proof

```sh
grep -c 'SPDX-License-Identifier: BSD-3-Clause' resources/board/lit-core.min.js
grep -o 'from"[^"]*"' resources/board/lit-core.min.js | sort -u   # empty
node resources/board/viewtest.js prds/.view.html
```
