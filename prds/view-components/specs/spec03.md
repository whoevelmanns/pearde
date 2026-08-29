---
complexity: 12
footprint:
  - resources/board/view.js
  - references/parts/view.md
---

# spec03 — a user's element is rendered by the page

A board's `view.user.js` registers a custom element. The page renders it in
named seams it owns, so an extension is part of the page rather than something
that rewrites it afterwards.

`pearde.slot(name, tag)` is the registration. The page renders every element
registered for a seam, in registration order, passing the payload down.

## Acceptance

- [x] `pearde.slot(name, tag)` exists and accepts a seam name and a tag name
- [x] The page carries at least the seams `toolbar`, `sidebar` and `inspector`
- [x] An element registered for a seam appears in the page's DOM
- [x] It receives the payload as a `data` property
- [x] A seam with nothing registered renders nothing — no empty wrapper
- [x] An unknown seam name is ignored, not an error
- [x] Registering after first paint still renders it
- [x] A board with no `view.user.js` renders no seam content — every seam
      is empty and `display:none`, so the page looks as it did
- [x] The harness is green on both boards
- [x] `references/parts/view.md` documents `pearde.slot` and the seam names

## Verify and Proof

```sh
cat > prds/view.user.js <<'JS'
import { LitElement, html } from "lit";
class MyPanel extends LitElement {
  static properties = { data: {} };
  render() { return html`<div id="mine">mine: ${this.data?.all?.length ?? 0}</div>`; }
}
customElements.define("my-panel", MyPanel);
pearde.slot("sidebar", "my-panel");
JS
python3 resources/board/plan.py gantt prds && node resources/board/viewtest.js prds/.view.html
rm prds/view.user.js
```
