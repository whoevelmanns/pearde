---
state: done
origin: requested
priority: 68
complexity: 10
blast-radius: mid
repo: pearde
workflow: probe-then-spec
footprint:
  - resources/guard.py
  - references/parts/guard.md
  - references/install.md
  - prds/memos/the-install-is-live-symlinks.md
  - resources/doctor.sh
  - prds/the-tool-keeps-its-word/guard-on-is-one-command/probe/verify.sh
  - prds/the-board-runs-itself/the-loop-is-commands/probe/verify.sh
actual: 0.11h
commit: 7dfdcfd
---

# the-skill-tree-is-guarded — a round on another board cannot write the skill through the install

When this is done, a session whose board is not this repo's cannot Edit or
Write a file under this repo through the symlinked install: `guard.py pre`
refuses, names the real path the link resolves to, names
`prds/memos/the-install-is-live-symlinks.md`, and says what to do instead —
file a PRD on the skill's own board, or hand the edit to a session working it.

## The consequence, named

`prds/memos/the-install-is-live-symlinks.md`: the install is file-by-file
symlinks into this repo, so a pearde round on `dotfiles` that corrected the
progress term wrote six files here, uncommitted, and two sessions on this
board spent two days attributing that and two row moves to a third writer.
The memo names this guard row as the cheapest honest fix and leaves it
untaken. The guard already sees every Edit and Write and already resolves a
file to its real path (a reference read through a link is keyed by its real
path, per @references/parts/guard.md).

## The rule

- On `pre` for an Edit or Write whose `file_path` resolves (through any
  symlink) to a path under the skill root — the directory holding
  `guard.py`'s own `resources/` — the guard compares that root with the
  board the session works (the nearest `prds/` above the working directory,
  the way `find_board` does). Not the same repo: deny, with the real path,
  the memo, and the two ways out. The same repo: pass, as today.
- A session with no board in scope (the working directory is this repo, or
  nowhere) passes — the guard refuses only a round that is provably
  another board's.
- Bash writes are not matched — the guard's `Bash` hook is a reader's check;
  say so in `guard.md` rather than pretend.
- `doctor`'s `guard` row, when `ok`, says `skill tree guarded`; the block
  `pearde guard on` writes is unchanged — the rule lives in `pre`.

## Files

| file | change |
|---|---|
| `resources/guard.py` | the check in `pre` for Edit/Write; the deny text |
| `references/parts/guard.md` | the row in the refusals table; the Bash caveat |
| `references/install.md` | one sentence beside the links: the guard refuses a write through them from another board |
| the memo | `status: decided`, the road taken |

## Verify

- Hook JSON on stdin in a temp project whose `prds/` is a copy of the example board, with `PEARDE_GUARD_STATE` in a temp dir: an Edit of `<skills-dir>/pearde/README.md` (a symlink into this repo) is denied naming `/Users/feb/dev/infra/pearde/README.md` and the memo; an Edit of a file under that project's own `prds/` passes; the same Edit from a working directory inside this repo passes.
- `the-loop-is-commands` (60), `tokens-per-transition` (42), `guard-on-is-one-command` (78) green, or each moved line named.
