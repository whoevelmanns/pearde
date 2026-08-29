---
state: done
origin: requested
priority: 3
complexity: 45
blast-radius: high
repo: pearde
needs:
  - view-user-extensions
footprint:
  - resources/board
  - references/parts
  - index.md
---

# view-components — a user's own element is a first-class part of the page

`@resources/board/view.js` builds every DOM view by string concatenation into
`innerHTML`. A board's `view.user.js` can read `window.pearde` and rewrite that
DOM, but it cannot *be* part of the page — there is no seam to render into and
nothing to hold state.

Vendor Lit. A user extension then registers a custom element and the page
renders it, because the browser owns that contract and this repo does not have
to invent one.

Done when a board's `view.user.js` can register an element that renders inside
the page, and the view harness is green before and after every step.

## Constraints

- **The harness gates every step.** No spec closes with it red. It opens a
  rendered page in real Chrome and checks what the page built — the jsdom
  version could not see an ES module at all, which is exactly what this PRD
  introduces.
- One self-contained output. Lit is vendored into the repo and inlined, never
  fetched — the page opens over `file://` with no network.
- No build step, no package manager at runtime. Lit's CDN build is one
  self-contained ES module and is used as shipped.
- The CDN build has no decorators. Use static `properties` and `styles`.
- A board with no `view.user.js` renders what it renders now.
- Porting is per view, harness green after each. A view is not half-ported.

## Pointers

- `lit-core.min.js` is 15,734 bytes, BSD-3-Clause, no bare imports.
- `LIVE_JS` in @resources/board/serve.py is a separate classic script and calls
  `window.__pearde_*`. Module scope does not reach it, so those assignments
  stay.
- `window.__BOARD` / `__BASE` are set by an inline classic script in the head.
  A module is deferred and runs after, so they are there.

## Report

**DONE.** Five specs, 55 of 55 boxes.

| spec | delivers |
|---|---|
| 01 | the page is an ES module; `@resources/board/viewtest.js` is the gate |
| 02 | Lit 3 vendored, inlined as a `data:` import map — offline, no build |
| 03 | three seams; a board's element renders in the page with live data |
| 04 | the frontier column is `<pearde-frontier>`, light DOM |
| 05 | memos, list and board too — and `pearde.replace` for a whole view |

**The gate.** `viewtest.js` opens a rendered page in real Chrome. jsdom was
tried first and rejected: it skips a module script silently and reports a
blank page as a pass, which is exactly the change this PRD makes. `--snap`
writes each view's markup and text, `--check` compares. Both boards: 40/40.

Every port is provable rather than eyeballed. The text a reader sees is
unchanged in all six views. The only markup delta is the mount tag and Lit's
marker comments — `<div id="list">` became `<pearde-list id="list">`.

**Light DOM, not shadow.** @resources/board/view.css carries 41 rules aimed at
`#land`, and the stylesheet is the only place a colour is written down. Every
component returns itself from `createRenderRoot()`, so not one rule moved.

**Two views were not ported, on purpose.** A custom element name is unique per
document: `customElements.define("pearde-analytics", …)` in the page is the
only definition that name can have, so converting a view to an element does
not let a board replace it. `pearde.replace(view, tag)` does, and it covers
all five DOM views including the two unported ones. Analytics builds four SVG
generators as strings and asks carries live form state — both carry real
regression risk and neither gains anything a board can use.

**Nondeterminism found and neutralised.** Lit stamps a random marker id per
page load, and a claim renders "held 3m". The snapshot normalises both, or the
gate would fail against itself.

**A harness bug found and fixed.** Snapshots were keyed on the parent
directory name, which is `prds` for every board — the master and pearde boards
collided. Keyed on the board's own name now.
