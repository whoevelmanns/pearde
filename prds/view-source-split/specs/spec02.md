---
complexity: 4
footprint:
  - resources/board/serve.py
  - index.md
---

# spec02 — the two files are watched and indexed

`SOURCES` in `@resources/board/serve.py` is the list the daemon stats to decide
whether its own code moved. The two new files belong in it, or editing the CSS
changes nothing until the daemon is restarted by hand.

`@index.md` holds one row per file and a `@@view` scope. Both new files need a
row, and both belong in that scope.

## Acceptance

- [x] `SOURCES` names `view.css` and `view.js`
- [x] Touching `view.css` makes `source_stamp()` return a different value
- [x] `index.md` has a Files row for each of the two new files
- [x] The `@@view` scope row names both
- [x] `resources/index.py check` exits 0
- [x] `resources/index.py scope view` lists seven files
- [x] `resources/doctor.sh` exits 0 with `index` and `view` both `ok`

## Verify and Proof

```sh
python3 resources/index.py check && echo "index clean"
python3 resources/index.py scope view
bash resources/doctor.sh; echo "doctor rc=$?"
python3 -c "
import sys; sys.path.insert(0,'resources/view'); import serve
print([s.split('/')[-1] for s in serve.SOURCES])"
```
