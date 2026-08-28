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
| `index`      | —                                      | @references/files.md and the tree disagree, or an `@@` keyword is undefined in @index.md |
| `statusline` | —                                      | @resources/statusline.sh renders nothing for this board                       |
| `board`      | no board                               | off the contract path, or no `language`                          |
| `members`    | not a master board — no `members:`     | an entry that is not a board on disk, or an empty list           |
| `origin`     | no PRDs to read                        | a `derived` PRD with no `from:`, or the @references/parts/derived.md tripwire live |
| `memos`      | no `memos/`                            | a memo fails the check in `@references/memo.md`                   |
| `workflows`  | no `workflows/`                        | a file fails the check in `@references/workflow.md`               |
| `questions`  | no PRDs to read                        | a round the user cannot act on — the four shapes are below        |
| `view`       | the service is not running             | it runs and this board is not registered                         |
| `plan`       | no plan on record yet                  | —                                                                |

- **No agent is named in `doctor.sh`, and none is looked for.** Where a skill
  folder goes and where a status line is configured are the reader's setup,
  not this repo's — @references/install.md is that step, written to be worked
  out rather than executed. So doctor checks only what is true regardless of
  who is reading: the skill files parse, the map matches the tree, the status
  line renders, the board is on its contract.
- `skills` is about frontmatter, not placement. A skill is found by its
  `name:` and fires on its `description:`. Frontmatter that does not parse is
  a skill that silently never fires, which reads exactly like a model
  choosing not to use it. A `name:` that disagrees with the file name
  installs one skill under another's name.
- `statusline` answers the half that is ours. A line wired to a script that
  renders nothing and a line that is not wired look identical in a terminal.
  Doctor runs the script against this board and says which it is.
- `--fix` repairs one thing: a view service down or not watching this board.
  It never writes a settings file — a status line lives in the user's own.
- `questions` runs `@resources/questions.py check`, the only reader of the
  round's format. It reports four shapes, and every one of them is silent from
  the outside — a board with a broken round and a board with nothing to ask
  look identical: a `## Questions` or `## Answers` heading with nothing under
  it; a question that asks nothing, or that carries no recommended answer; an
  `## Answers` section with no `## Questions` above it, which is an answer to
  a question nobody wrote down; and a PRD parked on the user — `state:
  question`, or any parked state or `mode:` naming a human — that never says
  what it is asking. It reads `needs:` in the same pass, because a `needs:`
  holding prose instead of PRD names resolves to nothing in `plan` and is
  reported nowhere else. An answered round is history and is left alone. Not
  `--fix`-able: what a question should have asked is the one thing only its
  author knows.
- `workflows` runs `@resources/workflows.py check`, the only reader of the
  workflow format. It reads the library the way `memos` reads `memos/` —
  the closed frontmatter set, one slug key, the required sections — and the
  half no single file can see: a step naming an atomic nobody wrote, and a
  `workflow:` on a `prd.md` or a spec naming no **workflow** in the library
  — an atomic is a file, so naming one is this same failure: a route was
  asked for and a single step was found. Both are silent from the outside,
  and both send a worker nowhere. A `workflows:` pointing outside `prds/` is
  checked in full, not mirrored: it is this library shared between boards,
  not another system's. Not `--fix`-able — what a step should name is its
  author's to say.
- `index` runs `@resources/index.py check` over both halves of the map — the
  scopes in @index.md, the manifest in @references/files.md: a file on disk
  with no row, a row naming no file, a scope naming no file, an `@@` keyword
  nobody defined. It is not `--fix`-able — which row a new file belongs in is
  a judgement.
- After repairing, doctor re-checks once — the report and exit code describe
  the state the repairs left behind.

Run it on the first run, on `doctor`, and whenever a part is silent when it
should not be.
