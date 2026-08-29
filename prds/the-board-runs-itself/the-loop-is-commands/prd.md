---
state: done
origin: requested
actual: 2.1h
commit: 7a664bf
priority: 58
complexity: 31
blast-radius: mid
repo: pearde
workflow: probe-then-spec
needs:
  - transitions-are-commands
  - specced-is-a-command
  - collect-is-a-command
  - brief-is-printed
  - init-asks-nothing
footprint:
  - references/parts/loop.md
  - references/parts/solo.md
  - references/parts/round.md
  - references/parts/guard.md
  - references/parts/states.md
  - references/parts/workers.md
  - references/parts/commits.md
  - references/parts/progress.md
  - references/parts/handles.md
  - references/drill.md
  - references/settings.md
  - resources/guard.py
  - resources/board/transitions.py
  - README.md
  - references/system.md
  - resources/pearde.py
  - prds/the-board-runs-itself/transitions-are-commands/probe/verify.sh
  - prds/the-board-runs-itself/one-command/probe/verify.sh
  - prds/workflows-on-the-board/workflow-attach/probe/verify.sh
  - prds/workflows-on-the-board/workflow-improve/probe/verify.sh
---

# the-loop-is-commands — the round is written as the calls it makes, on one page

When this is done, @references/parts/loop.md is under 120 lines, every step
names the one command it runs and the one decision the orchestrator makes
between commands, and every rule a command now enforces has left the prose.

## Contract

| step | command | the orchestrator decides |
|---|---|---|
| 1 scan | `pearde scan` · `pearde sweep` once per session · read `prds/.round.md` · `pearde init` when there is no board | nothing — read |
| 2 answer | `pearde answer <prd> Q<n> "<text>"` per answer | what to put to the user, per @references/drill.md, and what they said |
| 3 refine | `pearde refine <prd> < report` | whether the analyst's table is usable; a drill when it is not |
| 4 spec ahead | `pearde claim <prd> <worker>` · `pearde brief <prd>` → dispatch | which persona the job wears |
| 5 implement | the same two commands | which persona the job wears |
| 6 collect | read the report · apply or refuse `## Workflow` edits · `pearde collect <prd>` | whether to believe the report; whether an edit was the atomic's |
| 7 drill, then stop | one drill round over the frontier · rewrite `prds/report.md` and `prds/.round.md` · `pearde view wait` | the forks and their three answers |

What leaves `loop.md`, because a command refuses it: the three dispatch
skips, the finished condition and the box spellings, the seven collect
actions, the pipeline count, "never take a worker's word". What stays: the
three token rules at the head, the judgement in the right-hand column, and
the pointers.

`pearde sweep [--apply]` lists every claim silent past `claim-ttl` — default
30 minutes, a `settings.md` key — where silent means the newest mtime over
the PRD directory **and** every path of the PRD's footprint union in `repo`
(the same union `collect` computes) is older than that: an implementer works
in the repo and an analyst's probe lives in the PRD folder, and either moving
is a live worker. `--apply` moves `analyzing → open` and `claimed → failed`,
reading a swept worker's report first as step 1 says, and never a claim
another session's `.round.md` names. `the-page-shows-the-round` draws the
same rule from `plan.py`.

## Rules

- **The guard refuses a hand-written state where it is wired.** A
  `PostToolUse` hook runs after the bytes land, so this is a new
  `PreToolUse` matcher on `Edit|Write` — `guard.py pre` reads the tool input,
  and an edit that changes the `state:` line of a `prd.md` is denied with
  `use pearde set`. The block in @references/parts/guard.md grows the
  matcher, and the reader wires it as they wire the rest — doctor reports it,
  never writes it. It is a mechanism exactly where a person has wired it and a
  sentence everywhere else, and the prose says which. `transitions.py` writes
  through `edit.py`, not through a tool call, so it is never matched.
- **The drill writes its tree through `pearde refine`.** @references/drill.md
  § Output and `skills/pearde-drill.md` say so; a hand-made `state: open`
  would be the edit the matcher refuses.
- `solo.md` is the same seven rows with the brief followed by hand; still
  under 25 lines.
- `round.md` loses nothing — the round file is still what the tool cannot
  know. Its `## Established` gains one line: the progress line is printed by
  every command, so it is never computed by hand.
- The README's loop table is the seven rows above.
- **Delete, do not deprecate.** A sentence a command enforces is removed from
  every part it stood in, in this PRD's commit — @references/language.md.

## Files

| file | change |
|---|---|
| `references/parts/loop.md` | rewritten to the table |
| `references/parts/solo.md` · `round.md` · `guard.md` | as above |
| `resources/guard.py` · `references/parts/guard.md` | the `PreToolUse` `Edit|Write` matcher and the refusal |
| `resources/board/transitions.py` | `sweep`, registered through `COMMANDS` |
| `references/settings.md` | `claim-ttl` |
| `references/parts/states.md` · `workers.md` · `commits.md` · `progress.md` | the sentence each command now enforces, deleted |
| `references/drill.md` | § Output writes the tree through `pearde refine` |
| `README.md` | the loop table |
| `references/parts/handles.md` | the `pending` marks cleared; `sweep` |

## Verify

- `wc -l references/parts/loop.md` ≤ 120; `solo.md` ≤ 25.
- A probe greps every `pearde <cmd>` in `loop.md` and runs `pearde <cmd>
  --help`: all exit 0.
- With the new matcher wired in a temp project's `.claude/settings.json`, a
  probe feeding `guard.py pre` an `Edit` tool input that changes `state:` in
  a `prd.md` gets a deny naming `pearde set`; the same input changing a body
  line passes; `pearde set` on the file is untouched by the hook.
- On a copy of the example board with `claim-ttl: 1m`, the copy's mtimes set
  two minutes back with `touch -d`, `pearde sweep` lists `building`;
  touching one footprint path in its `repo` removes it from the list;
  `--apply` on the stale one sets `failed`.
- `grep -ci "never take a worker" references/parts/*.md README.md` is 0 —
  it is 2 today (`states.md`, `README.md`).

## Report

DONE 25/25 · commit 7a664bf · probe 60/60 · attach 47/47 improve 71/71 transitions 74/74 one-command 54/54
