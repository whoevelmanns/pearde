# States

The nine states, what sets each, and what a tenth one means.

| state       | meaning                                   | set by                         | leaves via                                    |
|-------------|-------------------------------------------|--------------------------------|------------------------------------------------|
| `open`      | claimable for analysis                    | user / orchestrator            | analyst dispatched → `analyzing`               |
| `analyzing` | analyst working out what to do            | orchestrator                   | analyst returns → `specced` \| `refine` \| `question` |
| `refine`    | needs a sub-PRD split or more detail      | orchestrator (analyst verdict) | children created → `open`                      |
| `question`  | blocked on the user                       | orchestrator (analyst verdict) | answers written → `open`                       |
| `specced`   | specs exist, ready to implement           | orchestrator                   | implementer dispatched → `claimed`             |
| `claimed`   | implementer working it                    | orchestrator                   | returns → `done` \| `failed`                   |
| `blocked`   | work done, boxes waiting on a named event | orchestrator                   | the event lands → `claimed` \| `done`          |
| `done`      | specs implemented and verified            | orchestrator                   | terminal                                       |
| `failed`    | attempt failed, needs revisit             | orchestrator                   | `retry <prd>` → `open`                         |

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
