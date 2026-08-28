---
complexity: 8
workflow: implement-a-spec
footprint:
  - resources/board/plan.py
  - references/settings.md
---

# spec01 — `silent` is one rule in `plan.py`, and `scan` prints its word

A held PRD whose files have not moved for longer than `claim-ttl` is silent.
The rule lives in `plan.py` as `silent_of(prd, settings, collect=None)` —
minutes of silence past the limit, else `None` — and three readers take it
from there: the scan line, the page's payload (`tasks[].silent`) and the
sibling `sweep`. `claim-ttl` is a `settings.md` key, default `30m`. The
payload also carries `vision.purpose`, the one sentence of `prds/vision.md`.

## What already stands

The probe left all of it in `resources/board/plan.py` (the `# ── silence`
block after `hours()`: `CLAIM_TTL`, `SILENT_STATES`, `claim_ttl`,
`prd_repo`, `newest_mtime`, `silent_of`, `fmt_age`; the `silent=` field and
the `"vision"` key in `gantt_payload`; `settings` and the `silent` bit in
`cmd_scan`'s `line`) and the `claim-ttl` row in `references/settings.md`. The
implementer's job is to run the checks below on a copy and tick what holds;
nothing is left to write unless a check fails.

## Rules the code keeps

- Silence is read off files, never off a process: the newest mtime over the
  PRD directory and every path of its footprint union — its own `footprint:`
  plus its specs', the union `collect` commits — in `prd_repo(prd)`, which is
  `collect.repo_of`'s rule. Dot-dirs and `__pycache__` are skipped.
- Only `claimed` and `analyzing` can be silent — the in-flight band. A
  `blocked` PRD is waiting on a person, and a PRD to collect is a worker that
  finished, so `silent_of` returns `None` for both.
- `scan` on a board with no claim past `claim-ttl` prints byte for byte what
  it printed before: the word is appended to the line only when the rule
  fires, and nothing else in the output moved.
- `claim_ttl`: `30m` `2h` `1d` as `hours()` reads them, a bare number is
  minutes, missing or unreadable is 30.

## Acceptance

Fixture: `python3 resources/board/plan.py example $D/b`, `git init` in
`$D/b`, `claim-ttl: 1m` appended to `$D/b/prds/settings.md`, every file's
mtime set two minutes back with `touch -t`. `$D` from `mktemp -d`, never
under `prds/`.

- [x] `python3 resources/board/plan.py scan $D/b/prds` prints the `building` line ending in ` · silent <N>m` and the `finished` line without the word — exactly one `silent` on the board
- [x] `mkdir -p $D/b/src && touch $D/b/src/app.py` (the footprint path in the repo) — the next `scan` prints no `silent`; setting the mtime back restores it
- [x] `touch $D/b/prds/building/specs/spec01.md` (a file under the PRD dir) — the next `scan` prints no `silent`
- [x] on a second copy with every mtime fresh and no `claim-ttl` key, `scan` prints no `silent` and no `claim-ttl` — the output is what it was before this PRD
- [x] `silent_of` on the fixture returns a float for `building`, `None` for `finished` (collect), `asking` (question) and `next` (open)
- [x] `claim_ttl({"claim-ttl": v})` is 1.0 for `1m`, 120.0 for `2h`, 480.0 for `1d`, 30.0 for `30`, 30.0 for `{}` and for `junk`
- [x] `fmt_age(42.4)` is `42m`, `fmt_age(100)` is `1.7h` — the page's own spelling
- [x] `gantt_payload` on the fixture: `tasks[building].silent` is a float, `tasks[finished].silent` is `None`, `vision.purpose` is `""`; with a `vision.md` carrying `vision: Ship the line.` it is that sentence
- [x] `references/settings.md` carries the `claim-ttl` row, default `30m`, naming `silent_of` as the one reader

## Verify and Proof

```sh
D=$(mktemp -d); python3 resources/board/plan.py example $D/b >/dev/null; ( cd $D/b && git init -q . )
printf 'claim-ttl: 1m\n' >> $D/b/prds/settings.md; python3 resources/board/plan.py plan $D/b/prds >/dev/null
find $D/b -path $D/b/.git -prune -o -type f -exec touch -t "$(date -v-2M +%Y%m%d%H%M)" {} +   # resources/board/plan.py reads these mtimes
python3 resources/board/plan.py scan $D/b/prds | grep -c 'silent'          # 1
python3 resources/board/plan.py scan $D/b/prds | grep 'building .* · silent [0-9]*m$'
python3 resources/board/plan.py example $D/c >/dev/null; find $D/c -type f -exec touch {} +
python3 resources/board/plan.py scan $D/c/prds | grep -c 'silent'          # 0
grep -n 'claim-ttl' references/settings.md; rm -rf $D
```
