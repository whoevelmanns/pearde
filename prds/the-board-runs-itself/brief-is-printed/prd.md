---
state: done
origin: requested
actual: 0.7h
commit: 2ae39b4
priority: 64
complexity: 20
blast-radius: mid
repo: pearde
workflow: probe-then-spec
needs:
  - one-command
footprint:
  - resources/board/brief.py
  - references/files.md
  - references/parts/handles.md
  - index.md
  - references/parts/workers.md
  - references/parts/consult.md
  - resources/doctor.sh
---

# brief-is-printed — a worker's brief is one command's output, never composed

When this is done, the orchestrator dispatches a worker with the output of
`pearde brief <prd>` and nothing else, and the text of the brief lives in one
file that the command renders.

## Contract

`pearde brief <prd> [--role analyst|implementer] [--as <id>]`
`pearde brief --consult <id> --question "<q>" [--transcript <path>]`

Prints, in this order:

1. one header line — `# brief <prd> · <role> · as <id> · wf <slug|none> ·
   repo <path>` — for the round to log;
2. the persona line — `Work as @references/personas/<id>.md.`;
3. the workflow block from @references/parts/workers.md, when `workflow:` on
   the PRD (or, for an implementer, on any spec) resolves — the route inlined
   by `workflows.py brief`, one block per distinct slug;
4. the role's brief, verbatim from `workers.md`, every placeholder filled.

| placeholder | filled from |
|---|---|
| `<prd>` | the PRD's real path — never `@<member>/…` |
| `<repo>` | the PRD's `repo:`, else the member's repo root, else the board's |
| `<language>` | the PRD's own board's `settings.md` |
| `<probe>` | `prds/<prd>/probe/` — the location `probe-code-lives-in-the-prd-folder` fixes |
| `<board>` | the board path, for `workflows.py brief` |

The role follows the state — `open` is an analyst, `specced` an implementer —
and `--role` overrides. The persona is `--as`, default `engineer`; the
orchestrator reads the job table in `workers.md` and passes what it decides.

Exit 1, naming the skip, on a PRD that is not dispatchable — held, gated,
clashing, or carrying a slug that names nothing.

## Rules

- **One source.** The brief text stays in `workers.md` between markers —
  `<!-- brief:analyst -->` … `<!-- /brief -->`, one pair per role — and the
  command reads it from there. No copy under `resources/`; a change to the
  brief is a change to one file.
- The placeholders are named once, in `workers.md`, in the table above. A
  placeholder the file uses and the table does not name is a `doctor`
  failure under `skills`… no: under a new `briefs` row, which also fails when
  a marker pair is missing or unterminated.
- The consultant brief renders the same way with `<transcript_path>`,
  `<prds/>`, `<repo>` and the question.
- **Three probe clauses join the analyst brief**, absorbed from the deferred
  `probe-code-lives-in-the-prd-folder`: probe code lives at `<probe>` —
  `prds/` is outside the manifest scan, so it costs no row and travels with
  the PRD; fixtures are built in a temp dir at run time, never under `prds/`
  — a directory holding `prd.md` anywhere under the board is a PRD; and a
  box spelling quoted into a PRD or a spec is backtick-quoted first, because
  the matcher is line-based and a pasted `- [ ]` is a real box.

## Files

| file | change |
|---|---|
| `resources/board/brief.py` | new |
| `references/parts/workers.md` | the markers, the placeholder table; "give each worker exactly its brief" becomes "hand it `pearde brief`" |
| `references/parts/consult.md` | the `--consult` line |
| `resources/doctor.sh` | the `briefs` row |
| `resources/board/brief.py` | registers `brief` through `COMMANDS` |

## Verify

- On a copy of the example board, `brief big/second` — the one ready PRD —
  equals the analyst block of `workers.md` with the five placeholders
  replaced — a probe diffs them;
- `brief building` exits 1 with `held`; `brief next` exits 1 naming
  `building`; `brief next --force` prints the brief anyway and says `forced`;
- on a PRD carrying the example workflow, the output holds the workflow block
  and both atomics inlined;
- `doctor` reports `briefs ok`, and `broken` when a marker is removed.

## Report

DONE 16/16 · commit 2ae39b4 · probe 104/104 · 47/47 73/73 39/39
