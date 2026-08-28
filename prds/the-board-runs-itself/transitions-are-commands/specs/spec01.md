---
complexity: 25
workflow: implement-a-spec
footprint:
  - resources/board/transitions.py
  - prds/the-board-runs-itself/transitions-are-commands/probe
---

# spec01 — `transitions.py`: the eight commands, each a gate, a write, a line and a row

`resources/board/transitions.py` exposes `COMMANDS = {"add", "claim",
"release", "answer", "defer", "retry", "unblock", "set"}` and runs as
`python3 resources/board/transitions.py <cmd> …` until the dispatcher of
`one-command` discovers it. Every command resolves `<prd>` through
`plan.py scan` (so `@<member>/<rel>` writes at the member's real path),
checks the gate the PRD's table names, writes through `edit.py` one
frontmatter line at a time, appends `{"t","prd","from","to"}` to the PRD's
own board's `prds/.transitions.jsonl`, and prints the progress line with
every term computed after the write. A refusal exits 1 on stderr with the
gate named and what would clear it, and writes nothing. The persona is
`--as <id>`, else `PEARDE_AS`, else a refusal.

## What stands from the probe

The whole module is in the tree and the probe's harness closes it:
`bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh`
printed `74 checks · 72 pass · 0 fail · 2 pending on resources/questions.py`
on 2026-08-28. The fixture (`probe/fixture.py`) is the shape of
`an-example-board`'s contract plus `probing`, `stuck`, `broke`, `clash`,
`dangling`, `badround`; when `resources/board/example/` lands, the harness
may build from `plan.py example <dir>` instead and add the six extra PRDs.

Decisions the build made where the contract left room, each visible in the
harness — keep them or change them with the test:

- **leaf** is the planner's definition, `resolve_needs`'s implicit need on
  undone children: a parent whose children are all `done` is claimable.
- **`unblock`** writes `blocked → specced` after checking `needs:` all
  `done`; `claim <prd> <worker>` then takes it through the ordinary gate.
  States.md's `the event lands → claimed` is that pair.
- **`defer`** refuses a PRD carrying `claim:` — release it first.
- **`retry`** moves the `## Failure` section under `## History` as
  `**failed, retried <now>**` plus its text, one `set_body`, then
  `failed → open` and clears `claim:`.
- **`set` without `--force`** runs the gate of the command that owns the
  `(from, to)` edge (`--worker` for a claim edge) and refuses an edge no
  command owns; `--force` skips the gate, writes only `state:`, and the line
  reads `▸ <prd>: <from> → <to> · forced · …`.
- **`add --parent <prd>`** files under a parent — the view's `/new` passes
  one. The slug is `serve.py`'s: lowercase, non-alphanumerics to `-`, 60
  chars; a taken slug is refused, never suffixed.
- The transitions row is written at the PRD's **own** board (`board_path`)
  with the local rel, so a member's memory sits beside its files.
- The `answer` that is not the last one writes the line, moves no state,
  and writes no row; `add`'s row is `"from": null`.

## What is left

- `COMMANDS` values take `argv` (the list after the command name) and return
  the exit code. If `one-command`'s dispatcher settles on a different
  signature, adapt the `_command` wrapper only — the `cmd_*` functions and
  `transition()` stay.
- `.transitions.jsonl` joins the machine-local names in `.gitignore` — the
  file is outside this PRD's footprint; the orchestrator adds the row
  `prds/.transitions.jsonl` beside `prds/.history.jsonl`.

## Acceptance

- [x] `bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh` prints `0 fail`; every `ok` line that exists on 2026-08-28 is still there
- [x] every refusal in the harness exits 1 with the gate named on stderr and the fixture's `git status --porcelain` empty afterwards — the `git diff empty after every refusal` line
- [x] `claim next impl-1` on the gated PRD exits 1 naming `building`; after `set building done --force` it exits 0 and `git diff --numstat` on `next/prd.md` is `2 1` (state changed, `claim:` added)
- [x] the terms `asked … · …% · derived … · open … · …%` on the command's line equal the `progress:` line of `plan.py scan` on the same board after the write, and the line ends `· as <persona>`
- [x] `answer asking Q1`, `Q2`, `Q3` leaves `asking` `open` with three `**Qn** *(answered <ts>)* — …` lines under `## Answers`; a second `answer asking Q1` exits 1 with `answered` in the message
- [x] a command with neither `--as` nor `PEARDE_AS` exits 1 and writes nothing
- [x] `.transitions.jsonl` holds one `{"t","prd","from","to"}` row per state move, and `.history.jsonl` is byte-identical before and after the whole harness
- [x] `set @example/landed open --force --board <master>/prds` moves the member's own `prd.md` and writes its row into the member's `.transitions.jsonl`
- [x] `python3 -c 'import transitions as t; print(sorted(t.COMMANDS))'` from `resources/board` prints the eight names

## Verify and Proof

```sh
bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh
python3 resources/board/transitions.py 2>&1 | head -3      # the usage, exit 2
cd resources/board && python3 -c 'import transitions as t; print(sorted(t.COMMANDS))'
```
