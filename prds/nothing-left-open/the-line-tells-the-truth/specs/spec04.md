---
complexity: 6
footprint:
  - resources/board/plan.py
  - resources/board/transitions.py
  - prds/nothing-left-open/the-line-tells-the-truth/probe/verify.sh
---

# spec04 — `vision` and `example` declare their flags through the one parser

`plan.py` exposed both through `COMMANDS` with no `flags` attribute, so
`pearde vision --bogus` exited 0 with the flag ignored and `pearde example
--bogus` printed a usage line that never named the flag. Both now declare
with the same class every other command declares with and parse with
`transitions.py` `Args`, so an unknown flag is refused before the board is
read, exit 2, naming the flag and the list — `vision`: `--board, --json,
--next, --check`; `example`: none — and `--help` prints that same list.

The class moved: `transitions.py` imports `plan.py` at module level, so
`plan.py` cannot hold a `transitions.Flags` at import time. `Flags` is now
defined in `plan.py` — the root every command module imports — and
`transitions.py` keeps the name as `Flags = planlib.Flags`, so `brief.py`,
`init.py`, `specs.py` and `collect.py` still declare through `trlib.Flags`
unchanged. `Args` stays in `transitions.py`; the two `plan.py` commands
import it lazily at call time. An empty declaration prints `no flags`
instead of an empty list, so `example takes: no flags` reads as a sentence.

## What already stands (the probe built it in place)

- `resources/board/plan.py`: `class Flags` (the body `transitions.py` had,
  `__str__` falling back to `no flags`), `VISION_FLAGS`, `EXAMPLE_FLAGS`,
  `_vision_cli` and `cmd_example` parsing through `translib.Args` and
  printing `pearde vision: …` / `pearde example: …` on `FlagRefused`,
  `.flags` set on both before `COMMANDS`. `_vision_cli` takes `--board
  <path>` and still takes the positional board `plan.py`'s own `main` and
  the `vision-is-first-class` harness use.
- `resources/board/transitions.py`: the class replaced by `Flags =
  planlib.Flags` with a three-line comment. `FLAGS`, `Args`, `run` untouched.
- `an-unknown-flag-refuses/probe/verify.sh` reads 196/196 before and after.
- The probe's section D, 16 checks, green.

## What is left

Nothing to write. `plan.py`'s own `main()` still routes `plan.py vision`
through the loose `--x` filter — that is the script's direct entry, not a
`pearde` command, and the contract names `pearde vision`; it is left as it
was and said here so nobody reads it as an omission.

## Acceptance

- [ ] `python3 resources/pearde.py vision --bogus --board <copy>/prds` exits 2 and stderr is `pearde vision: unknown flag --bogus — vision takes: --board, --json, --next, --check`
- [ ] `python3 resources/pearde.py example --bogus` exits 2 and stderr is `pearde example: unknown flag --bogus — example takes: no flags`
- [ ] `python3 resources/pearde.py vision --help` prints `takes: --board, --json, --next, --check`; `pearde example --help` prints `takes: no flags`
- [ ] `pearde vision --check --board <copy>/prds` and `pearde vision <copy>/prds --check` print the line `python3 resources/board/plan.py vision --check <copy>/prds` prints
- [ ] `pearde vision --board` with no value exits 2 saying `--board takes a value`
- [ ] `pearde example <empty-dir>` still copies the board, exit 0
- [ ] `pearde set --bogus x open --board <copy>/prds` still exits 2 with `set takes: --as, --board, --worker, --force, --dry` — the class moved, the list did not
- [ ] `python3 -c` importing `transitions` and `plan` from `resources/board` shows `transitions.Flags is plan.Flags`
- [ ] `bash prds/an-unknown-flag-refuses/probe/verify.sh` prints `196 checks · 196 pass · 0 fail`

## Verify and Proof

```sh
bash prds/nothing-left-open/the-line-tells-the-truth/probe/verify.sh </dev/null
python3 -c "import sys; sys.path.insert(0,'resources/board'); import transitions, plan; print(transitions.Flags is plan.Flags, plan.VISION_FLAGS, plan.EXAMPLE_FLAGS)"
bash prds/an-unknown-flag-refuses/probe/verify.sh </dev/null | tail -1
```
