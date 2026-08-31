# States

The nine states, what sets each, and what a tenth one means.

| state       | meaning                                   | set by                         | leaves via                                    | command |
|-------------|-------------------------------------------|--------------------------------|------------------------------------------------|---------|
| `open`      | claimable for analysis                    | user / orchestrator            | analyst dispatched → `analyzing`               | `add <title>` · `answer <prd> Q<n> "<text>"` on the last question · `retry <prd>` · `release <prd> open` |
| `analyzing` | analyst working out what to do            | orchestrator                   | analyst returns → `specced` \| `refine` \| `question` | `claim <prd> <worker>` · `sweep --apply` → `open` when silent past `claim-ttl` |
| `refine`    | needs a sub-PRD split or more detail      | orchestrator (analyst verdict) | children created → `open`                      | `release <prd> refine` |
| `question`  | blocked on the user                       | orchestrator (analyst verdict) | answers written → `open`                       | `release <prd> question` — gate: a `## Questions` round `questions.py check` accepts |
| `specced`   | specs exist, ready to implement           | orchestrator                   | implementer dispatched → `claimed`             | `specced <prd> --blast <x>` — gate: every `specs/*.md` accepted, weight summed · `unblock <prd>` — gate: `needs:` all `done` |
| `claimed`   | implementer working it                    | orchestrator                   | returns → `done` \| `failed`                   | `claim <prd> <worker>` · `sweep --apply` → `failed` when silent past `claim-ttl` |
| `blocked`   | work done, boxes waiting on a named event | orchestrator                   | the event lands → `specced`                     | `release <prd> blocked` — gate: `needs:` |
| `done`      | specs implemented and verified            | orchestrator                   | terminal                                       | `collect <prd>` — gate: every box closed in both files, every `## Verify and Proof` block and the board's `gate:` green |
| `failed`    | attempt failed, needs revisit             | orchestrator                   | `retry <prd>` → `open`                         | `release <prd> failed` — gate: `## Failure` |

**The command is the gate.** Every `state:` above is written by one of the
commands in the last column — @resources/board/transitions.py,
@resources/board/specs.py, @resources/board/collect.py, `pearde <command>` —
and each checks its gate before it writes, prints the progress
line of @references/parts/progress.md, and exits 1 naming the gate when the
table forbids the move. `claim` runs `plan.dispatchable`, the one predicate
loop steps 4 and 5 and `scan`'s ready band read, so what `scan` offers is
what `claim` takes: unclaimed; leaf — every child `done`, and a parked child
holds its parent (`leaf: … held by <child> (parked)`, listed under `gated`,
never ready); container — children all `done` and no specs or open box of
its own, which `collect` closes and `claim` refuses (`container:`); `needs:`
all `done`; no footprint overlap with a `claimed` PRD; `workflow:` resolves.
`defer <prd>` writes the parked `deferred` below.
`set <prd> <state> --force` writes any transition and says `forced` on the
line — the escape hatch, never the path. The view's drag calls the same
function forced, and its line says `forced · view`.

`blocked` vs `failed` — whose problem the open box is:

- `failed` — the attempt did not produce the work. A worker that guessed, or
  whose own checks are red, is `failed`.
- `blocked` — the work is done, and a box it cannot close waits on something
  named. Carries `needs:`. The body says which boxes are open and what closes
  each.
  It is live work — counted in the progress line and the plan, never blindly
  retried.

Never reach for `blocked` to avoid a hard `failed`.

A `state` outside this table is the user's own and **parked**: never
dispatched, never scheduled by `plan`, out of the progress line and the status
line, not folded into `open`. Report parked PRDs by name — neither progress
nor backlog. A parked child holds its parent: it is neither done nor coming,
so the parent is not dispatchable until that child is `done`.
`release <prd> open` is the way back — the one target: it clears `claim:` and files the PRD as claimable work; a parked container is `collect`'s, and `release` says so.

**Parked on a person owes a round.** A parked state, or a `mode:`, that names
a human — `hitl`, `waiting`, `user` — makes `question`'s claim without
`question`'s obligation: the board is stopped and nobody wrote down what is
being asked. Whichever word it uses, it carries `## Questions` in the format
of @references/drill.md, and step 2 of the loop puts it to the user with the
`question` PRDs. `doctor`'s `questions` row is that rule as a check.
