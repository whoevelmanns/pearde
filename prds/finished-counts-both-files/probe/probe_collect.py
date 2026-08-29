#!/usr/bin/env python3
"""PROBE — uncommitted. Measures `collect` over the master board using
plan.py's own readers, so the numbers are the ones the board prints.

Job 2's break-it proof, re-measured by a worker rather than inherited from the
memo. Nothing here edits a board file."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "resources", "board"))
import plan as P

BOARD = "/Users/feb/dev/infra/prds"
NAMED = ("@realm/02-linux-driver", "@realm/done-means-done/realm-classify")


def main():
    prds = P.scan(BOARD)
    collect = []
    held = []
    for rel, p in sorted(prds.items()):
        frac, closed, total, ready = P.standing(p)
        if ready:
            collect.append((rel, p["state"], closed, total))
        if p["state"] in P.HOLDING_STATES:
            held.append((rel, p["state"], closed, total, P.body_has_open_box(p)))
    print(f"collect: {len(collect)} finished, waiting to be closed")
    for rel, st, c, t in collect:
        print(f"  {rel} [{st}] {c}/{t}")
    print()
    print(f"held ({len(held)}) — every PRD in a HOLDING_STATE, the only "
          f"population collect can draw from:")
    for rel, st, c, t, box in held:
        print(f"  {rel:60} [{st}] specs {c}/{t}  body_open_box={box}")
    print()
    print("the two the memo names:")
    for rel in NAMED:
        p = prds.get(rel)
        if p is None:
            print(f"  {rel}: NOT ON THE BOARD")
            continue
        frac, closed, total, ready = P.standing(p)
        print(f"  {rel}: state={p['state']!r} specs {closed}/{total} "
              f"body_has_open_box={P.body_has_open_box(p)} collect={ready}")


if __name__ == "__main__":
    main()
