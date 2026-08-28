---
name: pearde-master
description: Plan across several repositories at once — one parent board that names other boards as members, scans them all, and returns a single ordered plan and one timeline over the merged set. The members stay where they are, boards in their own right; nothing is copied and no file in a member moves. Use for "/master", "plan across projects", "plan over several repos", "one board for all my projects", "master board", "add <path> as a member", "what does this master merge", "combine these boards", "portfolio view of my work".
---

Read @references/parts/master.md — it is the contract. The scopes are
`@@master` and `@@settings`.

```yaml
# <parent-repo>/prds/settings.md
name: <what the group is called>
members:
  - ../mitosys/prds
  - ../model/prds
```

- **Naming is the whole install.** `master <path> …` appends to `members:`
  and asks the group's `name:` the first time. It creates nothing in a member.
- **Run the round in the parent from then on.** The merged scan, the merged
  plan, one timeline. `python3 @resources/pearde.py members [board]` lists
  every member with its path, and `MISSING` where it is not on disk.
- **A missing member is the failure that matters**: the plan loses a whole
  project silently, and the board reads as smaller rather than broken.
  `pearde doctor` grows a `members` row on a master board.
