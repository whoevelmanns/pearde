---
workflow: fix-a-line
subject: one wrong line, from the report to the change
date: 2026-08-28
runs: 0
---

# fix-a-line — one wrong line, from the report to the change

## Use when

- A report names one line that is wrong, and the fix is the line.
- Not when the report names a behaviour and no line: that is a probe first.

## Steps

| # | atomic | why | on failure |
|---|--------|-----|------------|
| 1 | `find-the-line` | the report names a symptom, and the line is what gets changed | `stop` |
| 2 | `change-the-line` | the change and its test are one unit | `→ 1` |
