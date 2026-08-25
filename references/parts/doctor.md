# Install check

Telling a broken install from an absent one.

An install that is present and broken looks exactly like one that is absent.
`doctor.sh` tells them apart:

```sh
bash @resources/doctor.sh [board]         # report; exit 1 when a part is broken
bash @resources/doctor.sh --fix [board]   # report, then repair
```

One part per line, each `ok`, `off`, or `broken`. A broken part carries the
command that repairs it. `members` reports only on a master board, and `index`
never reads `off` — the map is either right or wrong.

| part         | `off`                                  | `broken`                                                        |
|--------------|----------------------------------------|------------------------------------------------------------------|
| `wired`      | no agent from @references/targets.md is here | a skill not linked, a block not written, or a copy where a link belongs |
| `index`      | —                                      | @index.md and the tree disagree, or an `@@` keyword is undefined  |
| `statusline` | no agent here renders one, or none is configured in the file in force | configured, and its command does not resolve or renders nothing |
| `board`      | no board                               | off the contract path, or no `language`                          |
| `members`    | not a master board — no `members:`     | an entry that is not a board on disk, or an empty list           |
| `origin`     | no PRDs to read                        | a `derived` PRD with no `from:`, or the @references/parts/derived.md tripwire live |
| `memos`      | no `memos/`                            | a memo fails the check in `@references/memo.md`                   |
| `view`       | the service is not running             | it runs and this board is not registered                         |
| `plan`       | no plan on record yet                  | —                                                                |

- **No agent is named in `doctor.sh`.** `wired` and `statusline` read
  @references/targets.md through @resources/targets.py — one row per agent,
  holding where its skills go, which instructions file it reads, and where a
  continuous line is configured. Adding an agent is adding a row.
- A row's alternatives are read in the order the agent itself reads them, so
  what doctor reports is the profile in force. A variable that moves an
  agent's whole configuration means a machine can hold several, and a line
  wired into the wrong one is correct and inert — the false green the
  `statusline` row exists to catch.
- `--fix` repairs three things: what @resources/install.sh owns — links and
  blocks — a dead status-line symlink, and a view service down or not
  watching this board. It never writes an agent's settings file; a missing
  status line is printed, never pasted for you. A **copy** where a link
  belongs is reported and never repaired: it may hold your edits.
- `index` runs `@resources/index.py check`: a file on disk with no row, a row
  naming no file, a scope naming no file, an `@@` keyword nobody defined. It
  is not `--fix`-able — which row a new file belongs in is a judgement.
- After repairing, doctor re-checks once — the report and exit code describe
  the state the repairs left behind.

Run it on the first run, on `doctor`, and whenever a part is silent when it
should not be.
