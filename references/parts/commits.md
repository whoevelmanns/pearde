# Commits

One PRD, one commit, on the transition that lands it.

Commit on the transition — otherwise one working tree holds every PRD's work,
and nothing can be reviewed, reverted, or bisected on its own.

The orchestrator commits. Never a worker — two implementers committing in
parallel write each other's half-finished files into each other's commits.

| transition          | do                                                              |
|---------------------|------------------------------------------------------------------|
| `claimed → done`    | commit                                                           |
| `claimed → blocked` | commit — the work is done, the open boxes wait on something named |
| `blocked → done`    | commit what closing the boxes wrote                              |
| `claimed → failed`  | nothing. Name the dirty paths in the report, leave them on disk  |

Board state written between transitions — answers, a refine split, a memo —
rides the next commit.

**Scope: the footprint, never the tree.** Add the union of the specs'
`footprint:` and the PRD's own, plus the PRD's folder. Never `git add -A`,
never `git commit -a` — step 5 already proved no other `claimed` PRD writes
that footprint.

- **The inherited tree is not the board's.** Step 1 records what is dirty
  before the round starts. Those paths are never added, whatever footprint
  they fall in. Name them once in the round.
- **A path the worker wrote outside its footprint is a wrong footprint.**
  Commit it with the rest and say so.

**Gate first.** Commit only what the `done` gate passed: verify output in the
report, every box `[x]`, spot-checks run. A red tree is a `failed` PRD, and a
`failed` PRD does not commit.

**Message.** Subject `<prd> — <what landed>`, one line per spec, `prd:` naming
the folder:

```
<prd> — <the PRD's contract in one line>

<specNN>: <goal>
<specNN>: <goal>

prd: prds/<path>
```

Write the sha to `commit:` on the PRD, beside `actual:` — the only link from a
`done` PRD to its code, and where `retry` on a regression starts.

**One commit per repo the PRD wrote.** A PRD with `repo:` elsewhere writes
code there and its record on the board: commit each where it lives, same
subject. On a master board that is the member's repo.

**Never push.** The commit is the board's, the push is the user's. Report what
is ahead and stop.

`commits: off` in `prds/settings.md` holds all of it — each transition then
names its dirty footprint. While on, a `*<dirty>` count climbing across rounds
is a board whose commits are not landing.
