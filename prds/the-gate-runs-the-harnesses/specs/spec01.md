---
complexity: 14
footprint:
  - resources/doctor.sh
  - prds/the-gate-runs-the-harnesses/probe/verify.sh
---

# spec01 — doctor runs the board's harnesses, and goes red when one does

A `harnesses` row in `resources/doctor.sh`: `find <board> -name verify.sh`,
run each with stdin closed, report `<green> of <found> green · <secs>s`.
`broken` on any non-zero exit, naming the harness and its first `FAIL` line,
so `doctor` exits 1. Opt-in — `harnesses: on` in `prds/settings.md`, default
off, plus `--harnesses` which runs them whatever the key says.

The expected count is never recorded here. A harness that pins its own
denominator is trusted on its exit code; one that does not is counted and
named as **unpinned**, and its pass does not make the row green on its own
account. What doctor reads is the idiom — a test comparing the harness's own
executed total against an integer literal — not the semantics.

**All of this stands in the tree**, built in place: an edit inside an existing
file has no meaning staged elsewhere. What is left for the implementer is to
run the checks below and quote them.

## Acceptance

- [x] `bash prds/the-gate-runs-the-harnesses/probe/verify.sh` prints
      `57 checks · 57 pass · 0 fail` and exits 0
- [x] the same harness prints the same 57 with `PEARDE_HARNESSES=1` set — it
      clears the guard for its own fixture runs rather than measuring it
- [x] `bash resources/doctor.sh` prints a `harnesses` row reading `off`, names
      the count of harnesses it did not run, and its fix line names both
      `harnesses: on` and `--harnesses`
- [x] `bash resources/doctor.sh --harnesses` prints `<n> of <m> green`, a
      wall-clock in whole seconds, and one indented line per failing harness
      carrying that harness's first `FAIL` line
- [x] with a harness red, that run exits 1; with none red, its exit code is
      the one the same board gives with the row off
- [x] `resources/doctor.sh` holds no expected total for any harness — no
      count, no ledger file, no path a count could be written to
- [x] the probe prints `note doctor on <board>, harnesses absent: before <a>s
      · after <b>s · delta <c>s`, measured against the committed doctor of the
      moment, and the delta is under one second

## Verify and Proof

```sh
bash prds/the-gate-runs-the-harnesses/probe/verify.sh
PEARDE_HARNESSES=1 bash prds/the-gate-runs-the-harnesses/probe/verify.sh
bash resources/doctor.sh                        # the row reads off, ~0.6s
bash resources/doctor.sh --harnesses            # the row runs them, ~86s
grep -vE '^[[:space:]]*#' resources/doctor.sh | grep -i harness | grep -c expected
                                                # 0 — no recorded total, ever
```
