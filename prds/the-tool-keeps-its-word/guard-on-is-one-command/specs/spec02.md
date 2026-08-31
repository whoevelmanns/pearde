---
complexity: 3
footprint:
  - resources/doctor.sh
  - resources/board/init.py
  - references/parts/guard.md
  - references/install.md
---

# spec02 — doctor, init and the manual name the command

Every place that used to hand the reader a block to paste now names
`pearde guard on`. `doctor`'s `guard off` fix line is the command; `init`
closes with a fourth line, `pearde guard on — optional, refuses the waste the
loop's rules name`; @references/parts/guard.md's "Wiring it" opens with the
command and keeps the JSON block as what the command writes; the guard bullet
of @references/install.md names `on`, `off` and `status`.

**Already standing from the probe (edited in place, uncommitted):** all four
files. **Left:** run the checks below, tick the boxes.

Decisions the build made, with the reason:

- The fourth `init` line is printed **before** the URL, not after `pearde`:
  `prds/the-board-runs-itself/init-asks-nothing/probe/verify.sh` pins the last
  three lines (`last3`) in four assertions, and README.md — another session's
  file today — describes them. Doctor's `guard off … fix: pearde guard on`
  row is printed just above, so the line reads as its answer. init.py's
  docstring says "four lines" and names the order.
- `doctor.sh`'s fix line spells both the alias and the long form:
  `fix "pearde guard on — writes the block of @references/parts/guard.md into $GSET, then /hooks or restart (python3 $SKILL_ROOT/resources/pearde.py guard on)"`
  — one line, the row above it untouched. The comment at doctor.sh line 157,
  "`--fix` writes the block", was already wrong before this PRD (doctor never
  wrote it) and is out of this spec's scope: reported, not edited.
- guard.md keeps the sentence `"matcher": "Edit|Write"` inside the JSON
  block — `the-loop-is-commands`'s harness greps for it.

## Acceptance

- [x] `bash resources/doctor.sh <tmp-repo-with-a-board-and-no-hooks>` prints `  guard       off     not wired in <tmp>/.claude/settings.json` and, on the next line, `fix: pearde guard on — writes the block of @references/parts/guard.md into <tmp>/.claude/settings.json, then /hooks or restart (python3 …/resources/pearde.py guard on)`
- [x] after `pearde guard on <tmp>`, the same doctor run prints `  guard       ok      wired in <tmp>/.claude/settings.json · MAX_THINKING_TOKENS=8000`
- [x] `python3 resources/board/init.py init <tmp>` (fresh git repo, `PEARDE_PORT=1`) prints `pearde guard on — optional, refuses the waste the loop's rules name` as the fourth-from-last line, and the last three lines are still the URL, `pearde add "<title>"`, `pearde`
- [x] `references/parts/guard.md` names `` `pearde guard on [<repo>]` `` in "Wiring it", keeps the JSON block with `"matcher": "Edit|Write"`, and "Turning it off" opens with `` `pearde guard off` ``
- [x] `references/install.md`'s guard bullet begins `- `pearde guard on` in the repo the board lives in` and names `pearde guard off` and `pearde guard status`
- [x] `bash prds/the-board-runs-itself/init-asks-nothing/probe/verify.sh` still prints `89 checks · 89 pass · 0 fail`; `bash prds/the-board-runs-itself/the-loop-is-commands/probe/verify.sh` still prints `60 checks · 60 pass · 0 fail`

## Verify and Proof

```sh
grep -n 'fix "pearde guard on' resources/doctor.sh
grep -n 'pearde guard on — optional' resources/board/init.py
grep -n 'pearde guard on \[<repo>\]\|"matcher": "Edit|Write"\|`pearde guard off`, or set' references/parts/guard.md
grep -n 'pearde guard on\|pearde guard off\|pearde guard status' references/install.md
bash -n resources/doctor.sh && python3 -c "import ast; ast.parse(open('resources/board/init.py').read())"
```
