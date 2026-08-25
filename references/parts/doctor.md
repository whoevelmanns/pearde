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
| `skills`     | —                                      | a skill file with no `name:`, no `description:`, or a `name:` that disagrees with its file name |
| `index`      | —                                      | @index.md and the tree disagree, or an `@@` keyword is undefined  |
| `statusline` | —                                      | @resources/statusline.sh renders nothing for this board                       |
| `board`      | no board                               | off the contract path, or no `language`                          |
| `members`    | not a master board — no `members:`     | an entry that is not a board on disk, or an empty list           |
| `origin`     | no PRDs to read                        | a `derived` PRD with no `from:`, or the @references/parts/derived.md tripwire live |
| `memos`      | no `memos/`                            | a memo fails the check in `@references/memo.md`                   |
| `view`       | the service is not running             | it runs and this board is not registered                         |
| `plan`       | no plan on record yet                  | —                                                                |

- **No agent is named in `doctor.sh`, and none is looked for.** Where a skill
  folder goes and where a status line is configured are the reader's setup,
  not this repo's — @references/install.md is that step, written to be worked
  out rather than executed. So doctor checks only what is true regardless of
  who is reading: the skill files parse, the map matches the tree, the status
  line renders, the board is on its contract.
- `skills` is about frontmatter, not placement. A skill is found by its
  `name:` and fires on its `description:`; frontmatter that does not parse is
  a skill that silently never fires, which reads exactly like a model
  choosing not to use it. A `name:` that disagrees with the file name
  installs one skill under another's name.
- `statusline` answers the half that is ours. A line wired to a script that
  renders nothing and a line that was never wired look identical in a
  terminal; doctor runs the script against this board and says which it is.
- `--fix` repairs two things: a dead status-line symlink, and a view service
  down or not watching this board. It never writes a settings file.
- `index` runs `@resources/index.py check`: a file on disk with no row, a row
  naming no file, a scope naming no file, an `@@` keyword nobody defined. It
  is not `--fix`-able — which row a new file belongs in is a judgement.
- After repairing, doctor re-checks once — the report and exit code describe
  the state the repairs left behind.

Run it on the first run, on `doctor`, and whenever a part is silent when it
should not be.
