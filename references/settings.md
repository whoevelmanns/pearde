# Settings

Every board-wide knob. Per-PRD values — `priority`, `est`, `repo` — live in
each `prd.md`'s frontmatter, not here.

The live copy is `prds/settings.md` on the board. This file is its template.
The skill folder is shared across installs, so a value written here would leak
into every board — never write values here.

```yaml
---
language: <language>
workers: 3
pipeline: 3
est-default: 4h
gantt-day: 8h
plane: auto
---
```

| key           | default      | meaning                                                          |
|---------------|--------------|------------------------------------------------------------------|
| `language`    | none — asked | the language every PRD, spec, and report is written in           |
| `workers`     | 3            | implementer slots, loop step 5                                   |
| `pipeline`    | 3            | `specced` PRDs kept ahead, loop step 4                           |
| `est-default` | 4h           | weight of an unestimated PRD while no PRD on the board has `est` |
| `gantt-day`   | 8h           | est-hours one day represents in the Plane Gantt; lower it to stretch a small board's timeline |
| `plane`       | auto         | `auto` mirrors whenever Plane is reachable, bootstrapping this board on first sight; `off` never mirrors and never reports |

## Read

Read `prds/settings.md` in loop step 1, once per session, and after writing
it. A key missing from the live copy reads at its default.

## Write

The orchestrator is the only writer, same as PRD state.

- No `prds/settings.md`: this is the first run. Run
  `bash <skill>/doctor.sh --fix` first, so a broken install is repaired before
  the board is written. Copy the block above in, ask the user for `language` —
  English, German, Spanish, any language, stated by the user, never guessed —
  and write the answer over `<language>`. Ask nothing else; the rest has
  defaults.
- `workers=N` / `pipeline=N`: write the key, then run with it.
- Any other setting the user states: write it, confirm in one line.

Unknown keys in the live copy are the user's: preserve them, same as PRD
frontmatter.
