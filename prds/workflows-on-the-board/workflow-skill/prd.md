---
state: done
origin: requested
priority: 50
complexity: 14
blast-radius: mid
repo: pearde
needs:
  - workflow-reader
footprint:
  - skills/pearde-workflow.md
  - SKILL.md
  - references/parts/handles.md
  - index.md
  - references/files.md
  - README.md
  - references/system.md
  - prds/workflows-on-the-board/workflow-skill/probe
  - prds/the-board-runs-itself/readme-in-three-rings/probe/verify.sh
  - prds/the-board-runs-itself/readme-in-three-rings/probe/quickstart.sh
actual: 1.2h
---

# workflow-skill — the door, and every place a skill is registered

When this is done, `pearde-workflow` is invocable wherever the other skills
are, and `workflow …` is a handle inside a round.

## Handles

| want                       | say                                                                                                      |
|----------------------------|-----------------------------------------------------------------------------------------------------------|
| the library                | `workflow` — `workflows.py list`                                                                          |
| one, as a worker sees it   | `workflow <slug>` — `workflows.py brief`; `show` when the slug is an atomic                               |
| a new atomic               | `workflow add atomic <subject>` — from `references/templates/atomic.md`, slugged as a memo is, `runs: 0`  |
| a new workflow             | `workflow add <subject>` — from `references/templates/workflow.md`; every step's atomic must exist first |
| attach                     | `workflow attach <prd> <slug>` — writes `workflow:` on that `prd.md`. An orchestrator write               |
| check                      | `workflow check` — `workflows.py check`, the `doctor` row alone                                           |

## Files

| file                             | change                                                                                                         |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `skills/pearde-workflow.md`      | new. `name: pearde-workflow`; a `description:` carrying the triggers — "workflow", "how do we do X", "attach a workflow", "improve the workflow", "check the workflows"; a body that names @references/workflow.md and @references/parts/workflows.md, scope `@@workflows`, and stops |
| `SKILL.md`                       | the name in the description's list of skills                                                                    |
| `references/parts/handles.md`    | the six rows; the name in the *also skills of their own* line                                                   |
| `index.md`                       | `@@skills` gains the file; `@@workflows` gains it as its first anchor                                            |
| `references/files.md`            | the row in the skills table                                                                                     |
| `README.md`                      | the *doing the work* row gains `@@workflows`; the lookup table gains *what a worker follows, and how a run improves it* → @references/parts/workflows.md |
| `references/system.md`           | one bullet, **Following**, and `workflow` in the handles line                                                   |

## Rules

- Kebab name, no colon — @references/install.md.
- With no board in scope: `workflow` says where the library would be; `add`
  and `attach` write nothing uninvited — the rule @skills/pearde-memo.md
  already follows.
- The skill body carries no rule the references do not. The knowledge is
  never in the skill.

## Verify

- `bash resources/install.sh <scratch-dir>` lists `pearde-workflow`;
  `--apply` builds its folder; `bash resources/doctor.sh` reports `skills
  ok`.
- `python3 resources/index.py check` silent.
