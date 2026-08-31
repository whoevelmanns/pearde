---
complexity: 6
workflow: implement-a-spec
footprint:
  - resources/board/transitions.py
  - prds/the-board-runs-itself/the-next-line-runs/probe/verify.sh
---

# spec01 — `add` runs with no persona named, and every other transition refuses naming the install line

`transitions.py` resolves the persona once, in `run()`. With neither `--as <id>`
nor `PEARDE_AS`, `add` files the PRD and its line ends `· as engineer (default)`
— a new PRD has no earlier line a default could rewrite. Every other command
(`claim` `release` `answer` `defer` `retry` `unblock` `set` `sweep`) refuses,
and the refusal names `PEARDE_AS` and the line `install --apply` prints:
`export PEARDE_AS=engineer`.

**Already standing from the probe** (built in place — a resolver has no meaning
outside the function it lives in): the docstring paragraph at the top of
`resources/board/transitions.py`, the constants `DEFAULT_PERSONA` / `DEFAULTS_FOR`
/ `INSTALL_LINE` after `PARKED`, and `persona_default()` immediately before
`run()`, which `run()` calls. The hunk is additive and disjoint from `record()`,
which a sibling PRD (`tokens-per-transition`) is adding counters to — re-read the
file before any further edit and leave one untouched line between the two.

**Left for the implementer:** re-read `transitions.py` against the live tree,
run the harness, tick the boxes. Nothing else in the file moves. The status
line's reader (`resources/statusline.sh`, `grep -o '▸[^"]*· as [a-z][a-z0-9-]\{1,15\}'`)
stops at the id, so ` (default)` never reaches the terminal — section D of the
harness proves it and no change there is owed.

## Acceptance

- [x] `python3 resources/board/transitions.py add "A first title" --board <copy of resources/board/example/prds>` with `PEARDE_AS` unset and no `--as` exits 0, files `a-first-title/prd.md` with `state: open`, and prints one line ending ` · as engineer (default)`
- [x] the same `add` with `--as skeptic`, or with `PEARDE_AS=mentor`, ends ` · as skeptic` / ` · as mentor` with no `(default)`; `--as` beats `PEARDE_AS`; a blank `PEARDE_AS` counts as unset
- [x] each of `claim` `release` `answer` `defer` `retry` `unblock` `set` `sweep` with neither exits 1, writes nothing to `.transitions.jsonl`, and its stderr names `PEARDE_AS`, `export PEARDE_AS=engineer` and `install --apply`
- [x] `set … --force` with neither still exits 1 — force skips the gate, not the persona
- [x] `bash resources/statusline.sh` fed a transcript whose last `▸` line ends `· as engineer (default)` renders `engineer` and no `(`
- [x] `git diff resources/board/transitions.py` shows hunks only in the module docstring, the constants after `PARKED`, and `persona_default`/`run` — `record()` untouched

## Verify and Proof

```sh
bash prds/the-board-runs-itself/the-next-line-runs/probe/verify.sh
# sections A–D and G are this spec's; the count line closes it: `96 checks · 96 pass · 0 fail`
git diff --stat resources/board/transitions.py
python3 -c "import ast; ast.parse(open('resources/board/transitions.py').read())"
```
