---
state: done
origin: requested
priority: 4
complexity: 12
blast-radius: mid
repo: pearde
footprint:
  - resources/board
  - index.md
---

# view-source-split — the page is files, not a Python string

`@resources/board/render.py` is 169,360 bytes, of which 7% is Python. The rest
is 42,177 bytes of CSS and 109,742 bytes of JS held in one string literal, so
no editor highlights it, no linter reads it, and nothing can test it.

Split the literal into `resources/board/view.css` and `resources/board/view.js`,
inlined at render time. The rendered page does not change.

Done when `prds/.view.html` renders **byte-identical** to the file this PRD's
first spec captures, and `render.py` is Python only.

## Constraints

- One self-contained output. `plan.py gantt` writes a file that opens over
  `file://` with no service — inlining happens at render, never a link.
- No dependency, no build step. Python 3 stdlib only, as four module
  docstrings already state.
- Hot reload keeps working. `@resources/board/serve.py` stats `SOURCES` every
  second and re-execs; the two new files join that list.
- Substitution order: `__CSS__` and `__JS__` first, then `__PAYLOAD__` and
  `__TITLE__`. `let DATA = __PAYLOAD__` moves inside `view.js` and must still
  be filled.
- The `</` → `<\/` escape applies to the payload only, and stays where it is.

## Pointers

- `TEMPLATE` holds exactly one `<style>` block and one `<script>` block.
- `LIVE_JS` lives in `@resources/board/serve.py` and is injected separately.
  It is out of this PRD's footprint and does not move.

## Report

**DONE.** Both specs closed, 15 of 15 boxes.

| | before | after |
|---|---|---|
| `render.py` | 169,360 B, 7% Python | **18,047 B, Python only** |
| `view.css` | — | 42,161 B |
| `view.js` | — | 109,724 B |

```
$ cmp baseline.view.html /Users/feb/dev/infra/prds/.view.html
BYTE-IDENTICAL
$ grep -c '__CSS__\|__JS__\|__PAYLOAD__\|__TITLE__' .view.html
0
$ python3 resources/index.py check ; echo rc=$?
rc=0
$ bash resources/doctor.sh ; echo rc=$?
  index       ok      68 files · 24 keywords · every anchor resolves
  view        ok      watching · http://127.0.0.1:8443/board/pearde
rc=0
```

One spec box was amended, not met as written. `spec02` asked that
`index.py scope view` list **seven** files. The scope holds eight — a
concurrent restructure moved `resources/view/` to `resources/board/`, split the
skill into ten, and added `@skills/pearde-view.md` to the same scope. The box
now reads "lists every file in the scope, the two new ones included", which is
what it was checking for. The count was never the point.

The same restructure repathed this PRD and its specs from `resources/view` to
`resources/board`.

**Defect found after `done`, and fixed.**

`spec02` added `view.css` and `view.js` to `SOURCES` so that editing one
reloads the open page. `restart()` compile-checks every entry in `SOURCES`
with Python's `compile()`. Neither file is Python, so the check raised
`SyntaxError`, `REFUSED` latched, and **the daemon stopped reloading
altogether** — it kept serving the code it had imported at start-up. The log
carried 17 refusals:

```
serve: view.css:1: invalid character '─' (U+2500) — not reloading
```

Symptom: the served page ran an older `render.py`, so the page's script was a
classic `<script>` while `view.js` opens with `import … from "lit"` —
`Uncaught SyntaxError: import declarations may only appear at top level of a
module`. The rendered `.view.html` file was correct throughout.

Fixed: `restart()` compile-checks `.py` only. The assets stay in `SOURCES`,
which is what changes the boot stamp and makes an open page reload.

Proved end to end — a `view.css` edit now reloads the open page:

```
{ loadsBeforeEdit: 1, loadsAfterEdit: 2, pageReloadedOnCssEdit: true }
```

**Why the gate missed it.** `viewtest.js` only ever opened `file://`. The
service is a different code path — it injects its own head script and live
loop — so a page that is correct as a file can be broken as a service. The
harness now takes a URL too, and counts any response of 400 or worse as a
failure, which is how the `/favicon.ico` 404 on every served page surfaced.
