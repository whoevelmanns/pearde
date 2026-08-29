---
state: done
origin: requested
actual: 0.6h
commit: e1ef842
priority: 60
complexity: 9
blast-radius: mid
repo: pearde
workflow: probe-then-spec
footprint:
  - resources/guard.py
  - references/parts/guard.md
  - resources/doctor.sh
  - resources/board/init.py
  - references/install.md
  - resources/pearde.py
---

# guard-on-is-one-command — `pearde guard on` wires the guard where the user asks, and doctor stops opening with `guard off`

When this is done, a person who wants the guard runs one command in the
repo that holds the board, and every `doctor` run afterwards reads `guard
ok`. Nothing writes a settings file unasked.

## The consequence, named

@references/parts/guard.md hands the reader a JSON block to paste into
`.claude/settings.json`, and `doctor` has printed `guard off — not wired`
as its first non-ok line on this repo every run for two days, including
after the guard gained the `PreToolUse` `Edit|Write` matcher that refuses a
hand-written `state:`. The rule that doctor never writes a settings file
stands — a command the user types is not doctor.

## The command

`pearde guard on [<repo>]` · `pearde guard off [<repo>]` · `pearde guard status`

- `on`: reads `<repo>/.claude/settings.json` (creating it if absent), adds
  the `env.MAX_THINKING_TOKENS` key if unset and the three hook entries from
  @references/parts/guard.md — `PreToolUse` on `Bash|Read`, `PreToolUse` on
  `Edit|Write`, `PostToolUse` on `Edit|Write` — each pointing at this
  skill's absolute `resources/guard.py`; preserves every other key; refuses
  to duplicate an entry already present; prints the file and the lines it
  added, and the one sentence the reader needs: a new settings file is
  read after `/hooks` or a restart.
- `off`: removes exactly the entries `on` added, nothing else.
- `status`: what `doctor`'s `guard` row says, alone.
- `doctor`'s `guard off` fix line becomes `pearde guard on`; `init`'s
  closing lines gain a fourth, `pearde guard on — optional, refuses the
  waste the loop's rules name`.

## Files

| file | change |
|---|---|
| `resources/guard.py` | `COMMANDS = {"guard": …}` — `on`, `off`, `status`; the JSON edit preserves unknown keys and order |
| `references/parts/guard.md` | the command replaces the paste-this block; the block stays as what the command writes |
| `resources/doctor.sh` | the fix line |
| `resources/board/init.py` | the fourth line |
| `references/install.md` | the guard bullet names the command |

## Verify

- In a temp repo with no `.claude/`: `guard on` creates the file with the three hooks and the env key; `doctor` on a board there reads `guard ok`; `guard on` again changes nothing and says so; `guard off` leaves an empty hooks block and the env key; `guard status` matches doctor's row.
- In a temp repo whose settings.json already holds other hooks and keys: after `guard on` and `guard off`, the file is byte-identical to before.
- `bash resources/doctor.sh` on this repo prints `fix: … pearde guard on`.

## Report

DONE 18/18 · commit e1ef842 · probe 78/78
