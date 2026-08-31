---
complexity: 3
footprint:
  - references/language.md
  - skills/pearde.md
  - index.md
---

# spec02 — the three files beside the README still point at it

The README moved its two tables under **Three rings**, and the agent-read
files that name the README follow it. `references/language.md` says who the
README is for, `skills/pearde.md` says where the table it opens with now
lives, and `index.md` is checked to still resolve — it never anchored into a
README heading, so it does not change.

## What stands from the probe

- `references/language.md`: the row `| README | a person, first time |
  quickstart, then rings |` in **Shape per document**, and one sentence
  under the table — the README is the one document where a sentence may
  carry two ideas.
- `skills/pearde.md`: its first line reads "Read @README.md — its **One
  question, one file** table, under **Three rings** as the core ring, is
  what to open next".
- `index.md`: untouched. `grep -r 'README.md#'` over `references/`,
  `skills/`, `index.md` and `SKILL.md` finds nothing, so no anchor follows a
  heading.
- `probe/verify.sh` section G checks all three.

## What is left

Nothing to write. Run the checks; `references/files.md` keeps its
`@README.md` row as it is — no file moved.

## Acceptance

- [x] `grep -c '^| README ' references/language.md` prints `1`
- [x] `sed -n 6p skills/pearde.md` starts `Read @README.md` and lines 6-8 name `**Three rings**`
- [x] `python3 resources/index.py check` prints nothing and exits 0
- [x] `bash resources/doctor.sh` prints `index ok` and `skills ok`

## Verify and Proof

```sh
grep -c '^| README ' references/language.md
sed -n '6,8p' skills/pearde.md
python3 resources/index.py check
bash prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh --no-run
```
