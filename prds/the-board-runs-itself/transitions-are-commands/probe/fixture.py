#!/usr/bin/env python3
"""Build the probe's board in <dir>/prds — the shape of `an-example-board`'s
contract, plus two PRDs the transitions need (`probing`, `stuck`, `broke`).
Never run against a real board: `python3 fixture.py "$(mktemp -d)"`."""
import os
import sys


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.lstrip("\n"))


def build(root):
    b = os.path.join(root, "prds")
    w(f"{b}/settings.md", """
---
name: example
language: English
workers: 2
pipeline: 1
weight-default: 20
---

# The example board
""")
    w(f"{b}/landed/prd.md", """
---
state: done
origin: requested
priority: 50
complexity: 10
blast-radius: low
commit: abc1234
actual: 2h
footprint:
  - src/landed
---

# landed — already done
""")
    w(f"{b}/building/prd.md", """
---
state: claimed
origin: requested
priority: 60
complexity: 20
blast-radius: mid
claim: impl-0 2026-08-28 13:00
footprint:
  - src/shared
  - src/building
---

# building — in flight
""")
    w(f"{b}/building/specs/spec01.md", """
---
complexity: 20
footprint:
  - src/building
---

# spec01 — half built

## Acceptance

- [x] one
- [x] two
- [x] three
- [ ] four
- [ ] five
""")
    w(f"{b}/finished/prd.md", """
---
state: claimed
origin: requested
priority: 55
complexity: 8
blast-radius: low
claim: impl-2 2026-08-28 12:00
footprint:
  - src/finished
---

# finished — every box closed, waiting to be collected
""")
    w(f"{b}/finished/specs/spec01.md", """
---
complexity: 8
footprint:
  - src/finished
---

# spec01 — done

## Acceptance

- [x] one
- [x] two
""")
    w(f"{b}/asking/prd.md", """
---
state: question
origin: requested
priority: 40
complexity: 0
blast-radius:
---

# asking — three forks for the user

## Questions

### Q1: Which colour?

The button is red or blue — which?

1. **red** — paint it red (recommended)
2. **blue** — paint it blue
3. **none** — no button

### Q2: Which size?

Small or large?

1. **small** — 12px (recommended)
2. **large** — 24px
3. **auto** — the viewer's choice

### Q3: Which name?

`go` or `run`?

1. **go** — `go` (recommended)
2. **run** — `run`
3. **start** — `start`
""")
    w(f"{b}/next/prd.md", """
---
state: specced
origin: requested
priority: 45
complexity: 12
blast-radius: mid
workflow: two-steps
needs:
  - building
footprint:
  - src/next
---

# next — gated on building
""")
    w(f"{b}/next/specs/spec01.md", """
---
complexity: 12
footprint:
  - src/next
---

# spec01 — the unit

## Acceptance

- [ ] one
""")
    w(f"{b}/big/prd.md", """
---
state: open
origin: requested
priority: 30
complexity: 0
blast-radius:
---

# big — a parent
""")
    w(f"{b}/big/first/prd.md", """
---
state: done
origin: requested
priority: 30
complexity: 5
blast-radius: low
---

# big/first — done
""")
    w(f"{b}/big/second/prd.md", """
---
state: open
origin: requested
priority: 30
complexity: 0
blast-radius:
---

# big/second — open
""")
    # beyond the example's contract: what the transitions need to exercise
    w(f"{b}/probing/prd.md", """
---
state: analyzing
origin: requested
priority: 35
complexity: 0
blast-radius:
claim: analyst-1 2026-08-28 14:00
---

# probing — an analyst holds it
""")
    w(f"{b}/stuck/prd.md", """
---
state: blocked
origin: derived
from: building
priority: 20
complexity: 6
blast-radius: low
needs:
  - landed
footprint:
  - src/stuck
---

# stuck — blocked on landed, which is done
""")
    w(f"{b}/stuck/specs/spec01.md", """
---
complexity: 6
footprint:
  - src/stuck
---

# spec01

## Acceptance

- [x] one
- [ ] two
""")
    w(f"{b}/broke/prd.md", """
---
state: failed
origin: requested
priority: 25
complexity: 7
blast-radius: low
---

# broke — a failed attempt

Some body text.

## Failure

The build hit a wall: the fixture was missing.
""")
    w(f"{b}/clash/prd.md", """
---
state: specced
origin: requested
priority: 44
complexity: 9
blast-radius: low
footprint:
  - src/shared/thing.py
---

# clash — footprint overlaps building
""")
    w(f"{b}/dangling/prd.md", """
---
state: specced
origin: requested
priority: 43
complexity: 9
blast-radius: low
workflow: no-such-route
footprint:
  - src/dangling
---

# dangling — workflow names nothing
""")
    w(f"{b}/badround/prd.md", """
---
state: analyzing
origin: requested
priority: 22
complexity: 0
blast-radius:
claim: analyst-2 2026-08-28 14:10
---

# badround — a round with no recommended answer

## Questions

### Q1: Which way?

Left or right?

1. **left** — go left
2. **right** — go right
3. **stay** — stay
""")
    # the daemon's burn-down, one row a day — a command never touches it
    w(f"{b}/.history.jsonl", '{"d": "2026-08-27", "done": 1, "hdone": 10.0, '
      '"hleft": 60.0, "left": 9, "states": {"open": 2}}\n')
    w(f"{b}/workflows/two-steps.md", """
---
workflow: two-steps
subject: a two step route
date: 2026-08-28
runs: 0
---

# two-steps — the route

## Use when

- always

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
| 1 | `look` | see | `stop` |
| 2 | `leap` | go | `→ 1` |
""")
    for slug in ("look", "leap"):
        w(f"{b}/workflows/{slug}.md", f"""
---
atomic: {slug}
subject: {slug} once
date: 2026-08-28
runs: 0
---

# {slug} — one step

## Do

1. {slug}.

## Done when

- it {slug}ed.

## Fails when

| seen | means | do |
|------|-------|----|
""")
    return b


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("fixture.py <dir>")
    print(build(sys.argv[1]))
