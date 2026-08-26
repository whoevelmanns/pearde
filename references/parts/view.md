# The view

The board is files. The view is how a person reads and works them. Once per
machine:

```sh
python3 @resources/board/serve.py ensure # start if needed, register this board
```

From then on `http://127.0.0.1:8443/board/<name>` is the board, live — within
a second of any file changing it swaps the new payload in **where it stands**:
the rows move, and scroll, zoom, selection and half-typed text do not. Every
registered board is listed at `/`. `PEARDE_PORT` moves the port.

| view          | answers                                                        |
|---------------|------------------------------------------------------------------|
| **timeline**  | what is in front of us — see below                                |
| **board**     | what is where — kanban by state; drag a card to write `state:`    |
| **asks**      | what is waiting on *you* — every `question` and `blocked` PRD. A round in `@references/drill.md`'s format renders as picks: the fork, its three prepared answers as buttons (recommended pre-selected), and an own-answer box per question |
| **list**      | all of it — sortable, filterable, one row per PRD                 |
| **analytics** | how this is going — where the work and weight sit, the est/actual records, weight left over time |
| **memos**     | what the board decided — `prds/memos/`, rendered                  |

**Every number is a door.** A count, a swatch, a bar, a column head — if it
names a set of PRDs, clicking it goes there: `5 waiting on you` opens **asks**,
`189w to the vision` filters the timeline to the critical chain, `137 done`
opens that list, a legend swatch filters by state. Nothing on the page is a
dead end, and the URL follows, so where you are is a link you can send.

**The timeline's x axis is not time** — agents start when work is
dispatchable, so a date on a bar is a staffing guess. The dependency structure
is not. The axis is weight along the **critical path**, and it is the **whole
track** — done work laid out by the same dependency arithmetic to the LEFT of
zero ending at now, the plan to the right, the right edge the vision reached.
Where you are is a place on the track, and the header says what percent of it
is behind you. Parked PRDs — `failed`, `deferred`, the user's own states — sit
at zero: visible, weighed, and scheduled by nothing.

- **★ critical** marks the chain that sets the finish. Weight cut there moves
  the vision closer. Weight cut anywhere else moves nothing.
- **float** is the tail behind a bar: how late it may start before it becomes
  critical.
- **ready now** is the frontier at zero, ordered by how much work each PRD
  unblocks. That ordering *is* the dispatch order. A PRD a worker already
  holds is not on it — it is in **to collect** or nowhere.
- **to collect** leads the frontier: finished work still open on the board.
  It comes first because closing one costs a commit and can open a whole
  frontier, which no dispatch can do. `x` filters to it, `#collect=1` links
  to it.
- a **footprint clash** is a pairwise `after` edge — the lower-priority PRD
  starts when the higher one ends, and nothing else waits with them. There
  are no waves and no rounds: a barrier would hold every unrelated PRD for
  the slowest member of a round, and agents do not work in rounds — each one
  starts the moment its own gates clear.
- The header names the **peak agent count** the fastest path asks for, beside
  what `workers` costs instead. The gap is the decision.
- **dates** (or `v`) draws the same bars on the worker-limited calendar, at
  `gantt-day` weight per day.

**The plan moves while the work does.** The live service reconciles every
board it watches — not only masters — so a bar re-sizes and everything
downstream of it slides within about a second of the file that moved.

A state is written twice per PRD — once on dispatch, once on return — so a
view that reads only states stands still for the whole of the run it is meant
to be showing. The acceptance boxes move continuously, and the view reads
them:

| on the page                | is                                                                  |
|----------------------------|----------------------------------------------------------------------|
| the solid part of a bar    | the fraction of that PRD's acceptance boxes an implementer has closed |
| the ghosted part           | what it has not proven yet. The edge between them moves as boxes close |
| `6/8` in the task column   | the same count, for a PRD in flight. It replaces the weight, which is already what is left |
| a shrinking bar            | a held PRD weighs what is **left** of it, so the chain shortens as the run lands checks |
| **✓** before a name        | every box closed — this one is yours to collect                      |
| `implementer-1 holding 40m`| off `claim:`, in the tooltip and the pane. Counted in the page, so it ticks between board changes |

- The signal is evidence, never a guess: a box is `[x]` because a check ran.
- A worker that ticks nothing shows no progress. That is correct — an
  unproven run has produced nothing the board can schedule around.

**The task column is the board's own tree.** A PRD's children sit indented
under it, a member board is the root of everything under it, and a branch
opens and closes from its `▸`. Two things decide whether a branch is open, in
that order: what you last clicked, and — for every branch you have not touched
— whether any of its subtree falls inside the window you are looking at. Pan
or zoom past a branch and it folds itself away, carrying a thin bar that says
how far its work reaches; pan back and it opens again. A closed branch's row
still reads its whole subtree: how many PRDs, their weight, how many are
critical. Clicking a container's name opens the PRD; clicking its caret folds
it. `group` picks something else to sort by — state, parent, board — and
`collapse all` shuts or opens every branch at once.

The chart is one canvas, drawn virtualised — a 40-PRD board and a 4000-PRD one
cost the same. Greyscale carries the plan — state is ink weight, not hue — and
the only colour on the page is the amber and red of the states that want a
person.

| do | to |
|---|---|
| drag | pan |
| ctrl/⌘+wheel | zoom at the pointer |
| drag the column edge | widen the names |
| `↑` `↓` | move the selection |
| `⏎` | open it |
| ⌘1–6 | switch view |

**Clicking anything opens the PRD**, and the pane writes back:

