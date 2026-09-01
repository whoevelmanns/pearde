# Without parallel workers

`workers=1`, `pipeline=1`, and the brief followed by hand. The seven steps do
not change — @references/parts/loop.md is the table, and it is the one to
read. Four of the rows are already what a solo round does; these three are
what changes in them.

| step | by hand |
|---|---|
| 3 refine | the `## Split` table is yours to write, then `pearde refine <prd> < split` |
| 4 spec ahead | after `pearde claim` and `pearde brief`, run the analyst's brief as a checklist, then `pearde specced <prd> --blast <x>` |
| 5 implement | the same two commands, then run the implementer's brief; tick each box as you close it |

A `workflow:` on the PRD is a route you follow yourself, so you write the
edit at the step that failed instead of collecting it: there is no report to
read, and no second reader to hand it to. Apply or refuse per whose fault the
failure was, as the loop does — applied for the atomic's fault, refused for
the code's or the PRD's; `runs` +1 on the workflow and every atomic that ran;
the text you wrote at the step: paste it or refuse it, never rewrite it;
`pearde workflow check`, then the collect — @references/parts/workflows.md.

Every rule holds: one writer per file, the gate is the command, work flows to
the leaves.
