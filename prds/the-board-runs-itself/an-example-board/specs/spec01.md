---
complexity: 14
workflow: implement-a-spec
footprint:
  - resources/board/example
  - resources/board/plan.py
  - resources/index.py
  - references/files.md
---

# spec01 — the example board, its copy command, and the two directory rows

`resources/board/example/` is a board of eight PRDs with a row in every band
of the pressure order, `plan.py example <dir>` copies it, and the manifest
names it — and the scout snapshots — as one directory row each, which
`index.py check` reads in both directions.

## What already stands (from the probe, uncommitted in the tree)

- `resources/board/example/` — `README.md`, `prds/settings.md` (`name:
  example`, `language: English`), `landed` (`done`, `commit: e053839`,
  `actual: 2h`), `building` (`claimed`, `claim: worker-building 2026-08-28
  13:49`, `workflow: fix-a-line`, `specs/spec01.md` at 3/5), `finished`
  (`claimed`, 3/3, `prd.md` clean), `asking` (`question`, one `### Q1:` round
  in drill.md's shape, three numbered answers, one `(recommended)`), `next`
  (`open`, `needs: building`), `big` (`open` parent, no `complexity:`) with
  `big/first` (`done`) and `big/second` (`open`); `memos/dates-are-written-not-stamped.md`;
  `workflows/fix-a-line.md` with atomics `find-the-line.md` and
  `change-the-line.md`.
- `resources/board/plan.py` — `EXAMPLE`, `cmd_example(argv)` returning the
  exit code, `COMMANDS["example"]` beside the sibling's `vision` entry, a
  pre-board dispatch in `main()` (the target directory holds no board yet),
  and the docstring line.
- `resources/index.py` — `covered()`, and `check()` reading a row whose
  anchor ends in `/`: it covers every path beneath it, is never reported as
  "not on disk", and prints `lists @<dir>/ — no such directory` when the
  directory is absent.
- `prds/the-board-runs-itself/an-example-board/probe/verify.sh` — 43 checks,
  all measured against a temp copy and a temp manifest.

## What is left

The two manifest rows. The probe could not write `references/files.md`; it
measured the rule through a temp manifest instead. Write the rows (or take
the ones the orchestrator wrote on collect), then run the checks below and
tick them.

## Acceptance

- [x] `references/files.md` carries `| @resources/board/example/ | … |` and `| @resources/scout/snapshots/ | … |`, and no longer carries the per-file `@resources/scout/snapshots/2026-08-25.tsv` row
- [x] `python3 resources/index.py check | grep -E 'resources/(board/example|scout/snapshots)'` prints nothing, with both `.tsv` snapshots on disk
- [x] `touch resources/scout/nope.tsv; python3 resources/index.py check | grep nope.tsv; rm resources/scout/nope.tsv` prints the `is on disk with no row` line for `nope.tsv`
- [x] with a row `@resources/nosuchdir/` added to a temp copy of the manifest and `index.FILES` pointed at it, `index.check()` prints `lists @resources/nosuchdir/ — no such directory` (the probe's harness does exactly this)
- [x] `python3 resources/board/plan.py example "$(mktemp -d)/x"` exits 0 and prints `example: …/x/prds`; run twice on the same dir it exits 2 and says `is not empty`
- [x] `python3 resources/board/plan.py scan <copy>` prints `collect — 1 finished`, `waiting on you — 1`, `in flight — 1 held`, `ready — 1 dispatchable`, `gated — 2`, and `8 PRDs`
- [x] `python3 resources/workflows.py check <copy>/prds` and `python3 resources/memos.py check <copy>/prds` are both silent
- [x] `find resources/board/example -name '.plan.json' -o -name '.round.md' -o -name '.history.jsonl' -o -name '.view.html'` prints nothing, after every harness in this repo has run once
- [x] `bash prds/the-board-runs-itself/an-example-board/probe/verify.sh` ends `43 pass · 0 fail`

## Verify and Proof

```sh
bash prds/the-board-runs-itself/an-example-board/probe/verify.sh
python3 resources/index.py check | grep -E 'resources/(board/example|scout/snapshots)' ; echo "exit=$? (1 is silent)"
D=$(mktemp -d); python3 resources/board/plan.py example "$D/x" && python3 resources/board/plan.py scan "$D/x" | grep -E '^(collect|waiting|in flight|ready|gated)'; rm -rf "$D"
```
