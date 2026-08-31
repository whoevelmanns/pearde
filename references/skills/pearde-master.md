---
name: pearde-master
description: Plan across several repositories at once — one parent board that names other boards as members, scans them all, and returns a single ordered plan and one timeline over the merged set. The members stay where they are, boards in their own right; nothing is copied and no file in a member moves. Use for "/master", "plan across projects", "plan over several repos", "one board for all my projects", "master board", "add <path> as a member", "what does this master merge", "combine these boards", "portfolio view of my work".
---

Read @references/parts/master.md — it is the contract: what `members:` does,
how an entry is written and resolved, how a member PRD is addressed, what
stays on the member against what the master holds, and how the group is
named. The scopes are `@@master` and `@@settings`.

```bash
python3 @resources/pearde.py members [board]   # every member, its path, MISSING where it is not on disk
```

`master <path> …` appends to `members:` in the parent's `.pearde/settings.md`;
every round from then on is worked in the parent. A missing member is the
failure that matters — the plan loses a whole project silently, and the board
reads as smaller rather than broken — so `pearde doctor` grows a `members` row
on a master board.
