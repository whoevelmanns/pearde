---
complexity: 6
footprint:
  - resources/board/collect.py
---

# spec03 — `collect` is the model: parsed by the shared parser, and its dry run prints the `dry ·` line

`collect.py` declares `FLAGS = transitions.Flags(("as", "board", "also",
"also-note", "widen", "snapshot"), ("dry", "fail", "trust"), multi=("also",
"widen"))` and `parse_args` builds its `opts` off `transitions.Args`, so the
refusal is `collect: unknown flag --dyr — collect takes: --as, --board,
--also, --also-note, --widen, --snapshot, --dry, --fail, --trust`, exit 2 —
the list the old `unknown flag --dyr` lacked. Both dry blocks (the ordinary
PRD and the container) keep every line they printed — `would add:`,
`record:`, `message:`, `<rel>: dry — nothing written` — and gain, before the
last one, the `dry · ▸ <rel>: <state> → done · … · round file owed · as
<persona>` line and `would write: prds/<rel>/prd.md · prds/.transitions.jsonl`.
The `commit <sha>` and `record <sha>` terms the real line carries are not on
the dry line: the commits do not exist yet, and a made-up sha is the silent
failure this PRD is about.

**Already standing from the probe** (uncommitted, in place — hunks at lines
80–85, 97–105, 604–618, 860, 1008, 1043, 1077 of the working file): `FLAGS`,
`parse_args`, `dry_line`, the two `dry_line(...)` calls, the
`(Stop, translib.FlagRefused)` catch and `cmd_collect.flags = FLAGS`. The old
`FLAGS`/`VALUED` sets are gone.

**Left:** run the boxes and quote the output.

## Acceptance

- [x] `pearde collect finished --dyr --board <copy>/prds` exits 2 with `collect: unknown flag --dyr — collect takes: --as, --board, --also, --also-note, --widen, --snapshot, --dry, --fail, --trust`
- [x] `pearde collect --help` prints a `takes:` line equal to that list
- [x] `--also <p>` without `--also-note` still exits 2 with `--also needs --also-note`; `--widen a --widen b` collects both paths
- [x] On a copy in its own git repo, `collect finished --trust --dry` exits 0, prints `finished: dry — nothing written` as its last line, and above it `dry · ▸ finished: claimed → done ·` ending `· round file owed · as engineer` and `would write: prds/finished/prd.md · prds/.transitions.jsonl`; the tree is clean and `state:` is still `claimed`
- [x] `collect-is-a-command` (133) and `collect-keeps-its-word` (101) print their baseline counts
- [x] `grep -c '^VALUED = ' resources/board/collect.py` prints `0`

## Verify and Proof

```sh
grep -n '^FLAGS = translib.Flags\|def dry_line\|translib.FlagRefused\|cmd_collect.flags' resources/board/collect.py
bash prds/an-unknown-flag-refuses/probe/verify.sh </dev/null | grep -E 'collect|verify:'
bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh </dev/null | tail -1
bash prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh </dev/null | tail -1
bash prds/the-board-runs-itself/hunks-land-where-they-came-from/probe/verify.sh </dev/null | tail -1
```
