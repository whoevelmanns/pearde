# Without parallel workers

The same loop, single-file — effectively `workers=1`, `pipeline=1`.

1. Scan.
2. Answer.
3. Refine.
4. Pick the highest-priority actionable PRD.
5. Run its brief yourself as a checklist — analyst for `open`, implementer for
   `specced`, both in `@@workers` — writing the transition before and after.
6. Print the progress line.
7. Repeat.

Every rule holds: one writer, verify before `done`, work flows to the leaves.
