#!/usr/bin/env python3
"""PROBE — uncommitted. Enumerates the population `collect` can draw from on
every board this install plans, so "collect is empty" can be told apart from
"collect is empty because of the matcher". A census, not a spot check."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "resources", "board"))
import plan as P

BOARDS = ["/Users/feb/dev/infra/prds", "/Users/feb/dev/infra/pearde/prds"]

for b in BOARDS:
    prds = P.scan(b)
    print(f"=== {b} — {len(prds)} PRDs ===")
    states = {}
    for rel, p in prds.items():
        states[p["state"]] = states.get(p["state"], 0) + 1
    print("  states:", dict(sorted(states.items())))
    cand = []
    for rel, p in sorted(prds.items()):
        frac, closed, total, ready = P.standing(p)
        if p["state"] in P.HOLDING_STATES:
            cand.append((rel, p["state"], closed, total,
                         P.body_has_open_box(p), ready))
    print(f"  held: {len(cand)}")
    for rel, st, c, t, box, ready in cand:
        print(f"    {rel:58} [{st}] {c}/{t} body_open={box} collect={ready}")
    # every PRD whose specs are fully closed, whatever its state — the set that
    # would reach collect if it were held
    full = [(rel, p["state"]) for rel, p in sorted(prds.items())
            if P.acceptance(p)[1] and P.acceptance(p)[0] == P.acceptance(p)[1]]
    print(f"  specs fully closed, any state: {len(full)}")
    for rel, st in full:
        print(f"    {rel:58} [{st}]")
    print()
