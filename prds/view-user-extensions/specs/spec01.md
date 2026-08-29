---
complexity: 6
footprint:
  - resources/board/render.py
---

# spec01 — a board's own CSS and JS reach its page

`render()` takes the board directory. When `<board>/view.user.css` or
`<board>/view.user.js` exists, inline it after the core equivalent — a user
rule wins on cascade order, and a user script runs against a built page.

A board with neither file renders exactly what it renders now.

## Acceptance

- [x] `render()` inlines `<board>/view.user.css` into a `<style>` after the
      core stylesheet
- [x] `render()` inlines `<board>/view.user.js` into a `<script>` after the
      core script
- [x] A board with neither file renders byte-identical output to before this
      spec
- [x] A board with a `view.user.css` saying `body{--test:1}` has that text in
      its rendered page, after the core CSS
- [x] An unreadable or absent user file is not an error — the page renders
- [x] A user file containing `</script>` does not break the page out of its
      tag

## Verify and Proof

```sh
B=/Users/feb/dev/infra/prds
python3 resources/board/plan.py gantt $B && cp $B/.view.html /tmp/pearde-clean.html
printf 'body{--test:1}\n' > $B/view.user.css
printf 'window.__userLoaded = true;\n' > $B/view.user.js
python3 resources/board/plan.py gantt $B
grep -c -- '--test:1' $B/.view.html
grep -c '__userLoaded' $B/.view.html
rm -f $B/view.user.css $B/view.user.js
python3 resources/board/plan.py gantt $B && cmp /tmp/pearde-clean.html $B/.view.html && echo "clean board unchanged"
```
