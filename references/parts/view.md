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

**One page, read top to bottom.** There are no tabs. The page opens with what
is up, then the plan, then the sections below in this order, and the bar in the
header is anchors that jump to one — it never hides a section, and an anchor
landing on a folded one opens it. ⌘1–7 jump the same way.

| # | section       | answers                                                        |
|---|---------------|------------------------------------------------------------------|
| 1 | **what's up** | what the board is doing and what is next, in prose — `prds/report.md`'s title, lede, `## In work` and `## Planned`, each cut to two or three whole sentences. A renderer, never an author. Beside it, how old the file is, off its modification time and not the dateline inside it; past a day the line says `stale` and carries the class. No file, one line naming `pearde report` |
| 2 | **timeline**  | what is in front of us — see below                                |
| 3 | **board**     | what is where — kanban by state; drag a card to write `state:`    |
| 4 | **analytics** | how this is going — where the work and weight sit, the est/actual records, the machine-wide hours-per-weight fit, weight left over time, and what a transition costs: calls per transition over the last thirty, refusals per session, both off the guard's count (@references/parts/guard.md). Calls are the proxy for tokens, named as such; no guard state at all reads `no guard`, never zero |
| 5 | **asks**      | what is waiting on *you* — every `question` and `blocked` PRD, and beside them the answered panel. A round in `@references/drill.md`'s format renders as picks: the fork, its three prepared answers as buttons (recommended pre-selected), and an own-answer box per question. An answered question leaves the cards at once and appears in the panel, newest first |
| 6 | **list**      | all of it — sortable, filterable, one row per PRD                 |
| 7 | **memos**     | what the board decided — `prds/memos/`, rendered                  |
| 8 | **report**    | the same file in full, folded — section 1 is its opening. ⌘7 |

**Three of those fold.** `list`, `memos` and `report` are archives, not
status: measured on a 41-PRD board they are 4038px of a 7065px page. Each
keeps its anchor and its heading in the flow and renders collapsed behind a
summary that says what is inside — `41 PRDs · every state, every weight`,
`13 on record · newest: …` — and opens on a click or on its anchor. What
folds is the body, by the reader's choice; nothing is hidden by the bar.
**Every section draws on the first paint**, folded or not, so nothing on
this page is waiting for a click to exist.

**The now strip is the first thing under the title**, on every view: three
doors — `to collect N` · `waiting on you N` · `in flight N` — the top three
bands of @references/parts/order.md, each a click into that set (the timeline
filtered to collect, the list filtered to the `hot` band, the list filtered to
the `held` band). Zero renders the door dimmed, never absent, so the strip is
the same shape on every board and the eye learns where to land. When a worker
in flight has gone silent the door says how many.

**Nothing that is git-ignored is rendered for a person.**
A file git ignores is machine scratch: `prds/.round.md` is one session's own
memory (@references/parts/round.md), `prds/.plan.json` and `prds/.history.jsonl`
are the board's. Each is true only at the instant it was written and each is
written in the board's own vocabulary — states, footprints, commit shas — which
is the one register @@report forbids in the document a person reads. The view
draws tracked files and nothing else. That rule is prose, and prose is not a
mechanism: what would enforce it is a check that `git check-ignore -q` refuses
every path the view fetches, and no such check exists.

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
is behind you. Once `calibrate` has fitted the machine's hours-per-weight
(see @references/parts/order.md), every weight on the page prints as tuned
real hours — header, tiles, vision pill, axis, drawer; before the first fit
they print as raw weight units. Parked PRDs — `failed`, `deferred`, the user's own states — sit
at zero: visible, weighed, and scheduled by nothing. Under the numbers the
page prints the one sentence `prds/vision.md` declares — the payload's
`vision.purpose`, empty on a board with no vision, and then no line.

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

**The y axis is pressure, not the schedule.** Read top to bottom by start
date, the one PRD asking you a question sits three hundred rows down, and a
board you have to hunt through is a board nobody glances at. Rows stack in the
pressure order — to collect, waiting on you, in flight, ready now, gated,
parked, landed — which is @references/parts/order.md's ranking and the same one
`plan.py scan` prints a round in. The top of the chart and the top of the scan
are one claim. Inside a band the plan arithmetic breaks the tie: earliest
start, then critical, then the size of the door it opens.

