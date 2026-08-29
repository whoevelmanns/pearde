---
complexity: 4
footprint:
  - resources/pearde.py
  - references/parts/handles.md
---

# spec05 — `--help` prints the declaration, and the handles table says where `--dry` applies

`pearde <cmd> --help` for a discovered command prints its doc line and then
`  takes: <list>` read off the callable's `flags` attribute — the same
`Flags` object the refusal formats, so the two cannot drift. `--help`
anywhere on the line, or `-h` first, is help. `handles.md`'s Command column
reads `pearde <cmd> [--dry]` on the fourteen commands that write — `add`,
`defer`, `retry`, `unblock`, `collect`, `claim`, `release`, `answer`, `set`,
`specced`, `refine`, `sweep`, `init`, `settings` — and the paragraph under
the table says what `[--dry]` means and what an undeclared flag gets.

**Already standing from the probe** (uncommitted, in place — pearde.py
hunks at lines 6, 18–21, 328–336; handles.md hunks at 23–24, 26–28, 49–54,
56–58, 62–67): the docstring lines, the `--help` branch reading
`getattr(fn, "flags", None)`, the fourteen `[--dry]` cells and the
paragraph.

**Left:** run the boxes and quote the output. `vision` and `example` — the
two commands `plan.py` exposes through `COMMANDS` — carry no `flags`
attribute, so `--help` prints their doc line alone; they are outside this
PRD's footprint (see the report's findings).

## Acceptance

- [x] For each of `add claim release answer defer retry unblock set sweep specced refine collect brief init settings`, `pearde <cmd> --help` exits 0 and its `takes:` line equals the list `pearde <cmd> … --dyr` names in its refusal
- [x] `pearde release big/second open --help` (the flag last) prints the help, exit 0, and moves nothing
- [x] `grep -c 'pearde [a-z]* \[--dry\]' references/parts/handles.md` prints `14`
- [x] `grep -c '\[--dry\]' references/parts/handles.md` counts the fourteen cells plus the paragraph's one mention — `15`
- [x] `grep -F 'unknown flag --dyr — release takes: --as, --board, --dry' references/parts/handles.md` matches — the prose carries the line the tool prints
- [x] `python3 resources/index.py check` is silent, exit 0, and `one-command` (54) and `the-next-line-runs` (96, once this PRD's commit lands — its line 157 measures `git diff` on `init.py`) hold
      — closed by the orchestrator at collect: the-next-line-runs reads `96 checks · 96 pass` in a worktree of 34a2a37

## Verify and Proof

```sh
for c in add claim release answer defer retry unblock set sweep specced refine collect brief init settings; do python3 resources/pearde.py $c --help; done
grep -c 'pearde [a-z]* \[--dry\]' references/parts/handles.md
bash prds/the-board-runs-itself/one-command/probe/verify.sh </dev/null | tail -1
bash prds/an-unknown-flag-refuses/probe/verify.sh </dev/null | grep -E '^C\.|help|verify:'
```
