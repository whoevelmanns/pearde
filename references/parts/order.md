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

`est:` and `actual:` are **legal, optional, and read by no decision**. A run
that measures itself cheaply may record it, for a human reading back. Nothing
asks an analyst to produce one. No round reports hours left — wall-clock is a
function of token throughput, tool latency and contention, not a property of
the work.

**Compute cost belongs in the spec that spends it.** GPU seconds, API calls, a
sweep priced from cached timings: real, predictable, and a legitimate reason to
scope a spec down or refuse a cell. That is a *scope* decision inside a spec,
never a *schedule* decision on a board.
