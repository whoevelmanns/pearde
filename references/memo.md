# Memos — a decision's facts live in the decision

A PRD says what to build. A **memo** says what was decided and what it beat.
They are different documents with different lifetimes: a PRD is done and stops
mattering, a memo outlives the work it governed and is the thing you read when
someone asks "why is it like this".

A memo is not a PRD. It is never claimed, never specced, never dispatched, and
it has no `state` — nothing in the loop touches it. Put it on the board anyway,
because the alternative is a decision recorded somewhere the next session will
not look.

```
prds/
  memos/
    <slug>.md
```

`memos/` holds no `prd.md`, so scan walks past it and the progress line never
counts it. One flat directory, no nesting: a memo is found by its slug.

## The frontmatter

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

| key             | required | what it is                                                    |
|-----------------|----------|---------------------------------------------------------------|
| `memo`          | yes      | the slug — equals the filename without `.md`                  |
| `kind`          | yes      | `decision` (a call was made) or `note` (source material folded in from outside, arguing nothing of ours) |
| `status`        | yes      | `open`, `decided`, or `superseded`                            |
| `subject`       | yes      | one line: what this memo settles                              |
| `date`          | yes      | the day the call was recorded, ISO 8601 and only that         |
| `updated`       | no       | set only on a *substantive* revision                          |
| `prds`          | no       | board-relative PRD dirs this memo governs; a list             |
| `supersedes`    | no       | the slug this replaces                                        |
| `superseded_by` | no       | the slug that replaced this                                   |

Anything else is a typo and fails the check. A misspelled key is worse than a
missing one, because it reads as present.

`status` is one word. A status that needs a sentence is a status doing the
memo's job — the sentence goes in the body, where a reader can argue with it.

`date` is **written, never stamped**. Nothing reads a clock: a generated date
moves on every mechanical sweep, and sorting memos by file mtime sorts them by
when somebody last touched a path rather than by when the call was made. One
padded spelling means string comparison is date comparison.

The dialect is the board's own — a `---` fence, one `key: value` per line, `-`
items for lists, matched by name at any indentation. Exactly what `prd.md` and
a spec use, so a memo is read by the parser that already exists rather than by
a second one written for prose.

## The body

`references/templates/memo.md` is the shape:

```
## Decision      what was settled, in the present tense
## Why           the argument — the part that has to survive
## Alternatives considered
                 what lost, and on what count. Never empty.
## Consequences  what this costs, including what it does not fix
```

**Alternatives is not optional.** A memo with no alternatives is a claim, not a
decision, and six months on nobody can tell whether the other road was walked
and rejected or never seen. Name what lost and why it lost.

## The check

`doctor.sh` reads every memo and reports `memos`:

- a `kind` or `status` word outside the closed set
- a slug that disagrees with its filename
- a required key missing, or a key nobody declared
- a date that is not ISO 8601, or an `updated` that precedes its `date`
- `status: superseded` naming no `superseded_by`, or naming a memo that does
  not exist
- `prds:` naming a directory that is not on the board

A memo is checked against the real board, not a fixture. The whole point is
that the frontmatter and the board cannot drift apart quietly.

## Why the board and not a docs folder

A decision recorded outside the board is a decision the next session does not
read. The board is what a session already walks; `memos/` is one directory
deeper on a path it is already on.

**What lost:** a `docs/` folder at the repo root — the conventional home, and
the one this was extracted from. It reads fine for a human and is invisible to
the loop, which is the failure mode being fixed. Keeping memos beside the PRDs
they govern means `prds:` can name a sibling and the check can verify it.

**Also lost:** status as the folder — `open/`, `decided/`, `superseded/`, with
the check enforcing that a memo sits in the directory matching its status.
Moving a file to change a status rots every inbound link, and memos are linked
from PRDs, from each other, and from Plane.

## Trimmed on the way in

The source system also had `kind: port` and the statuses `partial` and
`landed`, because its memos specified ports that owed a passing gate. A pearde
memo owes no gate — the PRD it governs owes that, and `done` is where it is
checked. Carrying `landed` here would give a memo a second, weaker copy of a
PRD's state, which is the one thing the board's frontmatter contract forbids:
one fact, one home.
