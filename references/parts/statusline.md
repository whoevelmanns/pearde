# The status line

What @resources/statusline.sh renders — the round's numbers, continuously,
for a person watching the terminal rather than the round. Nothing the loop
reads. The state-change line it draws from is @references/parts/progress.md.

It renders the progress line's numbers, plus what the working tree owes and a
link to the board:

```
<dir> <branch> *<dirty> ↑<ahead> ↓<behind> · <model>
▸pearde <rd>/<rn> <rp>% · +<dr>d · open <o> <q>% · <persona> · ▸board
```

- Two rows — sharing one pushes the board off a narrow terminal. No board in
  scope, no second row.
- `<rd>/<rn> <rp>%` is requested work only. `+<dr>d` is the derived PRDs not
  yet `done` — the backlog, not the tree — suppressed at zero, which reads as
  "drained" and not merely "none". Its job is to stop a derived tree growing
  unseen, and **that is why it is the remainder and not the total.** It
  rendered `<dn>`, every derived PRD, until 2026-08-30: a number that can only
  go up, so it could not answer its own question. A dotfiles board showed
  `+99d` with 95 of the 99 closed and was read as 99 things outstanding; this
  repo's own board showed `+7d` with nothing outstanding at all. The progress
  line has room for both halves and carries them as `derived <dd>/<dn>`
  (@references/parts/progress.md); this line has room for one and takes the
  one that moves.
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
- `▸vault` opens the board as an Obsidian vault — a native `obsidian://open`
  URI, so it needs no plugin, key, or daemon, and renders whenever
  `.pearde/.obsidian/` is there (@references/obsidian.md), daemon or no. The
  vault roots at the board, not the repo: Obsidian hides a dot-directory
  inside a vault, so `.pearde/` is invisible from a repo-root vault and
  visible in whole from its own. The URI names the vault by the id
  `obsidian.json` holds for that exact path (`?vault=<id>`) — a path Obsidian
  has not registered opens its ancestor vault instead, which is the repo
  root on a repo that is a vault too; an unregistered board falls back to
  `?path=`. `pearde init` registers it. Same `PRD_STATUS_LINK=off` rule.
