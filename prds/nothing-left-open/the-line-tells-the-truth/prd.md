---
state: analyzing
origin: requested
claim: analyst-the-line-tells-the-truth 2026-08-29 17:42
priority: 70
complexity: 0
blast-radius: high
repo: pearde
workflow: probe-then-spec
footprint:
  - resources/board/collect.py
  - resources/board/transitions.py
  - resources/board/plan.py
  - references/parts/progress.md
  - references/parts/statusline.md
  - resources/statusline.sh
  - README.md
  - prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh
  - prds/the-board-runs-itself/specced-is-a-command/probe/verify.sh
  - prds/memos/two-holes-the-flag-probe-found.md
---

# the-line-tells-the-truth — the progress line says who acted and what is done, and every discovered command refuses a flag it does not know

When this is done, four things the last day's runs measured are closed:

1. **`collect` refuses without a persona.** Today it writes `· as engineer`
   silently when neither `--as` nor `PEARDE_AS` is set; every transition
   refuses that case, and `add` alone defaults with `(default)` on the
   line. `collect` is the one verb that commits, and its line is the record
   — it refuses like `claim` does, naming `PEARDE_AS` and the install line.
2. **`set --force` clears what the target cannot carry.** A forced
   `analyzing → open` today keeps `claim: w1`, and `brief` reports the PRD
   held. `--force` skips the gate; it does not skip the bookkeeping: a
   target state that carries no claim (`open`, `specced`, `done`,
   `failed`, `deferred`, any parked word) clears `claim:`.
3. **The first term of the line is `done`.** An uncommitted rename sits in
   the tree — `plan.py` `progress_terms` (`asked`→`done`, the key and
   the scan's use of it), `transitions.py` `progress_line`, `progress.md`,
   `statusline.md`, `statusline.sh`, `README.md` — made by a session on
   another board through the symlinked install, deliberate and coherent:
   `asked` counts a container whose children all landed as outstanding,
   which is the lie `collect-keeps-its-word` closed from the other side.
   Adopt it whole (read every hunk; it is six files and one idea), and
   re-aim the two matchers that pin the old word:
   `transitions-are-commands/probe/verify.sh` (`the line opens with the
   transition`) and `specced-is-a-command/probe/verify.sh:126`.
4. **`vision` and `example` declare their flags.** `plan.py` exposes both
   through `COMMANDS` with no `flags` attribute, so `pearde vision --bogus`
   exits 0 with the flag ignored — the shape `an-unknown-flag-refuses`
   closed everywhere else. They declare through the same parser
   (`vision`: `--json`, `--next`, `--check`, `--board`; `example`: none).

## Files

| file | change |
|---|---|
| `resources/board/collect.py` | the persona refusal, the same text as `transitions.py`'s |
| `resources/board/transitions.py` | `set --force` clears `claim:` for a claimless target; the `progress_line` hunks adopted |
| `resources/board/plan.py` | the `progress_terms` hunks adopted; `vision`/`example` declare flags |
| `references/parts/progress.md` · `statusline.md` · `resources/statusline.sh` · `README.md` | the rename's hunks adopted as they stand |
| the two harnesses | the matchers read `done` |
| the memo | `status: decided` |

## Rules

- The rename is adopted, not rewritten: every hunk in the tree today is the
  change, and the analyst reads them before touching anything. Nothing else
  in those files moves.
- The persona refusal text is one string, shared with `transitions.py` —
  import it, do not copy it.

## Verify

- On a copy of the example board: `collect finished` with `PEARDE_AS` unset and no `--as` exits 1 naming `PEARDE_AS` and writes nothing; with `--as engineer` it lands.
- `set building open --force --as engineer` leaves no `claim:`; `brief building` no longer says held.
- `scan` on the copy prints `progress: done …`; `transitions-are-commands` and `specced-is-a-command` read 74/74 and 90/90 with the matchers re-aimed; `statusline.sh <<< '{}'` prints the `done` term.
- `pearde vision --bogus` and `pearde example --bogus` exit 2 naming the flag; `an-unknown-flag-refuses/probe/verify.sh` stays 196/196.
