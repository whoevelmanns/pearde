---
complexity: 5
footprint:
  - resources/view/view.js
---

# spec02 — `window.pearde`, the published surface

A user script needs a contract. The page already assigns `__pearde_apply`,
`__pearde_refresh` and `__pearde_hold` to `window` for `LIVE_JS` to call.
Publish the same capability under one documented name, and leave the three
globals in place — `LIVE_JS` is injected by `@resources/view/serve.py` into a
page it does not render, and calls them by those names.

## Acceptance

- [ ] `window.pearde` exists on a rendered page and is a plain object
- [ ] It carries `data`, `refresh`, `apply`, `onHold`, `board`
- [ ] `pearde.data` is the enriched payload — it has a `cpm` key
- [ ] `pearde.board` equals the board key the page was rendered for
- [ ] `onHold(f)` registers a predicate, and `__pearde_hold()` returns true
      while any registered predicate returns true
- [ ] The inspector's own dirty check still pauses live updates — the existing
      hold behaviour is not replaced, it is joined
- [ ] `window.__pearde_apply`, `__pearde_refresh` and `__pearde_hold` are all
      still assigned

## Verify and Proof

```sh
grep -n 'window.pearde' resources/view/view.js
grep -n '__pearde_apply\|__pearde_refresh\|__pearde_hold' resources/view/view.js
python3 resources/view/plan.py gantt /Users/feb/dev/infra/prds
grep -c 'window.pearde' /Users/feb/dev/infra/prds/.view.html
```
