---
atomic: change-the-line
subject: change the named line and cover it with a test that fails without it
date: 2026-08-28
runs: 0
---

# change-the-line — the fix, and the test that proves it

## Do

1. Write the test first and run it. It fails on the line as it stands.
2. Change the line. Run the test again. It passes.
3. Run the file's whole test module and quote the count.

## Done when

- The new test fails before the change and passes after it.
- The module's test count is quoted in the report.

## Fails when

| seen | means | do |
|------|-------|----|
