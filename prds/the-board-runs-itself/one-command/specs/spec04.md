---
complexity: 7
workflow: implement-a-spec
footprint:
  - resources/doctor.sh
---

# spec04 — two modules claiming one name is a `doctor` failure under `skills`

`doctor.sh`'s `skills` row turns `broken` when `pearde help` reports a
problem — a name two `resources/board/*.py` modules claim, a module claiming
a name `pearde.py` forwards, or a module that fails to import — and the note
under the row is the dispatcher's own line. Needs spec02.

Not in the PRD's `footprint:` — the PRD's `## Contract` names the doctor
failure and its footprint omits `resources/doctor.sh`. This spec's footprint
is the correction.

## What already stands

The dispatcher already detects all three problems and prints each on stderr
as `pearde: <problem>`, with `help` exiting 1 — the `# ── clash` block of
`@prds/the-board-runs-itself/one-command/probe/verify.sh` asserts the three
messages:

| seen | message |
|---|---|
| two modules, one name | `` `hello` is claimed by both hello.py and other.py `` |
| a module on a forwarded name | `` `scan` is forwarded by pearde.py and claimed by other.py `` |
| a module that does not import | `broken.py failed to import: …` |

Doctor reads none of it yet.

## What is left

1. In `resources/doctor.sh`, section `# ── skills`, after the per-file loop
   and before `if [ "$SKN" -eq 0 ]`:

   ```bash
   # One name, one module. pearde.py discovers resources/board/*.py and says
   # on stderr which names clash; a clash is a skill whose command answers
   # for the wrong file, so it is broken here rather than silently first-wins.
   CLASH=$(python3 "$SKILL_ROOT/resources/pearde.py" help 2>&1 >/dev/null | sed -n 's/^pearde: //p')
   [ -n "$CLASH" ] && SKBAD="$SKBAD
   $CLASH"
   ```

   The existing `elif [ -n "$SKBAD" ]` branch then reports the row as
   `broken` with the count and prints each line as a note. Its `fix` line
   becomes: `fix "frontmatter is what makes a skill findable — @references/install.md; one name per module under resources/board/ — python3 $SKILL_ROOT/resources/pearde.py help"`.
2. The header comment of `doctor.sh` (`# One part per line…`) gains, in the
   sentence listing what `skills` checks, the words `and every command name
   under resources/board/ is claimed by one module`.
3. No new row. The PRD says under `skills`, and a dispatcher that cannot
   route is an entry point that does not fire.

## Acceptance

- [x] on this tree, `bash resources/doctor.sh | grep "^  skills"` says `ok` and its note line is unchanged
- [x] in a temp copy of the repo with `resources/board/zz_clash.py` holding `COMMANDS = {"scan": lambda a: 0}`, the copy's `doctor.sh` prints `skills      broken  11 skills · 1 problem` and a note line reading `` `scan` is forwarded by pearde.py and claimed by zz_clash.py ``
- [x] in the same copy with a second module claiming a name the first already claims, the note names both files
- [x] the copy's `doctor.sh` exits 1 in both cases, and the `fix:` line names `pearde.py help`
- [x] every other row of the copy's report reads the same as before the fixture module was added

## Verify and Proof

```sh
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
rsync -a --exclude .git --exclude 'resources/board/state' --exclude __pycache__ ./ "$T/repo/"
bash resources/doctor.sh | grep "^  skills"
bash "$T/repo/resources/doctor.sh" > "$T/before.txt"; grep "^  skills" "$T/before.txt"
printf 'COMMANDS = {"scan": lambda a: 0}\n' > "$T/repo/resources/board/zz_clash.py"
bash "$T/repo/resources/doctor.sh" > "$T/one.txt"; echo "rc=$?"; grep -A2 "^  skills" "$T/one.txt"
printf 'def f(a): return 0\nCOMMANDS = {"zz": f}\n' > "$T/repo/resources/board/zz_a.py"; cp "$T/repo/resources/board/zz_a.py" "$T/repo/resources/board/zz_b.py"
bash "$T/repo/resources/doctor.sh" > "$T/two.txt"; echo "rc=$?"; grep -A3 "^  skills" "$T/two.txt" | grep -c "zz_a.py and zz_b.py"
diff <(grep -v "^  skills" "$T/before.txt" | grep "^  [a-z]") <(grep -v "^  skills" "$T/two.txt" | grep "^  [a-z]") && echo "other rows unchanged"
```
