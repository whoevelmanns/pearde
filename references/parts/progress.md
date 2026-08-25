# Progress line

The one line printed on every state change, term by term.

Print on EVERY state change:

```
▸ <prd>: <from> → <to> · asked <ad>/<an> · <ap>% · derived <dd>/<dn> · open <o>/<n> · <q>% · ready <r> · blocked <b> · collect <c> @<w> workers · as <persona>
```

| term       | is                                                                        |
|------------|---------------------------------------------------------------------------|
| weight     | the PRD's `complexity`; missing counts at the average of scored PRDs, `weight-default` if none |
| `<ad>/<an>`| `done` / all `origin: requested` — **the deliverable**                     |
| `<ap>`     | Σ weight(done, requested) / Σ weight(all requested). `failed` counts as remaining |
| `<dd>/<dn>`| `done` / all `origin: derived`. Counts, never weighted                      |
| `<o>`      | PRDs still `open`, both origins                                             |
| `<q>`      | `<o>/<n>`. A count — an `open` PRD is not scored yet                        |
| `<n>`      | the states in the @references/parts/states.md table only                   |
| a master   | every member's PRDs and its own, one set. A member's PRD is named `@<member>/<prd>` |
| `<r>`      | **ready** — dispatchable right now: `needs:` all `done`, no footprint clash with a `claimed` PRD |
| `<b>`      | **blocked** — not `done`, not ready. Name what holds the largest group      |
| `<c>`      | **to collect** — finished work still open: every acceptance box `[x]`, state not yet `done`. Omitted at zero |
| `as <persona>` | who is working, the id — @references/parts/personas.md. **Always last, never omitted**, because it is the only record of it |

- **`asked` is the answer to "how far along are we".** Derived PRDs enlarge
  the denominator with work the user never requested: a board 90% through its
  deliverable reads 63% combined. Report both or neither.
- Omit the `derived` term on a board that has none.
- When the tripwire is live, say so on the line and in the round.
- `<q>` and `<ap>` do not sum to 100 — untouched board vs requested work done.
- A parked PRD is in neither numerator nor denominator. Name it in the report.
- **`ready` and `blocked` are the actionable pair.** A board with 20 PRDs left
  and `ready 1` is not slow, it is serial. The round says which dependency or
  which footprint holds the other 19 — a fact a reader can act on.
- **`collect` above zero is the board waiting on itself.** The work is done
  and the states have not caught up, so `ready` is under-reporting by
  whatever those PRDs unblock. Close them before reading the rest of the
  line — step 6 of @references/parts/loop.md.
- **`as <persona>` is stored nowhere else.** A persona is session state and is
  written to no file, so this line is the only place it is recorded — which is
  why it is never omitted, not even when it has not changed, and why a
  `persona <id>` switch prints its own line in the same `▸ … · as <id>` form
  even though no state moved. @resources/statusline.sh reads the last one out
  of the session transcript; a round that leaves it off leaves the terminal
  showing the persona before it.

@resources/statusline.sh renders the same numbers continuously, plus what the
working tree owes and a link to the board:

```
<dir> <branch> *<dirty> ↑<ahead> ↓<behind> · <model>
▸pearde <ad>/<an> <ap>% · +<dn>d · open <o> <q>% · <persona> · ▸board
```

- Two rows — sharing one pushes the board off a narrow terminal. No board in
  scope, no second row.
- `<ad>/<an> <ap>%` is requested work only. `+<dn>d` is the derived count,
  suppressed at zero — its job is to stop a derived tree growing unseen.
- `*<dirty>` is uncommitted entries. `↑`/`↓` is commits against upstream. No
  upstream reads `no-upstream`, not `↑0`.
- `<persona>` is who is working, read from the session's own transcript — the
  last `· as <id>` a round printed, matched with the `▸` in front of it so
  prose cannot supply one. Nothing on disk holds a persona, and the status
  line runs in its own process, so the printed line is the only channel there
  is. Before the first round it is absent rather than `engineer`: an unstated
  persona is `engineer` anyway, and rendering a default nobody chose reads as
  an answer. It is the id, not the name, because the id is what you type back.
- `▸board` is an OSC-8 hyperlink to the live view. `PRD_STATUS_LINK=off`
  prints the label bare. Optional.
