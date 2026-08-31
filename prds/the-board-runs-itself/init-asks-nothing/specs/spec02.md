---
complexity: 6
footprint:
  - resources/doctor.sh
  - references/settings.md
  - references/install.md
---

# spec02 — `doctor` names `pearde init`, and a missing `language:` reads English

The three text edits the PRD's Files table asks for. All three stand in the
tree from the probe, uncommitted; this unit is the check that they say what
the memo decided, and the commit of them.

## What stands from the probe

- `resources/doctor.sh`, `board` row — three hunks, disjoint from the
  `briefs` row a sibling added at lines 370–394:
  - line 193: `board off` reads `no board — pearde init creates prds/` and
    carries a `fix:` line naming `python3 <root>/resources/pearde.py init [<dir>]`.
  - line 206: the `no settings.md` row is still `broken`; its `fix:` line
    names `pearde.py init <dir>` and says `language English unless --language`.
  - lines 208–211: a `settings.md` with no `language:` is `board ok … language
    English (default)` — the branch that read it as `broken` is gone.
- `references/settings.md`: the block's `language:` reads `English`; the
  `language` row's default is `English` and names `pearde init` and
  `pearde settings language=<l>` and the memo; the Write table's first row is
  `pearde init` and the `workers=N` row is `pearde settings workers=N`; the
  four-step first run is one paragraph naming `pearde init` and
  `@resources/board/init.py`. The sentence `stated by the user, never
  guessed` is gone from this file.
- `references/install.md`: `## The first run` is `pearde init` and what it
  leaves, and still says nothing about installing touches `prds/`.

## What is left

Nothing to write. Read the three diffs against the memo
`prds/memos/init-defaults-the-language.md`, run the block, tick the boxes.
The sentence in `references/parts/loop.md` (step 1, lines 52–55) and
`references/system.md:26` is outside this footprint — it is a row in the
analyst's report, for `the-loop-is-commands` or the orchestrator.

## Acceptance

- [x] `bash resources/doctor.sh <dir with no prds/>` prints a `board off` row whose next line contains `pearde.py init`
- [x] `bash resources/doctor.sh <dir whose prds/settings.md has no language:>` prints `board ok … language English (default)` and no `broken` board row
- [x] `bash resources/doctor.sh <dir whose prds/ has no settings.md>` prints `board broken … no settings.md` with a `fix:` line containing `pearde.py init`
- [x] `grep -c 'never guessed' references/settings.md references/install.md` is `0` for both, and `grep -c 'pearde init' references/settings.md references/install.md` is at least `1` for both
- [x] `bash -n resources/doctor.sh` exits 0 and `bash resources/doctor.sh` on this repo still prints `board ok`

## Verify and Proof

```sh
bash -n resources/doctor.sh
T=$(mktemp -d); mkdir -p "$T/nolang/prds" "$T/nosettings/prds" "$T/empty"
printf -- '---\nworkers: 2\n---\n' > "$T/nolang/prds/settings.md"
PEARDE_PORT=1 bash resources/doctor.sh "$T/empty"      | grep -A1 '^  board *off'    | grep -c 'pearde.py init'
PEARDE_PORT=1 bash resources/doctor.sh "$T/nolang"     | grep -c '^  board *ok .*language English (default)'
PEARDE_PORT=1 bash resources/doctor.sh "$T/nosettings" | grep -A1 'no settings.md'   | grep -c 'pearde.py init'
rm -rf "$T"
grep -c 'never guessed' references/settings.md references/install.md
grep -c 'pearde init' references/settings.md references/install.md
bash resources/doctor.sh | grep '^  board'
```
