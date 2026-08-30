---
complexity: 6
footprint:
  - resources/board/collect.py
  - prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh
  - prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh
  - prds/nothing-left-open/the-line-tells-the-truth/probe/verify.sh
---

# spec01 — `collect` refuses without a persona, through the one refusal `transitions.py` raises

`collect` is the verb that commits, and its `· as <id>` is the record of who
acted. Today `collect.py` `parse_args` fills `as` with `"engineer"` when
`--as` is absent and never reads `PEARDE_AS` at all. After this, the persona
resolves the way `transitions.py` `run` resolves it — `--as`, else
`PEARDE_AS`, else `persona_default("collect")`, which raises the one refusal
string every transition prints — and `cmd_collect` exits 1 on it, having
read nothing. `--snapshot` refuses the same way: it is the same command.

## What already stands (the probe built it in place)

- `resources/board/collect.py` `parse_args`: `persona = (a.opt.get("as") or
  os.environ.get("PEARDE_AS", "")).strip()`; `"as": persona or
  translib.persona_default("collect")`.
- `resources/board/collect.py` `cmd_collect`: a third `except
  translib.Refused` after the `FlagRefused` one — `collect: refused — <e>`
  on stderr, return 1. `FlagRefused` is listed first, so an unknown flag
  still exits 2.
- The probe's section A, 15 checks, green.

## What is left

The two committed collect harnesses call `collect` through a `run()` helper
that names no persona — `collect-keeps-its-word/probe/verify.sh:41` and
`collect-is-a-command/probe/verify.sh:132`, both `( cd "$D" && python3
"$COLLECT" --board "$D/prds" "$@" )`. The contract moves them from 101/101
and 133/133 to 41/101 and 49/133. The repair is one word in each helper:
`PEARDE_AS=engineer python3 "$COLLECT" …` — the helper names the persona
the harness always meant, and the `--as skeptic` line at
`collect-is-a-command:313` still overrides it because `--as` wins over the
environment. The probe proved the repair by running both harnesses with the
variable exported; the rule each asserts did not move.

## Acceptance

- [ ] On a copy of the example board, `env -u PEARDE_AS python3 resources/board/collect.py finished --board <copy>/prds` exits 1, stderr holds `collect: refused — persona: \`--as <id>\` on the line, or PEARDE_AS in the environment` and `export PEARDE_AS=engineer`, and `git status --porcelain` in the copy is unchanged
- [ ] `env -u PEARDE_AS python3 resources/board/collect.py --snapshot building --board <copy>/prds` exits 1 with the same refusal
- [ ] `PEARDE_AS=skeptic python3 resources/board/collect.py finished --board <copy>/prds --dry --trust` prints a line ending `· as skeptic` — the environment is read
- [ ] `python3 resources/board/collect.py --bogus finished --board <copy>/prds` still exits 2 naming `unknown flag --bogus`
- [ ] `grep -c 'persona: ' resources/board/collect.py` is 0 — the refusal text is imported from `transitions.py`, never copied
- [ ] `bash prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh` prints `101 checks · 101 pass · 0 fail` with `PEARDE_AS` unset in the caller's shell
- [ ] `bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh` prints `133 checks · 133 pass · 0 fail` with `PEARDE_AS` unset in the caller's shell, and its `L --as sets the persona term` line still passes

## Verify and Proof

```sh
bash prds/nothing-left-open/the-line-tells-the-truth/probe/verify.sh </dev/null
grep -c 'persona: ' resources/board/collect.py
env -u PEARDE_AS bash prds/the-tool-keeps-its-word/collect-keeps-its-word/probe/verify.sh </dev/null | tail -1
env -u PEARDE_AS bash prds/the-board-runs-itself/collect-is-a-command/probe/verify.sh </dev/null | tail -1
```
