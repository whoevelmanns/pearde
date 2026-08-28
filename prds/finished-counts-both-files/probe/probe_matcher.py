#!/usr/bin/env python3
"""PROBE — uncommitted. Drives plan.py's box matcher over the SAME eighteen
rows the four Rust gates assert in
`the_matcher_reads_every_spelling_of_one_rendered_box`, so "the same matcher"
is measured rather than asserted. Also runs the same rows against the matcher
this replaced, so the delta is a list of lines rather than a claim."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "resources", "board"))
import plan as P

# Copied verbatim from shared/shared/tests/done_boxes_are_ticked.rs:301-320,
# which realm/mitosys/model hold byte-identical.
CASES = [
    ("* [ ] a star bullet", True),
    ("+ [ ] a plus bullet", True),
    ("- [] no space inside the brackets", True),
    ("-  [ ] two spaces after the bullet", True),
    ("1. [ ] an ordered task list", True),
    ("1) [ ] an ordered task list, paren marker", True),
    ("- [ ] the literal spelling", True),
    ("  - [ ] indented, under no heading", True),
    ("\t- [ ] tab-indented", True),
    ("- [x] ticked, on evidence", False),
    ("- [X] ticked, capital", False),
    ("- [~] ~~struck~~ — with the reason beside it", False),
    ("* [x] ticked under a star bullet", False),
    ("prose quoting an inline `- [ ]` mid-sentence", False),
    ("- [a link](https://example.invalid) is not a box", False),
    ("- not a box at all", False),
    ("1234567890. [ ] ten digits, past GFM's bound", False),
    ("state: done", False),
]


def old_matcher(line):
    """`body_has_open_box`'s matcher at HEAD (6cd1edf), verbatim."""
    return line.lstrip().startswith("- [ ]")


wrong = [(l, e, P.opens_an_unticked_box(l))
         for l, e in CASES if P.opens_an_unticked_box(l) != e]
print(f"new matcher vs the gates' table: {len(CASES) - len(wrong)}/{len(CASES)} agree")
for l, e, g in wrong:
    print(f"  DISAGREES {l!r}: gates say {e}, plan.py says {g}")

oldwrong = [(l, e, old_matcher(l)) for l, e in CASES if old_matcher(l) != e]
print(f"\nHEAD's matcher vs the same table: "
      f"{len(CASES) - len(oldwrong)}/{len(CASES)} agree")
for l, e, g in oldwrong:
    print(f"  MISSES  {l!r}: gates say {e}, HEAD says {g}")

print("\n`- [~]` under both matchers — struck-box-spelling.md's claim:")
for l in ("- [~] struck", "  - [~] indented struck", "* [~] star struck"):
    print(f"  {l!r:28} new={P.opens_an_unticked_box(l)} head={old_matcher(l)}"
          f"  (False = still a closure)")
