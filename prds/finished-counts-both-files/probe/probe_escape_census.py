#!/usr/bin/env python3
"""PROBE — uncommitted. A census, not a spot check: every `prd.md` on every
board `plan.py` reads, every line, classified by which matcher sees it.

Answers one question with a population rather than an example — does widening
`body_has_open_box` change any verdict on the boards as they stand today?"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "resources", "board"))
import plan as P

BOARDS = ["/Users/feb/dev/infra/prds", "/Users/feb/dev/infra/pearde/prds"]


def old(line):
    return line.lstrip().startswith("- [ ]")


files, new_only, both = [], [], []
seen = set()
for b in BOARDS:
    for rel, p in P.scan(b).items():
        f = os.path.join(p["dir"], "prd.md")
        if f in seen or not os.path.isfile(f):
            continue
        seen.add(f)
        files.append((b, rel, f))

for b, rel, f in files:
    for i, line in enumerate(open(f, encoding="utf-8"), 1):
        n, o = P.opens_an_unticked_box(line), old(line)
        if n and not o:
            new_only.append((rel, i, line.rstrip()))
        elif n and o:
            both.append((rel, i))

print(f"population: {len(files)} prd.md files over {len(BOARDS)} boards "
      f"({', '.join(BOARDS)})")
print(f"lines the widened matcher newly calls an open box: {len(new_only)}")
for rel, i, l in new_only:
    print(f"  {rel}:{i}  {l[:120]}")
if not new_only:
    print("  none — every escape spelling is absent from every board file today,")
    print("  so the widening moves no verdict on the boards as they stand.")
print(f"lines both matchers call an open box: {len(both)}")

# and the reverse direction: nothing the old matcher caught may be lost
lost = []
for b, rel, f in files:
    for i, line in enumerate(open(f, encoding="utf-8"), 1):
        if old(line) and not P.opens_an_unticked_box(line):
            lost.append((rel, i, line.rstrip()))
print(f"lines HEAD called open and the widened matcher no longer does: {len(lost)}")
for rel, i, l in lost:
    print(f"  REGRESSION {rel}:{i}  {l[:120]}")
