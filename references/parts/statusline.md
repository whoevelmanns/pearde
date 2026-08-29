# The status line

What @resources/statusline.sh renders — the round's numbers, continuously,
for a person watching the terminal rather than the round. Nothing the loop
reads. The state-change line it draws from is @references/parts/progress.md.

It renders the progress line's numbers, plus what the working tree owes and a
link to the board:

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
