---
state: done
origin: requested
priority: 4
complexity: 22
blast-radius: low
repo: pearde
needs:
  - view-source-split
footprint:
  - resources/board
  - references/parts
  - index.md
---

# view-user-extensions — a board styles and scripts its own view

Changing a colour in the view means editing `@resources/board/render.py` today,
and the next `git pull` of the skill conflicts with that edit. The user's
change and the skill's source are the same file.

Give a board its own `prds/view.user.css` and `prds/view.user.js`, inlined
after the core when they exist. They live on the **board**, not in the skill,
so an extension survives a skill upgrade and differs per board.

Publish `window.pearde` as the surface those files may use, and document it.

Done when a board carrying both files renders them into its page, a board
carrying neither renders exactly as it does now, and the daemon reloads the
page when either file changes.

## Constraints

- Additive only. A board with no user files renders byte-identical output.
- Inlined after the core CSS and JS, so a user rule wins on cascade order and
  a user script sees a built page.
- `digest()` in `@resources/board/serve.py` walks `.md` only. A `.css` or `.js`
  change on the board must reach the watcher, or the page never updates.
- The surface is a contract. Name what is public, and nothing else.
- The user files are the board's, never the skill's. `resources/index.py`
  excludes board paths from the index, so they need no rows.

## The surface

`window.pearde` publishes what the page already assigns to `window.__pearde_*`
today, under one name:

| member      | is                                                        |
|-------------|-----------------------------------------------------------|
| `data`      | the enriched payload the page is drawing                   |
| `refresh()` | re-fetch and swap the payload in place                     |
| `apply(p)`  | swap a payload in without fetching                         |
| `onHold(f)` | register a predicate that pauses live updates while true   |
| `board`     | the board key this page was rendered for                   |

The `__pearde_*` globals stay — `LIVE_JS` in `@resources/board/serve.py` calls
them, and that file is injected into a page it does not render.

## Report

**DONE.** Four specs closed, 26 of 26 boxes.

| spec | delivers |
|---|---|
| 01 | `render(payload, board)` inlines the board's `view.user.css` and `view.user.js` after the core |
| 02 | `window.pearde` — `data`, `board`, `refresh`, `apply`, `onHold` |
| 03 | `digest()` stats both user files at every board root, so an edit reloads the page |
| 04 | the extension point documented in @references/parts/view.md |

Evidence:

```
$ node -e '<hold semantics>'          # HOLDS.some over the inspector predicate
clean, no user hold           : false (want false)
inspector dirty               : true  (want true)
user hold only                : true  (want true)
both released                 : false (want false)
user released, inspector dirty: true  (want true)

$ <digest before/after>
changes when view.user.css appears     : True
changes again when view.user.js appears: True
restored when both are removed         : True
master digest sees a member's asset    : True

$ curl http://127.0.0.1:8443/board/pearde   # the served path, not just the file
user css served: 1 · user js served: 1 · window.pearde: 1
removed cleanly when the files go: 0

$ node --check resources/board/view.js   # syntax-ok
$ python3 resources/index.py check ; bash resources/doctor.sh   # both rc=0
```

A `</style>` in user CSS and a `</script>` in user JS are both rewritten to
`<\/`, verified in the rendered page. The two literal `</script>` that remain
are the core's and the user's own closing tags.

Two findings outside this PRD's footprint, both fixed:

- `resources/index.py` demanded index rows for board files, contradicting
  @index.md's own "board paths address a board, not this skill". Any user whose
  board sits at the skill root hits it. `tracked()` now skips `prds/`.
- The live daemon was still running `resources/view/serve.py` after that
  directory was moved to `resources/board/`, so every `/board/<name>` request
  returned empty. Restarted from the new path — a daemon outlives a move of its
  own source, and `SOURCES` cannot notice a file that is gone.
