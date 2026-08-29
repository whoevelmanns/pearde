---
complexity: 6
footprint:
  - resources/guard.py
  - resources/pearde.py
  - prds/the-tool-keeps-its-word/guard-on-is-one-command/probe/verify.sh
---

# spec01 — `pearde guard on|off|status` is a command of guard.py, forwarded by pearde.py

`guard.py` gains three verbs beside `pre`/`post`/`check`: `on [<repo>]` writes
the hooks block of @references/parts/guard.md into `<repo>/.claude/settings.json`
(created when absent) adding only what is missing, `off [<repo>]` removes
exactly those entries, `status [<repo>]` prints `doctor`'s `guard` row alone.
`pearde.py` forwards the name: discovery scans `resources/board/*.py` only, so
`guard.py` is wired the way `memos.py` and `workflows.py` are — one `FORWARD`
row, `("guard.py", ["status"], ("on", "off", "status"))` — bare `pearde guard`
is `status`. The PRD's table says `COMMANDS = {"guard": …}` in `guard.py`;
that would be dead code, since nothing discovers it there, and a shim under
`resources/board/` would be the only board module that exists to import a
`resources/` script. The row is the smaller change and the precedent.

**Already standing from the probe (built in place, uncommitted):** the whole
command block in `resources/guard.py` (`SELF`, `THINK`, `HOOKS`, `ROW`,
`Refused`, `repo_of`, `settings_of`, `read_settings`, `write_settings`,
`hook_cmd`, `is_guard`, `entries_of`, `guard_on`, `guard_off`, `guard_status`,
`COMMAND`, `command`), the `__main__` branch that runs a verb outside the
swallow-everything `try` so a command's error is its own, the three docstring
usage lines, the `FORWARD` row in `resources/pearde.py`, and the harness
`probe/verify.sh` (78 checks). **Left:** run the harness, tick the boxes.

Rules the build settled, so the implementer does not re-decide them:

- `<repo>` defaults to the parent of the nearest `prds/` above the cwd;
  outside every board the command refuses and names `pearde guard on <repo>`.
- The JSON edit is `json.loads` into a dict (insertion-ordered), keys added
  with `setdefault` semantics, written `indent=2`, `ensure_ascii=False`, one
  trailing newline. Every key not named here keeps its place. A file that is
  not JSON, or not an object, is refused with nothing written.
- An entry is "present" when an entry with the same `matcher` holds a hook
  whose command matches `guard\.py\s+<mode>\b` — any path, so a stale path
  is skipped, not duplicated, and `on` says nothing about it.
- `on` with nothing to add writes nothing and prints
  `guard on: <file> — already wired, nothing changed`.
- `off` drops an entry only when every hook in it is the guard's; a mixed
  entry keeps its other hooks. An event list emptied by `off` is dropped;
  `hooks` itself and `env.MAX_THINKING_TOKENS` stay. `off` with nothing to
  remove prints `guard off: <file> — not wired, nothing changed`.
- `status` exits 0 `ok`, 1 `off` (with doctor's fix line under the row), 2
  `broken` — the row's text is doctor.sh's `row()` format byte for byte.
- The hook command is `python3 <realpath of guard.py> <mode>` — the real
  path, so an install link rebuilt does not orphan the hook.
- `on` and `off` on a file written by hand with another indent are not
  byte-identical on the round trip: the first write normalises to
  `indent=2`. The probe's byte-identical case uses a 2-space file.

## Acceptance

- [x] `pearde guard on <tmp>` on a repo with no `.claude/` creates `<tmp>/.claude/settings.json` holding `env.MAX_THINKING_TOKENS = "8000"`, `PreToolUse` entries with matchers `Bash|Read` and `Edit|Write`, and a `PostToolUse` entry with matcher `Edit|Write`, each hook `{"type": "command", "command": "python3 <realpath guard.py> pre|post"}`; the file parses with `indent=2` and ends in one newline
- [x] the output names the file, one `  + ` line per thing added (four on a fresh file), and the sentence `a new settings file is read after /hooks or a restart`
- [x] a second `pearde guard on <tmp>` writes nothing (cksum unchanged) and prints `already wired, nothing changed`
- [x] `pearde guard off <tmp>` leaves `"hooks": {}` and the env key, prints three `  - ` lines; a second `off` prints `not wired, nothing changed`
- [x] on a settings file holding `permissions`, a foreign `PreToolUse` `Bash` entry, a foreign `PostToolUse` `Edit|Write` entry, `env.OTHER`, a non-ASCII value and a trailing unknown key, `on` keeps key order and the foreign entries, and `on` then `off` (the cap dropped by hand) leaves the file byte-identical
- [x] `on` never overwrites a `MAX_THINKING_TOKENS` already set
- [x] a settings file that is not JSON: `on` and `off` exit 1, say `refused — <file> is not JSON`, and the file is untouched
- [x] `pearde guard status <tmp>` prints the same line `bash resources/doctor.sh <tmp>` prints for `guard`, exits 0 when `ok`, 1 when `off`
- [x] with no `<repo>`, run from inside a board, the command writes the repo above that board; run outside every board it exits 1 with `no board above … — name the repo: pearde guard on <repo>` and creates nothing
- [x] `pearde help` lists `pearde guard on [<repo>]`, `pearde guard off [<repo>]` and a bare `pearde guard [<repo>]` line reading `doctor's guard row alone`; `python3 resources/pearde.py help` still exits 0
- [x] the command written into the file, run with a `find prds -name prd.md` hook payload, answers `"deny"`
- [x] `bash prds/the-tool-keeps-its-word/guard-on-is-one-command/probe/verify.sh` prints `78 checks · 78 pass · 0 fail` and exits 0; `prds/` holds no fixture afterwards; this repo's `.claude/settings.json` never gains a `guard.py` line

## Verify and Proof

```sh
bash prds/the-tool-keeps-its-word/guard-on-is-one-command/probe/verify.sh
python3 resources/pearde.py help | grep -n 'pearde guard'
python3 resources/pearde.py guard --help
python3 -c "import ast; ast.parse(open('resources/guard.py').read()); ast.parse(open('resources/pearde.py').read())"
```
