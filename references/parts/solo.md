# Without parallel workers

The same loop, single-file — effectively `workers=1`, `pipeline=1`.

1. Scan.
2. Answer.
3. Refine.
4. Pick the highest-priority actionable PRD.
5. Run its brief yourself as a checklist — analyst for `open`, implementer for
   `specced`, both in `@@workers` — writing the transition before and after.
   A `workflow:` on the PRD is a route you follow yourself, so you write the
   edit at the step that failed instead of collecting it: there is no report to
   read, and no second reader to hand it to. Rules 2 to 5 of step 6 still hold
   — apply or refuse per whose fault the failure was, `runs` +1, `check`, then
   the commit — @references/parts/loop.md.
6. Print the progress line.
7. Repeat.

Every rule holds: one writer, verify before `done`, work flows to the leaves.
