---
complexity: 6
footprint:
  - resources/board/specs.py
---

# spec02 — `specced` and `refine` declare their flags and take `--dry`

`specs.py` declares `FLAGS` — `specced`: `--as, --board, --blast, --workflow,
--check, --dry`; `refine`: `--as, --board, --dry` — and parses through
`transitions.Args`, so `--dyr` is refused with that list, exit 2, before
`find_board`. `specced --dry` runs every check the real run runs (the files,
the limits, the state) and then prints the transition line the real run
would print on a scan holding `complexity`, `blast-radius`, `workflow`,
the cleared `claim` and `specced`; `refine --dry` reads the table off stdin,
prints one `dry · <rel>/<child>: open` per child it would create, the
parent's transition line on a scan holding the children (`fake_prd`), and
one `would write:` naming every child `prd.md`, the parent and the row.

**Already standing from the probe** (uncommitted, in place — hunks at lines
4–5, 19–22, 277–291, 381–405, 433–439, 445, 455–457, 463 of the working
file): the docstring, `FLAGS`, the dry branches of `specced` and `refine`,
`_command` parsing through `trlib.Args`, catching `trlib.FlagRefused` → 2
and setting `call.flags`. The private `Args` class is gone.

**Left:** run the boxes and quote the output.

## Acceptance

- [x] `pearde specced <prd> --dyr --board <copy>/prds` exits 2 with `unknown flag --dyr — specced takes: --as, --board, --blast, --workflow, --check, --dry`; `pearde refine <prd> --dyr --board <copy>/prds </dev/null` exits 2 naming `--as, --board, --dry`
- [x] `pearde specced --help` and `pearde refine --help` print `takes:` lines equal to those two lists
- [x] On a copy where `building` is `analyzing`: `specced building --blast mid --dry` exits 0, prints `dry · ▸ building: analyzing → specced ·…` and `would write: prds/building/prd.md · prds/.transitions.jsonl`, and `complexity:`/`blast-radius:`/`state:` in `prds/building/prd.md` are unchanged
- [x] The real `specced building --blast mid` then prints the dry line without its prefix, and writes `blast-radius: mid`
- [x] On a copy where `big/second` is `analyzing`: `refine big/second --dry` with a two-row `## Split` table on stdin prints `dry · big/second/alpha: open`, `dry · big/second/beta: open · needs alpha`, `dry · ▸ big/second: analyzing → open ·…` and `would write: prds/big/second/alpha/prd.md · prds/big/second/beta/prd.md · prds/big/second/prd.md · prds/.transitions.jsonl`, and no child directory exists afterwards
- [x] The real `refine` then prints the dry transition line without its prefix and leaves both children on disk
- [x] `specced <prd> --check --dry` behaves as `--check`: exit 0, nothing written
- [x] `grep -c '^class Args' resources/board/specs.py` prints `0`

## Verify and Proof

```sh
grep -n '^FLAGS = {\|trlib.Args(argv, FLAGS\[name\]\|trlib.FlagRefused\|if args.dry:' resources/board/specs.py
bash prds/an-unknown-flag-refuses/probe/verify.sh </dev/null | grep -E 'specced|refine|verify:'
bash prds/the-board-runs-itself/specced-is-a-command/probe/verify.sh </dev/null | tail -1
```
