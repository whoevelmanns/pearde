# States

The nine states, what sets each, and what a tenth one means.

| state       | meaning                                   | set by                         | leaves via                                    | command |
|-------------|-------------------------------------------|--------------------------------|------------------------------------------------|---------|
| `open`      | claimable for analysis                    | user / orchestrator            | analyst dispatched → `analyzing`               | `add <title>` · `answer <prd> Q<n> "<text>"` on the last question · `retry <prd>` · `release <prd> open` |
| `analyzing` | analyst working out what to do            | orchestrator                   | analyst returns → `specced` \| `refine` \| `question` | `claim <prd> <worker>` |
| `refine`    | needs a sub-PRD split or more detail      | orchestrator (analyst verdict) | children created → `open`                      | `release <prd> refine` |
| `question`  | blocked on the user                       | orchestrator (analyst verdict) | answers written → `open`                       | `release <prd> question` — gate: a `## Questions` round `questions.py check` accepts |
| `specced`   | specs exist, ready to implement           | orchestrator                   | implementer dispatched → `claimed`             | `unblock <prd>` — gate: `needs:` all `done`. `specced` itself is `specced-is-a-command` |
| `claimed`   | implementer working it                    | orchestrator                   | returns → `done` \| `failed`                   | `claim <prd> <worker>` |
| `blocked`   | work done, boxes waiting on a named event | orchestrator                   | the event lands → `claimed` \| `done`          | `release <prd> blocked` — gate: `needs:` |
| `done`      | specs implemented and verified            | orchestrator                   | terminal                                       | `collect-is-a-command`; until it lands, `set <prd> done --force` |
| `failed`    | attempt failed, needs revisit             | orchestrator                   | `retry <prd>` → `open`                         | `release <prd> failed` — gate: `## Failure` |

**The command is the gate.** Every `state:` above is written by one of the
commands in the last column — @resources/board/transitions.py, `pearde
<command>` — and each checks its gate before it writes, prints the progress
line of @references/parts/progress.md, and exits 1 naming the gate when the
table forbids the move. `claim` runs the one test loop steps 4 and 5 share:
leaf, unclaimed, `needs:` all `done`, no footprint overlap with a `claimed`
PRD, `workflow:` resolves. `defer <prd>` writes the parked `deferred` below.
`set <prd> <state> --force` writes any transition and says `forced` on the
line — the escape hatch, never the path. The view's drag calls the same
function forced, and its line says `forced · view`.

Never take a worker's word for a transition. `specced` requires spec files on
disk. `done` requires the verify commands actually run with output in the
report — spot-check the cheap ones.

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
nor backlog.

**Parked on a person owes a round.** A parked state, or a `mode:`, that names
a human — `hitl`, `waiting`, `user` — makes `question`'s claim without
`question`'s obligation: the board is stopped and nobody wrote down what is
being asked. Whichever word it uses, it carries `## Questions` in the format
of @references/drill.md, and step 2 of the loop puts it to the user with the
`question` PRDs. `doctor`'s `questions` row is that rule as a check.
