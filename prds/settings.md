---
name: pearde
language: English
workers: 1
pipeline: 1
weight-default: 20
gantt-day: 8h
---

# The pearde board

The skill's own board. One tree, one repo, no members.

## Admission

A PRD lives here if it changes this repo. Work that spans the family's trees
belongs on `@../prds` — that board's rule admits only what more than one tree
carries, and this skill is not one of its members.

## Deliverable

Code in this repo, plus the `@index.md` rows and `@references/` prose that
describe it. `resources/index.py check`, `resources/memos.py check` and
`resources/doctor.sh` are the gate — a PRD is `done` when all three are green
and its own acceptance boxes are closed.

## Footprints

Written relative to this repo root: `resources/view`, `references/parts`,
`index.md`. The view's four modules move together often enough that a PRD
touching any of them claims `resources/view` whole.
