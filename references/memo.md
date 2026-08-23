# Memos

A PRD says what to build. A memo says what was decided and what it beat.
Different lifetimes: a PRD goes `done` and stops mattering, a memo outlives the
work it governed.

```
prds/memos/<slug>.md
```

- No `state`. Never claimed, specced, or dispatched.
- `memos/` holds no `prd.md`, so scan walks past it and the progress line never
  counts it.
- One flat directory, no nesting. A memo is found by its slug.
- On the board anyway — a decision recorded where the next session does not
  look is a decision nobody has.

## Frontmatter

```
---
memo: one-writer
kind: decision
status: decided
subject: why the orchestrator is the only writer of PRD state
date: 2026-08-23
prds:
  - p2-parallel-dispatch
---
```

| key             | required | is                                                            |
|-----------------|----------|----------------------------------------------------------------|
| `memo`          | yes      | the slug — equals the filename without `.md`                   |
| `kind`          | yes      | `decision` (a call was made) or `note` (source material folded in from outside, arguing nothing of ours) |
| `status`        | yes      | `open`, `decided`, or `superseded`                             |
| `subject`       | yes      | one line: what this memo settles                               |
| `date`          | yes      | the day the call was recorded, ISO 8601 and only that          |
| `updated`       | no       | set only on a *substantive* revision                           |
| `prds`          | no       | board-relative PRD dirs this memo governs. A list              |
| `supersedes`    | no       | the slug this replaces                                         |
| `superseded_by` | no       | the slug that replaced this                                    |

The set is **closed**. Anything else is a typo and fails the check — a
misspelled key is worse than a missing one, because it reads as present.

`status` is one word. A status needing a sentence is a status doing the memo's
job; the sentence goes in the body where a reader can argue with it.

`date` is **written, never stamped**. Nothing reads a clock — a generated date
moves on every mechanical sweep, and sorting by file mtime sorts by when
somebody last touched a path rather than by when the call was made. One padded
spelling means string comparison is date comparison.

Dialect: a `---` fence, one `key: value` per line, `-` items for lists, matched
by name at any indentation — what `prd.md` and a spec already use, so a memo is
read by the parser that exists rather than a second one written for prose.

## Body

`references/templates/memo.md` is the shape:

| section                     | holds                                              |
|-----------------------------|-----------------------------------------------------|
| `## Decision`               | what was settled, present tense                    |
| `## Why`                    | the argument — the part that has to survive        |
| `## Alternatives considered`| what lost, and on what count. Never empty          |
| `## Consequences`           | what this costs, including what it does not fix    |

`Why` and `Alternatives considered` are the one place in the board where
paragraphs are correct, per `references/language.md`. Compress them.

**Alternatives is not optional.** A memo with no alternatives is a claim, not a
decision, and six months on nobody can tell whether the other road was walked
and rejected or never seen.

## The check

`doctor.sh` reports `memos`; `python3 <skill>/memos.py check [board]` is the
same check on its own. It fails on:

- a `kind` or `status` word outside the closed set
- a slug that disagrees with its filename
- a required key missing, or a key nobody declared
- a date that is not ISO 8601, or an `updated` preceding its `date`
- `status: superseded` naming no `superseded_by`, or naming a memo that does
  not exist
- `prds:` naming a directory that is not a PRD on this board

Checked against the real board, never a fixture — the frontmatter and the board
cannot drift apart quietly.

## Why the board, not a docs folder

A decision recorded outside the board is a decision the next session does not
read. The board is what a session already walks; `memos/` is one directory
deeper on a path it is already on.

**A `docs/` folder at the repo root** — the conventional home, and the one this
was extracted from. Lost: it reads fine for a human and is invisible to the
loop, which is the failure mode being fixed. Memos beside the PRDs they govern
let `prds:` name a sibling and let the check verify it.

**Status as the folder** — `open/`, `decided/`, `superseded/`, with the check
enforcing that a memo sits in the directory matching its status. Lost: moving a
file to change a status rots every inbound link, and memos are linked from
PRDs, from each other, and from Plane.

## Trimmed on the way in

The source system also had `kind: port` and the statuses `partial` and
`landed`, because its memos specified ports that owed a passing gate. A pearde
memo owes no gate — the PRD it governs owes that, and `done` is where it is
checked. Carrying `landed` here would give a memo a second, weaker copy of a
PRD's state, which is the one thing the frontmatter contract forbids: one fact,
one home.
