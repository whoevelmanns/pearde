---
workflow: add-a-file-to-the-skill
subject: a new file under references/ or resources/, from the file to a silent map
date: 2026-08-28
updated: 2026-08-28
runs: 2
---

# add-a-file-to-the-skill — a new file, and the two places that must point at it

## Use when

- A contract asks for a new reference page, a new script, a new template or a
  new config that ships with the skill.
- A file moves between roots, or is renamed — the same two pointers go stale.
- Not when the new file is a board file under `prds/` — the map skips `prds/`
  entirely, and a workflow or an atomic there is `add-a-contract-key` only if
  it also introduces a key.
- Not when the file already exists and only its text changes — that is
  `correct-a-documented-claim`.

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
| 1 | `read-the-contract` | fixes what the file must hold and which root it belongs under, before a path is chosen | `stop` |
| 2 | `place-the-file` | the root decides which scope rows and which checker branch ever see the file, so a wrong root is a rewrite and not a move | `→ 1` |
| 3 | `write-the-manifest-row` | nothing else in the tree points at a new file | `→ 2` |
| 4 | `sweep-for-other-copies` | older pages enumerate this root and now miss a member | `→ 3` |
| 5 | `run-the-repo-gate` | a map that disagrees with the tree is what fails for the next worker, not for you | `→ 3` |
