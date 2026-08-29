---
complexity: 14
footprint:
  - resources/board/transitions.py
---

# spec01 — one declaration, one parser, and `--dry` on every verb of transitions.py

`transitions.py` carries `Flags` (what one command takes), `FLAGS` (the
nine verbs' declarations), `Args` (the one parser every command module
imports) and `FlagRefused` (exit 2, raised before the board is read). Every
verb that writes — `add`, `claim`, `release`, `answer`, `defer`, `retry`,
`unblock`, `set`, `sweep --apply` — takes `--dry`: the gate runs, the line
the real run would print is printed with `dry ·` in front, `would write:`
names every path, nothing moves. The dry line is exact because `dry_line`
moves the state on the scan's dict and holds it in `plan.scan`'s place for
the one call that prints the line.

**Already standing from the probe** (uncommitted, in place — the hunks at
lines 21–29, 91–95, 255–348, 539–569, 585, 627, 646, 668–686, 708, 723–725,
750, 759, 830–832, 847–943 of the working file; the foreign `asked → done`
hunks at 504 and 517 are not this PRD's): the docstring paragraph, `FlagRefused`,
`transition(..., dry=False)` with its dry branch, `dry_line`, `fake_prd`,
`shown_path`, `say_dry`, `add(..., dry=False)`, the dry branch of `cmd_answer`
(the three outcomes on a scan holding the answer in memory — the transition
gate is not re-run, since it would refuse an answer that is not on disk),
`cmd_retry`'s and `cmd_sweep`'s dry branches, `Flags`/`DRY`/`FLAGS`/`Args`,
`run` catching `FlagRefused` → 2, `_command` setting `call.flags`.

**Left:** run the boxes and quote the output. A valued flag whose next token
starts with `--` is refused (`--worker takes a value`) — keep that; the old
parser ate `--board` as the worker's name.

## Acceptance

- [x] On a copy of the example board, `pearde release <parked> open --dyr --board <copy>/prds` exits 2, stderr carries `unknown flag --dyr — release takes: --as, --board, --dry`, and `git -C <copy> status --porcelain` is empty afterwards
- [x] The same line with `--board <path that does not exist>` exits 2 with the same message — the refusal is before any read of the board
- [x] `env -u PEARDE_AS pearde release <prd> open --dyr --board <copy>/prds` exits 2 on the flag, not 1 on the persona
- [x] For each of `add`, `claim`, `release`, `answer`, `defer`, `retry`, `unblock`, `set`, `sweep`: `--dry` exits 0, stdout has one line starting `dry · ` and one starting `  would write: `, and the copy's tree is clean after it
- [x] For each of those verbs the real run's last line equals the `--dry` line with `dry · ` removed — the fixture chain in `prds/an-unknown-flag-refuses/probe/verify.sh` section D
- [x] `claim --dry` lists `prds/.claims/<rel>/` beside `prd.md` and `.transitions.jsonl` when the board is in a git repo; `answer --dry` lists `prds/.claims/riders`
- [x] `add "Dry test" --dry` prints a line whose `open` count includes the new PRD and leaves no `prds/dry-test/` behind
- [x] `set <prd> open --worker --board <copy>/prds` exits 2 with `--worker takes a value — set takes: …`
- [x] `grep -c 'call.flags = FLAGS\[name\]' resources/board/transitions.py` prints `1` — the declaration rides the callable `pearde.py` discovers
- [x] `prds/.transitions.jsonl` on the real board has the same line count before and after every command above ran against copies

## Verify and Proof

```sh
grep -n 'class Flags\|^FLAGS = {\|class FlagRefused\|def dry_line\|def say_dry' resources/board/transitions.py
bash prds/an-unknown-flag-refuses/probe/verify.sh </dev/null | grep -E '^(A|B|C|D)\.|verify:'
bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh </dev/null | tail -1
bash prds/a-parked-prd-comes-back/probe/verify.sh </dev/null | tail -1
bash prds/the-board-runs-itself/tokens-per-transition/probe/verify.sh </dev/null | tail -1
```
