---
complexity: 6
footprint:
  - resources/board/brief.py
  - resources/board/init.py
  - prds/the-board-runs-itself/init-asks-nothing/probe/verify.sh
---

# spec04 — `brief`, `init` and `settings` declare their flags; `init` and `settings` take `--dry`

`brief.py` declares `FLAGS = transitions.Flags(("as", "board", "role",
"consult", "question", "transcript"), ("force", "check"))` — no `--dry`,
because brief writes nothing — and `cmd_brief` parses through
`transitions.Args`, exit 2 on `FlagRefused`. `init.py` imports
`transitions` and declares `init`: `--language, --name, --example, --dry`
and `settings`: `--board, --dry`. `init --dry` prints `dry · board <name> ·
language <l> — pearde settings language=<l> changes it` and `would write:`
with the absolute `settings.md`, `vision.md` and, inside a git repo,
`.gitignore` — and starts no daemon, runs no doctor; on an existing board it
says `would write: nothing — <board>/settings.md exists`. `settings
<k>=<v> --dry` prints `dry · settings: <k> <old> → <v>` and `would write:
prds/settings.md`.

The committed harness `init-asks-nothing` pins `init --bogus` to exit 1 at
line 165 — the count the contract moves (exit 2, with the list). That one
line is this spec's work: `"1"` → `"2"`. The rule it asserts — an unknown
flag is refused — did not move.

**Already standing from the probe** (uncommitted, in place — brief.py hunks
at lines 355–358, 363–367, 384; init.py hunks at 4–5, 26–30, 46, 70–74,
166–167, 172–191, 220, 235–238, 249–251, 257): both `FLAGS`, the `trlib`
import, the `--dry` branches of `cmd_init` and `cmd_settings`, `_command`
catching `trlib.FlagRefused` → 2 and setting `call.flags`. The private
`Args` classes are gone. The harness line is **not** yet changed.

**Left:** the one-line harness edit, then the boxes.

## Acceptance

- [x] `pearde brief <prd> --dyr --board <copy>/prds` exits 2 with `unknown flag --dyr — brief takes: --as, --board, --role, --consult, --question, --transcript, --force, --check`
- [x] `pearde init <new dir> --dyr` exits 2 with `init takes: --language, --name, --example, --dry` and creates no directory
- [x] `pearde settings workers=4 --dyr --board <copy>/prds` exits 2 naming `--board, --dry`, and `workers:` in the copy's `settings.md` is unchanged
- [x] `pearde init <new dir> --name nb --dry` exits 0, prints `dry · board nb · language English — …` and `would write: <dir>/prds/settings.md · <dir>/prds/vision.md`, prints no URL and no doctor report, and leaves no directory
- [x] `pearde settings workers=4 --dry --board <copy>/prds` prints `dry · settings: workers 1 → 4` and `would write: prds/settings.md`; the file is unchanged; the real run then prints `settings: workers 1 → 4`
- [x] `prds/the-board-runs-itself/init-asks-nothing/probe/verify.sh` line 165 reads `"2"` and the harness prints `89 checks · 89 pass · 0 fail`
- [x] `brief-is-printed` prints `verify: 104/104 checks pass`
- [x] `grep -c '^class Args' resources/board/brief.py resources/board/init.py` prints `0` for both

## Verify and Proof

```sh
grep -n '^FLAGS = \|trlib.FlagRefused\|if args.dry:' resources/board/brief.py resources/board/init.py
sed -n 165p prds/the-board-runs-itself/init-asks-nothing/probe/verify.sh
bash prds/the-board-runs-itself/init-asks-nothing/probe/verify.sh </dev/null | tail -1
bash prds/the-board-runs-itself/brief-is-printed/probe/verify.sh </dev/null | tail -1
bash prds/an-unknown-flag-refuses/probe/verify.sh </dev/null | grep -E 'brief|init|settings|verify:'
```
