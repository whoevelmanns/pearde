---
complexity: 8
workflow: implement-a-spec
footprint:
  - /Users/feb/dev/infra/prds/vision.py
  - /Users/feb/dev/infra/prds/allboards.py
  - /Users/feb/dev/infra/prds/.vision.json
  - /Users/feb/dev/infra/prds/settings.md
---

# spec03 — the master board's scripts retire, with nothing lost

`prds/vision.py` and `prds/allboards.py` on the master board at
`/Users/feb/dev/infra/prds` re-implement what `plan.py` now does, and
`.vision.json` is a file nothing reads. They go once `pearde vision --json`
on that board reproduces the last `.vision.json`, depth for depth — that
measurement is the gate, and this spec quotes it before the deletion.

The footprint is absolute on purpose: it is another repo's board, and
@references/parts/master.md says an absolute path is how a deliberate
cross-repo footprint is written. That board is worked by its own
orchestrator — take this spec only when dispatched with that board in
scope, and write nothing else there.

## What stands from the probe

- Measured on 2026-08-28, read-only, against a fresh run of the old
  `vision.py --json` in a temp mirror of the board: `plan.py vision --json
  /Users/feb/dev/infra/prds` agrees on all 13 PRDs both name — `depth
  differs on 0` — and on all 11 shared with the stale `.vision.json` of
  2026-08-27. `.vision.json` there was not written (mtime unchanged).
- The one divergence, explained: `@mitosys/record-shape-port` is on-axis
  at depth 0 under `plan.py` and off-axis under `vision.py`. Its edge
  `@mitosys/record-shape-port -> @master/corpus-flow` resolves only under
  the own-name rule (`settings.md` says `name: master`); the old script
  addressed the master's own PRDs as `@infra/…` from the directory name,
  so its own terminal never resolved. `corpus-flow` is `done`, and a done
  terminal costs no hop, hence depth 0. `@model`, `@realm`, `@shared` —
  the members' root `prd.md` files — appear only in the old `off_axis`:
  `plan.py` does not treat a board root as a PRD.
- `vision --check` on that board today prints `7 terminals · 14 on · 41
  off · longest chain 3` and exits 0 — every terminal and edge end
  resolves.

## What is left

- Re-run the measurement below on the day of the deletion and quote it.
- Delete the three files. `settings.md` on that board has a sentence under
  `## The destination` saying `vision.py` reads the file — rewrite it to
  name `pearde vision`.
- Nothing in this repo changes: `plan.py` never imported either script.

## Acceptance

- [x] `python3 resources/board/plan.py vision --check /Users/feb/dev/infra/prds` exits 0 and prints `7 terminals` — every terminal and edge in the master's `vision.md` resolves before anything is deleted
- [x] `python3 resources/board/plan.py vision --json /Users/feb/dev/infra/prds` and the old `.vision.json` agree on `depth` for every address both name (the sets compared by `(board, rel)` with `infra` read as `master`); the differences are listed and each is one of the explained kinds above — a PRD done or added since the file was written, a root `prd.md`, or the own-name rule
- [x] `/Users/feb/dev/infra/prds/vision.py`, `allboards.py` and `.vision.json` are no longer on disk, and `grep -c 'vision.py\|allboards.py' /Users/feb/dev/infra/prds/settings.md` prints `0`
- [x] `python3 resources/board/plan.py scan /Users/feb/dev/infra/prds` still prints a first line carrying `axis:` after the deletion

## Verify and Proof

```sh
python3 resources/board/plan.py vision --check /Users/feb/dev/infra/prds; echo "exit $?"
python3 resources/board/plan.py vision --json /Users/feb/dev/infra/prds > /tmp/new-vision.json
python3 - <<'EOF'
import json
new = json.load(open("/tmp/new-vision.json"))
old = json.load(open("/Users/feb/dev/infra/prds/.vision.json"))
def key(a):
    b, _, r = a[1:].partition("/")
    return ("master" if b in ("infra", "master") else b, r)
dn = {key(p["addr"]): p["depth"] for p in new["prds"]}
do = {key(p["addr"]): p["depth"] for p in old["prds"]}
both = sorted(set(dn) & set(do))
print(len(both), "both name; depth differs on",
      [(k, do[k], dn[k]) for k in both if do[k] != dn[k]])
print("only old:", sorted(set(do) - set(dn)))
print("only new:", sorted(set(dn) - set(do)))
EOF
ls /Users/feb/dev/infra/prds/vision.py /Users/feb/dev/infra/prds/allboards.py /Users/feb/dev/infra/prds/.vision.json 2>&1
grep -c 'vision.py\|allboards.py' /Users/feb/dev/infra/prds/settings.md
python3 resources/board/plan.py scan /Users/feb/dev/infra/prds | head -1
```

**Closed by the orchestrator, 2026-08-28, on the master board's own commit** —
`/Users/feb/dev/infra` `9776cb9` (its session, infra-5d, option 2): `prds/vision.py`
(−294), `prds/allboards.py` (−542), `prds/.vision.json` (−357) deleted, the
sentence in `prds/settings.md` § The destination and one line in `prds/plan.md`
rewritten, `vision.md` untouched. Measured by that session before deleting:
`pearde vision --json` 15 on-axis vs the script's 12, zero depth differences —
the three extra are two children a refine created that night and
`@mitosys/record-shape-port` under the own-name rule. `ls prds/vision.py
prds/.vision.json` there: `No such file or directory`.
