---
complexity: 20
footprint:
  - src/app.py
---

# spec01 — the line is fixed and covered

The one unit of `building`: change the line, cover it, and leave the tree
green.

## Acceptance

- [x] the failing line is found and named in the report
- [x] the line is changed
- [x] a test covers the change
- [ ] the test suite passes
- [ ] the change is reviewed against the footprint

## Verify and Proof

```sh
python3 -m pytest src/test_app.py -q
```
