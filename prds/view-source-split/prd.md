---
state: blocked
origin: requested
priority: 4
complexity: 12
blast-radius: mid
repo: pearde
footprint:
  - resources/view
  - index.md
---

# view-source-split — the page is files, not a Python string

`@resources/view/render.py` is 169,360 bytes, of which 7% is Python. The rest
is 42,177 bytes of CSS and 109,742 bytes of JS held in one string literal, so
no editor highlights it, no linter reads it, and nothing can test it.

Split the literal into `resources/view/view.css` and `resources/view/view.js`,
inlined at render time. The rendered page does not change.

Done when `prds/.view.html` renders **byte-identical** to the file this PRD's
first spec captures, and `render.py` is Python only.

## Constraints

- One self-contained output. `plan.py gantt` writes a file that opens over
  `file://` with no service — inlining happens at render, never a link.
- No dependency, no build step. Python 3 stdlib only, as four module
  docstrings already state.
- Hot reload keeps working. `@resources/view/serve.py` stats `SOURCES` every
  second and re-execs; the two new files join that list.
- Substitution order: `__CSS__` and `__JS__` first, then `__PAYLOAD__` and
  `__TITLE__`. `let DATA = __PAYLOAD__` moves inside `view.js` and must still
  be filled.
- The `</` → `<\/` escape applies to the payload only, and stays where it is.

## Pointers

- `TEMPLATE` holds exactly one `<style>` block and one `<script>` block.
- `LIVE_JS` lives in `@resources/view/serve.py` and is injected separately.
  It is out of this PRD's footprint and does not move.

## Blocked

Two boxes in `specs/spec02.md` wait on something outside this PRD:

| box | waits on |
|---|---|
| `resources/index.py check` exits 0 | @index.md matching the tree |
| `resources/doctor.sh` exits 0 | the same — `index` reads `broken`, 38 problems |

A second session is restructuring this repo while this PRD runs. Since
2026-08-25 22:04 it has moved `resources/scout/` to `skills/scout/`, moved the
root `SKILL.md` to `skills/pearde/SKILL.md`, added `skills/pearde/` as a
symlink facade over `index.md`, `README.md`, `references/` and `resources/`,
and added `references/targets.md` and `resources/targets.py`. @index.md still
lists the old paths and has no rows for the new ones.

None of the 38 problems names a file this PRD touched. This PRD's own rows for
@resources/view/view.css and @resources/view/view.js are present and resolve,
and `resources/index.py scope view` lists all seven files.

Closes when that restructure lands and @index.md matches the tree. The two
boxes are then re-run unchanged.
