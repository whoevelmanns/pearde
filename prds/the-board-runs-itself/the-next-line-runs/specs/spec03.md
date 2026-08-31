---
complexity: 3
workflow: implement-a-spec
footprint:
  - references/parts/handles.md
  - references/parts/personas.md
  - prds/the-board-runs-itself/the-next-line-runs/probe/verify.sh
---

# spec03 — the prose says where the session's persona lives

`personas.md` no longer says the persona is "stored nowhere": it is stored on no
board file, and lives in the session's environment — `PEARDE_AS`, exported as
`engineer` by the install line, read by every command that moves a PRD.
`persona <id>` is `export PEARDE_AS=<id>`; where each command runs in a fresh
shell (an agent's tool call) it is `--as <id>` on the line. The way back to
`engineer` is the install line again. `add` is named as the one command that
runs with neither, and why. `handles.md`'s `add` row says it runs as printed and
what its line ends with; the `who is working` row and the `persona <id>` /
`ask <id>` bullet name the export.

**Already standing from the probe** (in place): two paragraphs in
`references/parts/personas.md` (the "stored on no board file" paragraph and the
one after it; the "way back" sentence under *From candidate to active*), and in
`references/parts/handles.md` the `new PRD` row, the `who is working` row, and
the `persona <id>` and `ask <id>` bullet — nothing else in `handles.md`, which
`workflow-skill` (another session's pending PRD) also has rows in.

**Left for the implementer:** run the harness; tick the boxes. `skills/pearde-persona.md`
and `references/parts/progress.md` still say "no file records it" — true as
written, and outside this footprint; report, do not edit.

## Acceptance

- [x] the `| new PRD` row of `references/parts/handles.md` contains `Runs as printed` and `` `· as engineer (default)` ``
- [x] the `| who is working` row contains `export PEARDE_AS=<id>`; the `persona <id>` and `ask <id>` bullet says `Neither writes a board file` and names `--as <id>`
- [x] `references/parts/personas.md` contains `stored on no board file`, `PEARDE_AS`, `` `· as engineer (default)` ``, `export PEARDE_AS=engineer` and `` `--as <id>` on the line ``, and no longer contains `stored nowhere`
- [x] `git diff references/parts/handles.md` touches only the three places above — one `new PRD` row, one `who is working` row, one bullet
- [x] `python3 resources/index.py check` prints nothing — every `@` anchor in both files still resolves

## Verify and Proof

```sh
bash prds/the-board-runs-itself/the-next-line-runs/probe/verify.sh
# section H's handles.md and personas.md lines are this spec's
grep -c 'stored nowhere' references/parts/personas.md   # 0
git diff --stat references/parts/handles.md references/parts/personas.md
python3 resources/index.py check
```
