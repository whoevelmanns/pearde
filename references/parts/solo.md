# Without parallel workers

The same seven rows, `workers=1`, `pipeline=1`, and the brief followed by hand
— @references/parts/loop.md is the table, this is what changes in it.

| step | command | by hand |
|---|---|---|
| 1 scan | `pearde scan` · `pearde sweep` | — |
| 2 answer | `pearde answer <prd> Q<n> "<text>"` | — |
| 3 refine | `pearde refine <prd> < split` | the `## Split` table is yours to write |
| 4 spec ahead | `pearde claim <prd> <you>` · `pearde brief <prd>` | run the analyst's brief as a checklist, then `pearde specced <prd> --blast <x>` |
| 5 implement | the same two commands | run the implementer's brief; tick each box as you close it |
| 6 collect | `pearde collect <prd>` | — |
| 7 drill, then stop | as the loop | — |

A `workflow:` on the PRD is a route you follow yourself, so you write the
edit at the step that failed instead of collecting it: there is no report to
read, and no second reader to hand it to. Apply or refuse per whose fault the
failure was, as the loop does — applied for the atomic's fault, refused for
the code's or the PRD's; `runs` +1 on the workflow and every atomic that ran;
the text you wrote at the step: paste it or refuse it, never rewrite it;
`pearde workflow check`, then the collect — @references/parts/workflows.md.

Every rule holds: one writer per file, the gate is the command, work flows to
the leaves.
