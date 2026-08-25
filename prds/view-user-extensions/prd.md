---
state: specced
origin: requested
priority: 4
complexity: 22
blast-radius: low
repo: pearde
needs:
  - view-source-split
footprint:
  - resources/view
  - references/parts
  - index.md
---

# view-user-extensions — a board styles and scripts its own view

Changing a colour in the view means editing `@resources/view/render.py` today,
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
- `digest()` in `@resources/view/serve.py` walks `.md` only. A `.css` or `.js`
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

The `__pearde_*` globals stay — `LIVE_JS` in `@resources/view/serve.py` calls
them, and that file is injected into a page it does not render.
