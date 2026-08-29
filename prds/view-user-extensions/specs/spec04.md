---
complexity: 6
footprint:
  - references/parts/view.md
  - index.md
---

# spec04 — the extension point is documented where the view is

`@references/parts/view.md` is the `@@view` scope's prose. Add the extension
point there: the two filenames, where they live, when they load, and the
`window.pearde` table. Written to `@references/language.md` — a fact set is a
table, a rule set is bullets, no paragraph that is not an argument.

## Acceptance

- [x] `references/parts/view.md` names `view.user.css` and `view.user.js`,
      and says they live on the board
- [x] It carries the `window.pearde` member table
- [x] It states the load order — user files after core
- [x] It states that the files are the board's and survive a skill upgrade
- [x] No sentence joins two thoughts with a semicolon or a comma
- [x] No line over 82 characters outside a table or a code fence
- [x] `resources/index.py check` exits 0
- [x] `resources/doctor.sh` exits 0

## Verify and Proof

```sh
grep -n 'view.user' references/parts/view.md
awk 'length>82 && $0 !~ /^\|/ && $0 !~ /^ / {print FILENAME":"FNR": "length}' references/parts/view.md
python3 resources/index.py check && bash resources/doctor.sh >/dev/null && echo "green"
```
