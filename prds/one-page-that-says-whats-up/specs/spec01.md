---
complexity: 6
footprint:
  - resources/board/render.py
  - resources/board/view.js
  - resources/board/view.css
  - references/parts/view.md
---

# spec01 — the round panel comes off the page, and the rule that keeps it off

`<pearde-round>` renders `prds/.round.md`, which is git-ignored machine scratch.
Remove the element, its draw call, its fetch and its CSS, and write the general
rule into `references/parts/view.md` so nothing git-ignored is rendered for a
person again.

## What the probe established

Measured on the live board at 1440x900. The panel occupied y=171..374 — the top
quarter of the fold, the heaviest block above the chart after the plot itself.
Its content at that moment was **false**, not merely wrongly-worded: it said
"32 PRDs · 27 done" and "one buildable PRD left: `workflow-skill`, claimed" when
the board held 37 PRDs, 28 done, and that PRD had already landed as `ca7f647`.

That is the argument for removing rather than restyling it, and it generalises:
**`.round.md` is only true at a transition, and the page presents it as live.**
The file carries no timestamp, so nothing on the page can say how old it is.
After a rewrite it was true again — and still rendered `references/parts/view.md`,
`.gitignore`, `resources/scout/*` and the sha `099bb39` in the first screenful.
So both halves hold independently: wrong register when fresh, false when not.

Nothing is edited yet. The probe removed the panel in the browser only, via
`prds/one-page-that-says-whats-up/probe/onepage.js`.

## Acceptance

- [x] `grep -c 'pearde-round' resources/board/render.py resources/board/view.js` reports `0` for both files
- [x] `grep -c '/round?board=' resources/board/view.js` reports `0` — the fetch is gone with the element
- [x] The CSS rules keyed to the panel (`.rhd`, `.sec.owed`) are gone from `resources/board/view.css`, or are still reached by an element that remains
- [x] `references/parts/view.md` contains, on one line, a sentence stating that nothing git-ignored is rendered for a person
- [x] `bash prds/one-page-that-says-whats-up/probe/verify.sh` — the five checks that assert the panel still exists now FAIL, and are updated in the same change to assert its absence
- [x] `python3 resources/index.py check` exits 0 and prints nothing

## Note on the mechanism

The rule in `references/parts/view.md` is prose, and prose is not a mechanism.
What would enforce it is a check that every path the view reads is tracked by
git — `git check-ignore -q <path>` returning non-zero for each fetch target in
`resources/board/serve.py`'s `ROUTES`. That check does not exist and this spec
does not build it; `serve.py` is not in this PRD's footprint. It is named here
so the next reader knows the rule is asserted by review, not by the tree.

## Verify and Proof

```sh
grep -c 'pearde-round' resources/board/render.py resources/board/view.js
grep -c '/round?board=' resources/board/view.js
grep -n 'git-ignored' references/parts/view.md
bash prds/one-page-that-says-whats-up/probe/verify.sh
python3 resources/index.py check
```
