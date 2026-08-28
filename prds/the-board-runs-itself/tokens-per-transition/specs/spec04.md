---
complexity: 10
footprint:
  - resources/board/view.js
  - references/parts/view.md
  - prds/the-board-runs-itself/tokens-per-transition/probe/viewcheck.js
---

# spec04 — the analytics view draws the two series

`resources/board/view.js` `drawAnalytics` adds two charts after the
burn-down: **Calls per transition** — `costLine`, a polyline over the rows of
`DATA.transitions` whose `calls` is a number, one dot per transition with
the PRD, the edge, the calls, the refusals and the tokens (`tokens
unmeasured` when `null`) in its title, and the subtitle naming calls as the
proxy for tokens — and **Refusals per session** — `bars` over
`DATA.guard.sessions`, one bar per session with its refusals, calls and
transitions. When `DATA.guard` is `null` both read `no guard`; a guard that
has counted nothing on the board says so. `references/parts/view.md` names
the two series in the analytics row and lists `.transitions.jsonl` beside
`.history.jsonl`.

The two hunks stand from the probe (in `drawAnalytics`'s `innerHTML` after
the burn-down chart, and `costLine` before the writing-a-PRD section), disjoint
from the names-column hunks another session holds in the same file. The
probe's `viewcheck.js` drives the page; `viewtest.js` stays at its count.

## Acceptance

- [x] on a rendered copy with two counted transitions, the analytics view holds a chart titled `Calls per transition` with two `circle` dots and a subtitle containing `calls are the proxy for tokens`
- [x] the same page holds a chart titled `Refusals per session` with one `.brow` per session, its value reading `<refused> · <calls> calls · <n> transitions`
- [x] rendered with `PEARDE_GUARD_STATE` naming an absent directory, both charts read `no guard`
- [x] `NODE_PATH=<node_modules> node resources/board/viewtest.js --example` prints `36/36 passed` and no page error
- [x] `references/parts/view.md` names both series in the analytics row and lists `prds/.transitions.jsonl` in the gitignore block

## Verify and Proof

```sh
node --check resources/board/view.js
grep -n 'function costLine\|Calls per transition\|Refusals per session' resources/board/view.js
grep -n 'Calls per transition\|calls per transition\|transitions.jsonl' references/parts/view.md
NODE_PATH=/Users/feb/gstack/node_modules bash prds/the-board-runs-itself/tokens-per-transition/probe/verify.sh </dev/null | sed -n '/^## the analytics view/,/^## nothing leaked/p'
NODE_PATH=/Users/feb/gstack/node_modules node resources/board/viewtest.js --example | tail -1
```
