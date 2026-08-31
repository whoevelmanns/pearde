---
complexity: 5
footprint:
  - resources/board/plan.py
  - resources/board/transitions.py
  - references/parts/progress.md
  - references/parts/statusline.md
  - resources/statusline.sh
  - README.md
  - prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh
  - prds/the-board-runs-itself/specced-is-a-command/probe/verify.sh
  - prds/nothing-left-open/the-line-tells-the-truth/probe/verify.sh
---

# spec03 — the first term of the line is `done`: the rename adopted whole, its two matchers re-aimed

`asked` counted a container whose children all landed as outstanding. The
rename that fixes it sits uncommitted in the tree — six files, one idea:
`plan.py` `progress_terms` key `"asked"` → `"done"` and `cmd_scan`'s use of
it, `transitions.py` `progress_line`, and the term tables and examples in
`progress.md`, `statusline.md`, `statusline.sh`'s header comment, and the
README's `add` row. `<ad>/<an>/<ap>` become `<rd>/<rn>/<rp>`. It is adopted
as it stands; nothing else in those files moves. The two committed
harnesses that pinned the old word read `done`.

## What already stands

- Every hunk of `git diff HEAD -- resources/board/plan.py
  resources/board/transitions.py references/parts/progress.md
  references/parts/statusline.md resources/statusline.sh README.md` that
  spells `asked`/`ad`/`an`/`ap` — the analyst read each; all are the rename.
  Not the rename and left alone: `plan.py`'s mode flip `100644 → 100755` in
  that same diff.
- `transitions-are-commands/probe/verify.sh:74` (`the line opens with the
  transition`) and `specced-is-a-command/probe/verify.sh:126` match `· done`.
  Those harnesses read 65/74 and 90/90 after the re-aim — the transitions
  count was 64/74 before it; its nine remaining reds are another session's
  `answer` work, named in the analyst's report.
- No reader of the old key is left under `resources/`, `references/` or in
  `README.md` — the probe's C7 greps for it.
- The probe's section C, 7 checks, green.

## What is left

Nothing to write. The implementer confirms the six files' hunks are still
only the rename at collect time — `git diff -U0 HEAD -- <the six>` — and
that the committed harnesses read the counts below. A hunk in those files
that is not the rename is somebody else's and is named, not taken.

## Acceptance

- [ ] `python3 resources/board/plan.py scan <copy>/prds` prints a line opening `progress: done ` and no line holding `asked`
- [ ] `set next claimed --force --as engineer --board <copy>/prds` prints `▸ next: open → claimed · forced · done <rd>/<rn> · <rp>% · …`
- [ ] From the copy's root, `echo '{}' | bash resources/statusline.sh` renders `▸pearde <rd>/<rn>` with the same `<rd>/<rn>` scan printed
- [ ] `grep -rl -E '"asked"|<ad>|asked [0-9]+/[0-9]+' resources references README.md` prints nothing
- [ ] `bash prds/the-board-runs-itself/specced-is-a-command/probe/verify.sh` prints `90/90 checks pass`
- [ ] `bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh` passes `the line opens with the transition`
- [ ] `git diff HEAD -- README.md references/parts/progress.md references/parts/statusline.md resources/statusline.sh` holds only hunks spelling `asked`→`done` or `<ad>/<an>/<ap>`→`<rd>/<rn>/<rp>`

## Verify and Proof

```sh
bash prds/nothing-left-open/the-line-tells-the-truth/probe/verify.sh </dev/null
grep -rl -E '"asked"|<ad>|asked [0-9]+/[0-9]+' resources references README.md || echo no-old-key
bash prds/the-board-runs-itself/specced-is-a-command/probe/verify.sh </dev/null | tail -1
bash prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh </dev/null | grep 'the line opens with the transition'
```
