---
complexity: 12
workflow: implement-a-spec
footprint:
  - references/templates/vision.md
  - references/parts/order.md
  - references/parts/board.md
  - references/parts/master.md
  - resources/doctor.sh
  - references/files.md
  - index.md
---

# spec02 — the file has a template, the prose names it, and `doctor` checks it

`references/templates/vision.md` is the file `init` will write, with
`terminals:` and `edges:` commented out. `order.md` says the axis is
`prds/vision.md` and how depth is counted; `board.md` shows the file in the
layout; `master.md` says how a master's terminals address members and its
own PRDs. `doctor` gains a `vision` row — `off` with no file, `ok` with the
summary, `broken` naming every terminal or edge end that resolves to no PRD.
The manifest and the index carry the template.

## What stands from the probe

- `references/templates/vision.md` — written; `read_vision` on a copy of it
  returns the placeholder sentence, no terminals, no edges (the commented
  lines parse as nothing).
- `references/parts/order.md` — the sentence naming `.vision.json` and
  `vision.py` is replaced by the `prds/vision.md` paragraph: terminals,
  depth over `needs:` plus `edges:`, done costs no hop, parent after
  children, off-axis, the scan line, `pearde vision`, and that a board with
  no `terminals:` prints none of it. The three committed harnesses that
  read parts files are unchanged (`47/47`, `73/73`, `39/39`).
- `references/parts/board.md` — `vision.md` in the layout block, one bullet
  under it.
- `references/parts/master.md` — a **The vision.** paragraph before **The
  master is where you work.**: `@<member>/<rel>` as `needs:`, plus
  `@<name>/<rel>` for the master's own PRD; the master reads only its own
  file.
- `resources/doctor.sh` — the `vision` block between `members` and
  `origin`, reading `plan.py vision --check`: exit 0 prints the summary as
  `ok`, exit 1 prints `broken` with one indented line per dangling name and
  the fix line. On this repo's board today: `vision ok 1 terminal · 14 on ·
  3 off · longest chain 5`.

## What is left

- `references/files.md`: one row `| @references/templates/vision.md | one
  board's destination — the vision, its terminals, its edges |` under the
  templates section.
- `index.md`: `@references/templates/vision.md` appended to the `@@order`
  row, to `@@templates`, and to `@@board`. Until then `python3
  resources/index.py check` prints the template's line — the one line this
  PRD adds to a check that other uncommitted work is also reddening.
- No `loop.md` change: the loop reads `scan`, and the scan line is the
  whole change.

## Acceptance

- [x] `python3 resources/index.py check` prints no line naming `references/templates/vision.md`
- [x] `grep -c 'templates/vision.md' index.md` prints at least `3` (`@@order`, `@@templates`, `@@board`) and `grep -c '@references/templates/vision.md' references/files.md` prints `1`
- [x] `grep -c 'vision.py' references/parts/order.md` prints `0` and `grep -c 'The axis is `prds/vision.md`' references/parts/order.md` prints `1`
- [x] `grep -c 'vision.md' references/parts/board.md` prints at least `2` (the layout line and the bullet)
- [x] `grep -c '@<name>/<rel>' references/parts/master.md` prints `1`
- [x] `bash resources/doctor.sh <a temp dir holding a copy of resources/board/example with a vision.md naming `- nowhere` under terminals>` prints a line beginning `vision      broken` followed by an indented `terminal nowhere names no PRD`; with `terminals: [big]` the row reads `vision      ok      1 terminal · 2 on · 4 off · longest chain 1`; with no `vision.md` it reads `vision      off`
- [x] `bash prds/workflows-on-the-board/workflow-attach/probe/verify.sh`, `…/workflow-improve/probe/verify.sh` and `…/workflow-reader/verify.sh` still print `47/47`, `73/73` and `39/39`

## Verify and Proof

```sh
python3 resources/index.py check | grep -c 'templates/vision.md'
grep -c 'templates/vision.md' index.md
grep -c '@references/templates/vision.md' references/files.md
grep -c 'vision.py' references/parts/order.md
grep -c 'vision.md' references/parts/board.md
grep -c '@<name>/<rel>' references/parts/master.md
D=$(mktemp -d); cp -R resources/board/example/. "$D"
bash resources/doctor.sh "$D" | grep -A1 '^  vision'
printf -- '---\nvision: x\nterminals:\n  - big\n---\n' > "$D/prds/vision.md"
bash resources/doctor.sh "$D" | grep '^  vision'
printf -- '---\nvision: x\nterminals:\n  - big\n  - nowhere\n---\n' > "$D/prds/vision.md"
bash resources/doctor.sh "$D" | grep -A1 '^  vision'
rm -rf "$D"
```
