---
complexity: 5
workflow: implement-a-spec
footprint:
  - resources/install.sh
  - references/install.md
---

# spec03 — `install --apply` prints the alias line, and `install.md` says so

`bash resources/install.sh --apply <skills-dir>` ends with one line the
reader may paste into their shell —
`alias pearde='python3 <repo>/resources/pearde.py'` — and writes nothing
outside the skills directory. `references/install.md` carries the same line
once. Needs spec02: the alias names a file that must exist.

## What already stands

Nothing in the tree. The probe did not edit `install.sh` because the file it
aliases was still under `probe/`. The exact edits are below.

## What is left

1. `resources/install.sh`, in the final `case "$MODE"`: the `apply)` branch
   prints, after its `built.` / `already built` message, two lines:

   ```
   echo "  one word for every tool — add to your shell, nothing here writes it:"
   echo "  alias pearde='python3 $ROOT/resources/pearde.py'"
   ```

   `$ROOT` is already the repo's absolute path in that script. Report mode
   and `--remove` print no alias.
2. The usage block at the top of `install.sh` gains no line — the alias is
   output, not an option.
3. `references/install.md`, section `## What installing means`, after the
   `bash @resources/install.sh --remove …` code block, one bullet:
   `- **One word.** \`--apply\` prints \`alias pearde='python3 <repo>/resources/pearde.py'\` — add it to your shell yourself. Nothing here writes a shell file. Every skill file names the same \`python3 @resources/pearde.py <cmd>\` line, so the alias and the skills are one surface.`
4. `references/install.md` section `## Uninstall` gains, at the end of its
   first paragraph: `Drop the alias from your shell file — it was yours to
   add.`

## Acceptance

- [x] `bash resources/install.sh --apply <tmpdir>` prints exactly one line matching `alias pearde='python3 .*/resources/pearde.py'`, and the path inside the quotes exists
- [x] `bash resources/install.sh <tmpdir>` (report mode) and `--remove <tmpdir>` print no `alias` line
- [x] after `--apply` then `--remove` on a fresh temp dir, the temp dir is empty — nothing was written anywhere else by the run
- [x] `grep -c "alias pearde=" references/install.md` prints 1 — the bullet; the uninstall line says "the alias" and carries no second copy of the command
- [x] `python3 resources/index.py check` prints no line naming `references/install.md` or `resources/install.sh`

## Verify and Proof

```sh
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
bash resources/install.sh --apply "$T" | grep -c "alias pearde='python3 .*/resources/pearde.py'"
A=$(bash resources/install.sh --apply "$T" | sed -n "s/.*alias pearde='python3 \(.*\)'/\1/p"); ls -l "$A"
bash resources/install.sh "$T" | grep -c alias; bash resources/install.sh --remove "$T" | grep -c alias
ls -A "$T" | wc -l
grep -n "alias pearde" references/install.md
python3 resources/index.py check | grep -c "install\.\(md\|sh\)"
```
