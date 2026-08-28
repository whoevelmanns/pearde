---
complexity: 6
footprint:
  - references/parts/doctor.md
  - references/settings.md
---

# spec02 — the page says what the row means, and the key is where keys live

`references/parts/doctor.md` gains the `harnesses` row in the parts table, the
`--harnesses` line in the usage block, and three bullets in the register of
the `memos` / `workflows` / `questions` bullets already there: what the row
runs and why it is opt-in; that the expected count is the harness's own and
there is no ledger, with `unpinned` defined and the honest limit of what
doctor can read stated; and the recursion guard.

`references/settings.md` gains one row in the key table for `harnesses:`,
where `memos:`, `workflows:` and `gate:` already are. Without it the key is
documented only on the doctor page, and the one place a reader looks up board
settings does not mention it. Unknown keys are preserved and read by nothing,
so nothing breaks meanwhile — this is the only reason it can be a separate
unit at all.

**The doctor page stands in the tree.** The `references/settings.md` row is
**not written**: that file was open in another session for the whole of this
run, and a hunk landed into a live edit is a merge nobody asked for. It is
one table row.

## Acceptance

- [x] `references/parts/doctor.md` has a `harnesses` row in the parts table
      whose `off` column names both `harnesses:` and `--harnesses`, and whose
      `broken` column says a harness exiting non-zero is named with its first
      `FAIL` line
- [x] its usage block carries the `--harnesses` invocation
- [x] a bullet says why the row is opt-in, in one line a needle can match
- [x] a bullet says the count is the harness's own, defines `unpinned`, and
      states plainly that nothing forces a harness to pin one
- [x] a bullet says a harness that runs doctor gets the guard, and why
- [x] `references/settings.md` has one `harnesses:` row in the key table,
      default `off`, saying it is read by `doctor` alone and pointing at
      `@references/parts/doctor.md`
- [x] no other row of that key table moved — the diff on
      `references/settings.md` is one added line

## Verify and Proof

```sh
grep -n '`harnesses`' references/parts/doctor.md
grep -n -- '--harnesses' references/parts/doctor.md
grep -n 'a gate nobody can afford to run' references/parts/doctor.md
grep -n 'no ledger' references/parts/doctor.md
grep -n 'not run inside a harness' references/parts/doctor.md
grep -n '^| `harnesses`' references/settings.md
git diff --numstat references/settings.md
```