- title, `state`, `priority`, the body, and a note appended to `## Notes`.
- On a `question` PRD, the round itself — each fork with its three prepared
  answers as radio picks (the recommended one pre-selected) and an own-answer
  box. "answer & reopen" writes the
  picks under `## Answers` (`**Q1** — <text>`) and sets it `open`. A
  `## Questions` section not in @references/drill.md's format falls back to
  raw text and a free textarea.
- The **asks** view is that same round for every waiting PRD at once (⌘⏎
  sends).
- `+ PRD` (or `n`) writes a new one.
- Every write goes through @resources/board/edit.py: one line at a time,
  atomically, frontmatter and body never in the same write.
- A worker's report lands via `POST /report` (`{"board","prd","text"}` →
  `## Report`).

Deep links: `#prd=<rel>` opens one PRD, `#view=asks` a view, `#state=blocked`
a filtered list, `#crit=1` the critical chain, `#collect=1` the finished work
waiting to be closed.

```sh
python3 @resources/board/plan.py plan         # the frontier and the queue, to stdout
python3 @resources/board/plan.py reconcile    # re-order it, keep the anchor
python3 @resources/board/plan.py gantt --open # the same view as one HTML file
python3 @resources/board/plan.py status       # the board, its members, its memos
python3 @resources/board/serve.py wait        # block until the board moves
```

`gantt` writes `prds/.view.html` — the same render, self-contained, no service
needed. It loses only what needs the service: the detail pane's live read and
every edit.

**Being woken, not polling.** `serve.py wait` sleeps in the kernel and exits
the moment anything on the board moves, printing what did. Park it in the
background at session start, and whenever a round ends with work still open.

**What the board keeps.** `prds/.plan.json` is the last plan.
`prds/.history.jsonl` is one row a day — the only memory the board has, and
what the burn-down draws. Both are machine-local and regenerable, so gitignore
them:

```
prds/.plan.json
prds/.history.jsonl
prds/.view.html
```

**Extending it.** A board styles and scripts its own view. Two optional files
at the board root, inlined into the page after everything the skill ships:

| file                 | is                                              |
|----------------------|-------------------------------------------------|
| `prds/view.user.css` | rules that win the cascade over the skill's own  |
| `prds/view.user.js`  | a script that runs against a built page          |

- They belong to the **board**, never to the skill — a skill upgrade leaves
  them untouched, and two boards extend differently.
- A board with neither renders exactly what it renders without this.
- Editing either reloads the open page within about a second. They are board
  content, so the daemon never re-execs for them.
- A `</style>` or `</script>` inside one is escaped, not honoured.
- Gitignore them with the rest, or commit them — the board's call.

`window.pearde` is what a script may use. Nothing else is a contract:

| member      | is                                                       |
|-------------|----------------------------------------------------------|
| `data`      | the enriched payload the page is drawing, `cpm` included  |
| `board`     | the board key this page was rendered for                  |
| `refresh()` | re-fetch the payload and swap it in place                 |
| `apply(p)`  | swap a payload in without fetching                        |
| `onHold(f)` | hold live updates while `f()` returns true                |

```js
// prds/view.user.js — pause the live swap while a dialog of your own is open
pearde.onHold(() => document.body.classList.contains("my-dialog-open"));
```

**Your own element in the page.** `view.user.js` is a module, and Lit ships
with the view, so a board writes a component and the page renders it. The
browser owns that contract — there is no plugin API to learn beyond where an
element goes.

| seam        | where it renders                         |
|-------------|------------------------------------------|
| `toolbar`   | under the numbers, above the view         |
| `sidebar`   | floating at the bottom right of the page  |
| `inspector` | inside the PRD panel, above its buttons   |

- `pearde.slot(name, tag)` renders one registered element into one seam.
- Every slotted element gets the payload as its `data` property, updated on
  every live swap.
- A seam with nothing registered renders nothing — no wrapper, no gap.
- An unknown seam name is ignored, never an error.
- Registering after the page has painted works.

```js
// prds/view.user.js — a panel of your own, fed by the board
import { LitElement, html } from "lit";

class BoardAge extends LitElement {
  static properties = { data: {} };
  render() {
    return html`<b>${this.data?.all?.length ?? 0} PRDs</b>`;
  }
}
customElements.define("board-age", BoardAge);
pearde.slot("sidebar", "board-age");
```

**Replacing a whole view.** A custom element name is unique per document, so
a board cannot define its own `pearde-list` over the page's. It registers an
element of its own and takes the view instead:

```js
// prds/view.user.js — this board draws its own list
import { LitElement, html } from "lit";
class MyList extends LitElement {
  static properties = { data: {} };
  createRenderRoot() { return this; }
  render() { return html`<div>${this.data.all.length} PRDs</div>`; }
}
customElements.define("my-list", MyList);
pearde.replace("list", "my-list");
```

- `board`, `asks`, `list`, `analytics` and `memos` can be replaced. The
  timeline cannot — it is a canvas the plan arithmetic draws.
- The page stops drawing a view it has handed over.
- A replaced view gets the payload as `data` on every swap, like a seam.
- An unreplaceable name is ignored, never an error.

**Checking a change.** `node @resources/board/viewtest.js prds/.view.html`
opens the rendered page in a real browser and reports what it built — Lit
bound, every seam, every view. It needs `playwright-core` installed where you
run it, and exits 2 saying so when it is absent.

`--snap <dir>` writes every view's markup and text. `--check <dir>` compares
against it, so a change to how a view is built is provable rather than
eyeballed — the text a reader sees must not move.

Give it the served URL as well as the file — `node @resources/board/viewtest.js
http://127.0.0.1:8443/board/<name>`. They are different code paths, and a page
that is correct as a file can be broken as a service.

It compares a page against a board in a known state. A PRD that moved changes
what the views draw, and every check fails for that reason alone. Snapshot the
board, change the code, compare — never across a round.
