---
complexity: 5
footprint:
  - resources/board/serve.py
---

# spec03 — the watcher reaches a board's user files

`digest()` walks the board for `.md` files only, so a change to
`view.user.css` moves nothing and the page never updates. The two user files
are board content, not skill source — they belong in `digest()`, not in
`SOURCES`.

Editing either must bump the board's sequence within about a second, which is
what makes the live page reload.

## Acceptance

- [x] `digest()` stats `view.user.css` and `view.user.js` at the board root
- [x] Writing `view.user.css` changes `digest()`'s return value
- [x] Deleting it changes it back
- [x] A member board's user files are digested too, on a master board
- [x] The daemon does not re-exec on a user file change — it is board content,
      so the page reloads through the normal sequence bump

## Verify and Proof

```sh
B=/Users/feb/dev/infra/prds
python3 - <<'PY'
import sys; sys.path.insert(0,'resources/view'); import serve
B="/Users/feb/dev/infra/prds"
a=serve.digest(B)
open(B+"/view.user.css","w").write("body{--t:1}")
b=serve.digest(B)
import os; os.remove(B+"/view.user.css")
c=serve.digest(B)
print("changed on write:", a!=b, "· restored on delete:", a==c)
PY
```
