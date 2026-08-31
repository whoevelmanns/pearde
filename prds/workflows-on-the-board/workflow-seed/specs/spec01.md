---
complexity: 26
workflow: implement-a-spec
footprint:
  - prds/workflows
---

# spec01 — the first library: five workflows over thirteen atomics

`prds/workflows/` holds the board's routes. This unit writes it: five workflows,
thirteen atomics, every atomic named by at least one workflow. The library was
seeded with every file at `runs: 0` so that the first collect would be the first
count. The jobs are read off this repo's own references — a workflow orders the
steps and cites the source, and the atomic names the commands.

**What already stands.** The probe wrote all eighteen files, and the first
collect has since landed on them: nine files read `runs: 1` and seven carry an
`updated:`. The acceptance below therefore measures what a collect preserves,
not the `runs: 0` moment a collect necessarily ends.
`python3 resources/workflows.py check prds` is silent, `list` prints 5 workflows
and 13 atomics, and `brief` renders each workflow with every atomic inlined
under its step. `bash resources/doctor.sh` reports
`workflows ok · 5 workflows · 13 atomics · the library checks out`.

| workflow                     | the job                                                          | the source                                            |
|------------------------------|------------------------------------------------------------------|--------------------------------------------------------|
| `add-a-file-to-the-skill`    | a new file under `references/` or `resources/`                   | @references/files.md · @index.md                       |
| `add-a-contract-key`         | a new frontmatter key, wired to a check that fails on it         | @references/parts/contract.md · @resources/memos.py    |
| `implement-a-spec`           | the implementer's route                                          | @references/parts/workers.md                            |
| `probe-then-spec`            | the analyst's route                                              | @references/parts/workers.md                            |
| `correct-a-documented-claim` | a wrong or ambiguous claim, corrected everywhere it is copied    | @references/parts/workflows.md · the sweep three PRDs this session lost runs to |

**What is left.** Read the eighteen files and judge the prose: a `## Do` step
that names no command, a `## Done when` bullet that cannot fail, or a `why`
clause that restates the atomic's `subject` is a defect to fix here. The
harness in spec03 measures the shape, not the sense.

## Acceptance

- [x] `python3 resources/workflows.py check prds` prints nothing and exits 0.
- [x] `python3 resources/workflows.py list prds` shows at least three rows of
      kind `workflow` and at least six of kind `atomic`.
- [x] Every file in `prds/workflows/` carries `runs:` as an integer >= 0, and
      the `runs` column of `list` never disagrees with that file's own `runs:`
      — the property a collect preserves, in place of the `runs: 0` a collect
      destroys.
- [x] Every `updated:` in the library is an ISO date, and none predates its own
      file's `date:`.
- [x] Every atomic file in the directory is named in at least one workflow's
      `## Steps` table — enumerated from the directory, not from a list.
- [x] Every step cell names a file that exists and is an atomic, never a
      workflow.
- [x] `python3 resources/workflows.py brief <slug> prds` exits 0 for every
      workflow and prints one `### N — <atomic>` heading per step with that
      atomic's body under it.
- [x] No workflow's `on failure` column is `→ 1` on every row: each workflow
      has two or more distinct back-edge targets below step 1, and step 1 is
      `stop`.
- [x] Every atomic carries a non-empty `## Do` and `## Done when`, and a
      `## Fails when` table with the header row always present and no data row
      while *that file's own* `runs` is `0` — a file already in a run may carry
      rows or none, since a clean run adds nothing.
- [x] Every workflow's `## Use when` names at least one near-miss it does not
      fit and the slug that does.
- [x] No agent, tool, hook or vendor name appears anywhere in the directory.
- [x] `bash resources/doctor.sh` prints a `workflows` row with status `ok`.

## Verify and Proof

```sh
python3 resources/workflows.py check prds && echo "check silent"
python3 resources/workflows.py list prds
for w in $(python3 resources/workflows.py list prds | awk '$2=="workflow"{print $1}'); do
  python3 resources/workflows.py brief "$w" prds > /dev/null && echo "brief $w ok"
done
awk 'FNR==1{f=0} /^---$/{f++; next} f==1 && /^(runs|updated|date):/{print FILENAME": "$0}' prds/workflows/*.md
bash resources/doctor.sh | grep '^  workflows'
```