The bands apply inside every grouping, and in **tree** a branch is as pressing
as the most pressing thing inside it — a folded parent holding one `question`
rises carrying it. Tree is one click away and it is not what a board opens on:
under it a container's aggregate track and the landed work inside an early
branch sit above the run that is happening right now.

**A name rides its own work.** There is no column of names to correlate
against: a PRD's name is written inside its pill where the pill can hold it,
and floating just off the end where it cannot — off the *start* instead when
the end is against the right edge — with what is left of it beside it, boxes
while a worker holds it and weight otherwise. Ink inside a pill is chosen from
that pill's own colour, so it is legible on a near-white `open` and a
near-black `specced` alike.

Two names can want one patch of canvas, and at six pixels a row most of them
do. Rows are in the pressure order, so placement is greedy from the top: what
is to collect, waiting on you, in flight and ready claim their names first, and
the settled tail is what loses one to a collision. A row without its name keeps
its bar, its hover and its click — the name is the cheapest thing on a row to
drop and the only one that can go without the work going with it.

`names` (or `t`) brings the old column back for when a sorted list of names is
the thing you want; it slides in rather than appears, and the plan re-lays out
under it. At dense row heights that column staggers into two, each name still
on its own row's centre line and its row banded behind it, because the band is
what pairs a name to a bar.

**Both axes fit the window.** `ppu` fits the weight across. Down, the **row
rail** on the plot's own left edge is a slider between the two honest answers:
at the top every row is the height it is meant to be read at and the board
scrolls; at the bottom the whole board is on the screen and the rows are as
short as that takes. Neither end is right for every board, which is why it is a
rail and not a rule. It runs the axis it scales — up is the tall row, and the
two end caps are the legend: two fat rows above, four thin ones below. Drag it
anywhere, wheel over it, click an end, or arrow the thumb; hold shift for the
fine grain. Hovering it, and every move of it, says the pitch in pixels and how
many of the rows that puts on the screen. `fit` (or `f`) puts the horizontal
half back after a zoom. Row height still has two clamps — a
ceiling so four PRDs are not four fat stripes, and a floor below which a bar
stops being a shape, past which the remainder scrolls.

**Two cards, not one.** The plan and **focus** sit side by side with air
between them, and focus pushes in and out from the right — `focus` (or `L`).
The plan takes the width back as it goes. The stage takes whatever height the
page has left under it, measured rather than guessed, so a wrapped toolbar
never pushes the legend off the bottom and never leaves dead page under it.

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
| `6/8` beside a name        | the same count, for a PRD in flight. It replaces the weight, which is already what is left |
| a shrinking bar            | a held PRD weighs what is **left** of it, so the chain shortens as the run lands checks |
| **✓** before a name        | every box closed — this one is yours to collect                      |
| `implementer-1 holding 40m`| off `claim:`, in the tooltip and the pane. Counted in the page, so it ticks between board changes |
| `silent 42m` beside it     | nothing under the PRD directory or its footprint union in `repo` has moved for longer than `claim-ttl` (`settings.md`, default 30m). Below the limit the row says only `holding`. In amber, in the column's meta and on the bar's label too: the one word in the column that asks for a person. `scan` prints the same word on the same line — one rule, `silent_of` in @resources/board/plan.py, read by both and the one `sweep` acts on. Read off files, never off a process: the board cannot see a worker, and a file that has not moved is the only honest signal. A PRD to collect is never silent — its worker finished |

- The signal is evidence, never a guess: a box is `[x]` because a check ran.
- A worker that ticks nothing shows no progress. That is correct — an
  unproven run has produced nothing the board can schedule around.

