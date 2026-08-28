---
state: done
origin: requested
actual: 1.5h
commit: 0f59032
priority: 56
complexity: 30
blast-radius: mid
repo: pearde
workflow: probe-then-spec
needs:
  - transitions-are-commands
footprint:
  - resources/board/serve.py
  - resources/board/render.py
  - resources/board/view.js
  - resources/board/view.css
  - resources/board/viewtest.js
  - resources/board/plan.py
  - references/parts/view.md
  - references/settings.md
---

# the-page-shows-the-round — the live page says what the session is doing, and which workers are alive

When this is done, a person opening `/board/<name>` sees in the first
screenful what is finished, what is waiting on them, what is in flight and
whether the worker on it is still moving, and what the session has written
down — without opening a terminal.

## Contract

| on the page | is |
|---|---|
| the **now strip** under the title | three doors: `to collect N` · `waiting on you N` · `in flight N` — the top three bands of @references/parts/order.md, each a click into that set. Zero renders the door dimmed, never absent |
| the **round panel** | `prds/.round.md` rendered read-only when it exists: `## Owed` first, then `## Asked`, then the rest. Live like everything else. Absent file, absent panel |
| `silent 42m` on a held row | the newest mtime over the PRD directory and the PRD's footprint union in `repo` is older than `claim-ttl` (`settings.md`, default 30m). Below the limit the row says `held 12m` as today. `scan` prints the same word on the same line — one rule, `plan.py`, read by both, and the one `sweep` acts on |
| the **report** view | `prds/report.md` rendered — the seventh view, ⌘7 |

Every write the page makes goes through `transitions.py` after
`transitions-are-commands`; this PRD adds no writer.

## Rules

- The daemon serves `.round.md` and `report.md` over `GET /round` and
  `GET /report`; both are read from disk on each call, like `/prd`.
- `digest()` already changes on any `.md` under the board, so a `.round.md`
  rewrite swaps the panel in within a second with no new watcher.
- Silence is read off files, never off a process — the board has no way to
  see a worker, and a file that has not moved is the only honest signal.
- The strip and the panel are Lit elements in the light DOM, per
  `view-components`; both are replaceable through `pearde.replace`.

## Files

| file | change |
|---|---|
| `resources/board/plan.py` | `silent` in `standing`/`claim_of`; the word on the scan line; `claim-ttl` |
| `resources/board/serve.py` | `/round`, `/report`, the name from `settings.md`, the redirect |
| `resources/board/render.py` · `view.js` · `view.css` | the strip, the panel, the report view, the silent mark |
| `references/parts/view.md` | the rows above |
| `references/settings.md` | `claim-ttl` |

## Verify

- `viewtest` on the example copy: the strip reads `1 · 1 · 1`; the report
  view renders the copy's `report.md`; a `.round.md` written into the copy
  appears in the panel within two seconds over the served URL.
- With `claim-ttl: 1m` and the copy's mtimes set two minutes back with
  `touch -d`, the `building` row reads `silent` on the page and in `scan`;
  touching a file under it, or a footprint path in its `repo`, flips both to
  `held`.
- `--check` against the snapshot before this PRD differs only in the strip,
  the panel, the report tab and the silent word.

## Report

DONE 24/25 + 1 struck · commit 0db29e9 · probe 50/50 · viewtest --example 36/36 · 47/47 73/73 39/39
