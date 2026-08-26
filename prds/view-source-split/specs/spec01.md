---
complexity: 8
footprint:
  - resources/board/render.py
  - resources/board/view.css
  - resources/board/view.js
---

# spec01 — the cut, with byte equality as the proof

Move the `<style>` body to `resources/board/view.css` and the `<script>` body to
`resources/board/view.js`. `TEMPLATE` keeps `<style>__CSS__</style>` and
`<script>__JS__</script>`. `render()` reads both siblings, substitutes them,
then substitutes `__PAYLOAD__` and `__TITLE__`.

Capture the current render first. It is the acceptance test.

## Acceptance

- [x] `prds/.view.html` is captured before any edit, as the baseline
- [x] `resources/board/view.css` exists and holds the whole former `<style>` body
- [x] `resources/board/view.js` exists and holds the whole former `<script>` body
- [x] `render.py` contains no `<style>` or `<script>` body — `TEMPLATE` is
      markup with `__CSS__` and `__JS__` placeholders only
- [x] `render.py` is under 20,000 bytes
- [x] A fresh render of the same board is byte-identical to the baseline
- [x] `let DATA = __PAYLOAD__` resolves — the rendered page contains no literal
      `__PAYLOAD__`, `__CSS__`, `__JS__` or `__TITLE__`
- [x] `python3 -c "import ast; ast.parse(open('resources/board/render.py').read())"` exits 0

## Verify and Proof

```sh
python3 resources/board/plan.py gantt /Users/feb/dev/infra/prds
cmp "$BASELINE" /Users/feb/dev/infra/prds/.view.html && echo "byte-identical"
grep -c '__CSS__\|__JS__\|__PAYLOAD__\|__TITLE__' /Users/feb/dev/infra/prds/.view.html
wc -c resources/board/render.py resources/board/view.css resources/board/view.js
```