**With `names` on, that column is the board's own tree** — under `group: tree`,
which is one click from the urgency order a board opens on. A PRD's children sit indented
under it, a member board is the root of everything under it, and a branch
opens and closes from its `▸`. Two things decide whether a branch is open, in
that order: what you last clicked, and — for every branch you have not touched
— whether any of its subtree falls inside the window you are looking at. Pan
or zoom past a branch and it folds itself away, carrying a thin bar that says
how far its work reaches; pan back and it opens again. A closed branch's row
still reads its whole subtree: how many PRDs, their weight, how many are
critical. Clicking a container's name opens the PRD; clicking its caret folds
it. `group` picks what the rows stack by — `urgency` (the pressure order, flat,
and what a board opens on), `tree`, state, parent, board — and `collapse all`
shuts or opens every branch at once. Pressure bands inside whichever is picked.

The chart is one canvas, drawn virtualised — a 40-PRD board and a 4000-PRD one
cost the same. Greyscale carries the plan — state is ink weight, not hue — and
the only colour on the page is the amber and red of the states that want a
person.

| do | to |
|---|---|
| drag | pan |
| ctrl/⌘+wheel | zoom at the pointer |
| drag the column edge | widen the names, when `names` is on |
| drag the left rail | row height — wheel it too, shift for fine |
| `↑` `↓` | move the selection |
| `⏎` | open it |
| ⌘1–7 | switch view |

**Clicking anything opens the PRD**, and the pane writes back:

- title, `state`, `priority`, the body, and a note appended to `## Notes`.
- On a `question` PRD, the round itself — each fork with its three prepared
  answers as radio picks (the recommended one pre-selected) and an own-answer
  box. "answer & reopen" writes the
  picks under `## Answers` (`**Q1** — <text>`) and sets it `open`. A
  `## Questions` section not in @references/drill.md's format falls back to
  raw text and a free textarea.
- A `blocked` PRD's wall renders the same way when it is written as a round.
  The heading is matched by prefix, so `## Blocked on a human with a browser`
  is the same section as `## Blocked`.
- **Each question answers on its own.** `answer Q1` writes that one under
  `## Answers` and leaves the rest of the round open. The PRD only goes back
  to `open` when nothing in the round is left unanswered.
- Which questions are already answered is read off `## Answers`, not
  remembered by the page — a redraw, a reload and a second reader all agree,
  and nothing is answered twice.
- An answer is written as `**Q1** *(answered 2026-08-28 14:22)* — <the
  decision>`. The id opens the line and the decision follows the dash, as
  before; the stamp is what the answered panel orders by. A line written
  before the stamp existed still reads — it sorts under the dated ones.
- **"take the recommended"** picks the analyst's recommendation on every
  question that carries one and sends in the same click. It appears only when
  the round recommends something.
- The **asks** view is that same round for every waiting PRD at once (⌘⏎
  sends). It renders exactly what the inspector renders — the same picks, the
  same prose, the same buttons — because both build from the same parse.
- **The answered panel** is the right half of that view: every question the
  board has settled, newest answer first, each row the question, the decision
  and the PRD it belongs to — click one to open that PRD. It is read over
  `GET /answers` out of the PRDs themselves, so it holds answers from PRDs
  that have long since reopened, not only from the ones still asking. A
  question answered here leaves its card in the same motion, so the cards
  hold open forks only and going through a round is a list that empties.
- `+ PRD` (or `n`) writes a new one.
- Every write goes through @resources/board/edit.py: one line at a time,
  atomically, frontmatter and body never in the same write.
- A worker's report lands via `POST /report` (`{"board","prd","text"}` →
  `## Report`).
- `GET /report` serves `prds/report.md` as `{"text": <file or null>}`, read
  from disk on each call like `/prd`. `/round` is gone: the page dropped the
  panel, and a route nothing fetches is a door to nowhere.

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
what the burn-down draws. `prds/.transitions.jsonl` is one row a transition,
appended by the transition commands, carrying the guard's count for the window
before it — what the cost series draw. All are machine-local, so gitignore
them:

```
prds/.plan.json
prds/.history.jsonl
prds/.transitions.jsonl
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

- `board`, `asks`, `list`, `analytics`, `memos` and `report` can be
  replaced. The timeline cannot — it is a canvas the plan arithmetic draws.
- `now` and `whatsup` — the door strip and the prose section above the plan —
  are replaced the same way: `pearde.replace("now", "my-now")` puts the element
  in the strip's place and hands it the payload on every swap.
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
