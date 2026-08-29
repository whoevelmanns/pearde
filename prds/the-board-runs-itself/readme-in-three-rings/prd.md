---
state: done
origin: requested
actual: 0.7h
commit: fa82dd3
priority: 55
complexity: 9
blast-radius: low
repo: pearde
workflow: probe-then-spec
needs:
  - the-loop-is-commands
  - init-asks-nothing
  - vision-is-first-class
footprint:
  - README.md
  - references/language.md
  - index.md
  - skills/pearde.md
---

# readme-in-three-rings — a newcomer runs a board in five minutes, and meets the rest only when it matters

When this is done, a person who has never seen this repo reads `README.md`,
runs five commands, and has a board with a PRD on it and the page open — and
nothing an agent reads has moved.

## Contract

`README.md`, in this order, under 200 lines:

| section | holds |
|---|---|
| **In sixty seconds** | five lines: `python3 <repo>/resources/pearde.py install --apply <skills-dir>` (which prints the `pearde` alias the next four use), `pearde init --example`, `pearde add "…"`, `pearde`, `pearde view`. What each prints |
| **What is on disk** | one table: `prd.md`, `specs/`, `memos/`, `workflows/`, `settings.md`, `vision.md` — one line each, what it is and who writes it |
| **The nine states** | one picture — a Mermaid state diagram — with the `pearde` command on every arrow. No prose beside it |
| **The round** | the seven-row table from `loop.md`, and one sentence: the tool moves, the orchestrator chooses |
| **Three rings** | core · advisors · tools — one paragraph each, ending in the `@@` scope to open. The reader stops at the ring they need |
| **Glossary** | twenty words at most — PRD, spec, box, footprint, needs, weight, axis, band, collect, claim, memo, workflow, atomic, persona, consult, drill, master, member, guard, doctor |
| **Addressing** | the two lines about `@` and `@@`, as today |

The current README's tables move: "One question, one file" and the scope
table go under **Three rings** as the core ring's body, unchanged in content.

## Rules

- **A human reader.** @references/language.md gains one row — *README ·
  reader: a person, first time · shape: quickstart, then rings* — and the
  README is the one document where a sentence may carry two ideas. Every
  reference keeps the existing rules.
- Nothing an agent needs moves. `index.md` stays the map,
  `references/system.md` the drop-in block, `skills/pearde.md` still opens
  with "Read @README.md" and the round table it finds there is the same
  seven rows.
- Every command in the quickstart is run by a probe on a temp dir, end to
  end, and the README's stated output is what it printed.
- The diagram names every state of @references/parts/states.md exactly once,
  and no other.

## Files

| file | change |
|---|---|
| `README.md` | rewritten to the table |
| `references/language.md` | the row |
| `index.md` | `@@skills`, `@@install` rows follow the README's new anchors |
| `skills/pearde.md` | its "Read @README.md — its **One question, one file** table" line points at the table's new place under the core ring |

## Verify

- `wc -l README.md` ≤ 200.
- `probe/quickstart.sh` runs the five lines in a temp dir with a temp
  skills dir; each exits 0, the skills dir holds eleven folders after line
  one, and the page answers at the printed URL.
- A probe extracts the Mermaid block and checks the state set equals
  `states.md`'s table, 9 = 9.
- `python3 resources/index.py check` silent; `bash resources/doctor.sh`
  every row `ok` or `off`.

## Report

DONE · committed fa82dd3
