# Weight and order

Three axes decide what runs next. None of them is a clock.

1. **Dependency** — `needs:` all `done`, and no footprint overlap with a
   `claimed` PRD. A hard gate: an unready PRD is not a candidate at all.
2. **Vision importance** — `priority`, higher first. How much this matters to
   what the project is *for*, argued in the PRD body. Not how long it takes.
3. **Complexity and blast-radius** — `complexity` 1-100 is the weight the
   progress line and `plan` use. `blast-radius` breaks ties and decides what a
   round leads with: a `high` PRD that is wrong costs more than a `low` one
   that is late.

The analyst scores `complexity` and `blast-radius` at spec time, from the specs
it just wrote — how many units, how much is unknown, how much of the tree they
touch. The orchestrator writes them on the SPECCED transition.

### No axis is a clock

`actual:` is a record and nothing reads it. `est:` is a fallback: a PRD with
no `complexity` is weighed by its `est` rather than dropping to the board
average. Nothing asks an analyst to produce one, and no round reports hours
left — wall-clock is a function of token throughput, tool latency and
contention, not a property of the work.

The weight of one PRD, first that answers:

1. its specs — each spec's `complexity`, or that spec's `est`, summed
2. its own `complexity`
3. its own `est`
4. the average weight of every scored PRD on the board
5. `weight-default` from `prds/settings.md`, when nothing is scored

A parent with live children weighs zero — the work is in the children, and
weighing it too counts the same work twice. A held PRD weighs what is LEFT of
it, floored at a twentieth.

**Compute cost belongs in the spec that spends it.** GPU seconds, API calls, a
sweep priced from cached timings: real, predictable, and a legitimate reason to
scope a spec down or refuse a cell. That is a *scope* decision inside a spec,
never a *schedule* decision on a board.
