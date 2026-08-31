# Memos

A PRD says what to build. A memo says what was decided and what it beat.
Different lifetimes: a PRD goes `done` and stops mattering, a memo outlives
the work it governed.

```
.pearde/memos/<slug>.md
```

- No `state`. Never claimed, specced, or dispatched.
- `memos/` holds no `prd.md`, so scan walks past it and the progress line
  never counts it.
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
| `kind`          | yes      | `decision` (a call was made) or `note` (source material folded in, arguing nothing of ours) |
| `status`        | yes      | `open`, `decided`, or `superseded`                             |
| `subject`       | yes      | one line: what this memo settles                               |
| `date`          | yes      | the day the call was recorded, ISO 8601 and only that          |
| `updated`       | no       | set only on a *substantive* revision                           |
| `prds`          | no       | board-relative PRD dirs this memo governs. A list              |
| `supersedes`    | no       | the slug this replaces                                         |
| `superseded_by` | no       | the slug that replaced this                                    |

The set is **closed**. Anything else fails the check — a misspelled key is
worse than a missing one, because it reads as present.

`status` is one word. A status needing a sentence goes in the body, where a
reader can argue with it.

`date` is **written, never stamped** — a generated date moves on every
mechanical sweep, and mtime sorts by who last touched a path, not by when the
call was made. One padded spelling means string comparison is date comparison.

Dialect: a `---` fence, one `key: value` per line, `-` items for lists,
matched by name at any indentation — what `prd.md` and a spec already use, so
one parser reads all three.

## Body

`@references/templates/memo.md` is the shape:

| section                     | holds                                              |
|-----------------------------|-----------------------------------------------------|
| `## Decision`               | what was settled, present tense                    |
| `## Why`                    | the argument — the part that has to survive        |
| `## Alternatives considered`| what lost, and on what count. Never empty          |
| `## Consequences`           | what this costs, including what it does not fix    |

Where the decision rests on recorded knowledge, `Why` wikilinks the
conclusion — `[[<slug>]]`, the note under `.pearde/wiki/conclusions/`. The
memo cites, the KB holds the provenance; no frontmatter key for it, the body
is the only place a reference can be argued with.

`Why` and `Alternatives considered` are the one place on the board where
paragraphs are correct, per @references/language.md. Compress them.

**Alternatives is not optional.** A memo with no alternatives is a claim, not
a decision — nobody can later tell whether the other road was walked and
rejected or never seen.

## An external source

A repo whose decisions already live in another system does not move them —
one fact, one home. Point `memos:` in `.pearde/settings.md` at that dir:

```yaml
memos: ../.mi/docs/memos
```

The dir is read-only, every scalar frontmatter key rendered as-is. The check
then verifies only what is universal — the file parses, the required five are
present — and leaves the foreign vocabulary alone. The closed set applies only
to the board's own `memos/`.

## The check

`doctor.sh` reports `memos`; `python3 @resources/memos.py check [board]` is the
same check alone. It fails on:

- a `kind` or `status` word outside the closed set
- a slug that disagrees with its filename
- a required key missing, or a key nobody declared
- a date that is not ISO 8601, or an `updated` preceding its `date`
- `status: superseded` naming no `superseded_by`, or naming a memo that does
  not exist
- `prds:` naming a directory that is not a PRD on this board

Checked against the real board, never a fixture — the frontmatter and the
board cannot drift apart quietly.

## Why the board, not a docs folder

`memos/` is one directory deeper on a path the session already walks.
Rejected:

- **`docs/` at the repo root** — reads fine for a human, invisible to the
  loop. Memos beside the PRDs let `prds:` name a sibling the check can verify.
- **Status as the folder** (`open/`, `decided/`, …) — moving a file to change
  a status rots every inbound link.
