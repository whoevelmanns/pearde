# Weight and order

Three axes decide what runs next. None of them is a clock.

1. **Dependency** — `needs:` all `done`, and no footprint overlap with a
   `claimed` PRD. A hard gate: an unready PRD is not a candidate at all.
2. **The vision axis** — asap lanes first, then depth, then `priority`. A
   PRD declaring `axis: asap` in its frontmatter is a deliberate exception —
   the "see it working" ask — and dispatches before everything, by priority.
   On-axis PRDs dispatch deepest-first: the longest serial chain first,
   because every hour it waits is an hour added to the finish. `priority`
   breaks ties within a depth. A PRD off the axis dispatches after all
   on-axis work, by priority. The axis is `prds/.vision.json`, written by
   `prds/vision.py`.
3. **Complexity and blast-radius** — `complexity` 1-100 is the weight the
   progress line and `plan` use. `blast-radius` breaks ties and decides what a
   round leads with: a `high` PRD that is wrong costs more than a `low` one
   that is late.

The analyst scores `complexity` and `blast-radius` at spec time, from the specs
it just wrote — how many units, how much is unknown, how much of the tree they
touch. The orchestrator writes them on the SPECCED transition.

### No axis is a clock

`actual:` is a record the plan never schedules by. `est:` is a fallback: a
PRD with no `complexity` is weighed by its `est` rather than dropping to the
board average. Nothing asks an analyst to produce one, and no round reports
hours left — wall-clock is a function of token throughput, tool latency and
contention, not a property of the work.

The one clock the board does show is fitted, not estimated: `plan.py
calibrate` reads every done PRD carrying an `actual:` across every registered
board and fits one machine-wide constant — hours per unit of weight, as a
ratio of sums so a five-minute PRD cannot outvote a three-day one, with a
P20–P80 band from the per-PRD spread. Once fitted, every weight on the board
prints as tuned real hours — weight × the fit × `TUNE`, a hand-set margin
hard-coded in `plan.py` (1.618): raise it when the board keeps finishing
late, lower it when it keeps beating the number. A bad fit can
mislabel an axis; it can never re-order the work — precisely because `est`
and `actual` stay out of the schedule, nobody ever had a reason to game them,
which is what makes them honest calibration data. Refit as `actual:` records
accumulate; the fit is dated and lives in `resources/board/state/`.

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
