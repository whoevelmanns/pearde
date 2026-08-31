---
complexity: 4
workflow: implement-a-spec
footprint:
  - resources/install.sh
  - references/install.md
  - resources/board/init.py
  - prds/the-board-runs-itself/the-next-line-runs/probe/verify.sh
---

# spec02 — `install --apply` prints the export beside the alias, and `init`'s three lines run as printed

The newcomer's first minute is two pasted lines and three printed ones. `install
--apply` closes with two lines for the shell — the alias, then
`export PEARDE_AS=engineer` under one heading that says what each is; report
mode prints neither. `references/install.md` says the same under **Two lines**,
and its first-run paragraph says the three lines `init` prints run as printed.
`init` itself needs no edit: measured in a fresh shell holding only the two
pasted lines, its URL answers 200, `pearde add "<title>"` files `prds/title/`
and prints the progress line `· as engineer`, and `pearde` scans — and with the
export skipped, `add` still runs (`(default)`) while `set` refuses naming the
line.

**Already standing from the probe** (in place): the three `echo` lines in
`resources/install.sh`'s `apply)` case, the **Two lines** bullet and the
first-run sentence in `references/install.md`. `resources/board/init.py` is
unchanged and stays so — the PRD's row for it reads "measured, not restated".

**Left for the implementer:** run the harness; tick the boxes. The README's
quickstart still spells its third line `pearde add --as engineer …` — that file
and `readme-in-three-rings/probe/quickstart.sh` belong to `readme-in-three-rings`,
whose analyst is live; they are a finding in the report, not this spec's edit.

## Acceptance

- [x] `bash resources/install.sh --apply <fresh dir>` exits 0 and its output holds the line `  alias pearde='python3 <repo>/resources/pearde.py'` immediately followed by the bare line `  export PEARDE_AS=engineer`, under a heading containing `who is working`; a second `--apply` prints both again; `bash resources/install.sh <dir>` (report mode) prints no `PEARDE_AS`
- [x] in `env -i` `bash --noprofile --norc` with `shopt -s expand_aliases` and the two printed lines pasted verbatim, in a fresh git repo, `pearde init --example` exits 0 and its last three lines are the URL, `pearde add "<title>"`, `pearde`
- [x] in that shell the URL answers HTTP 200; `pearde add "<title>"` run literally exits 0, files `prds/title/prd.md`, and prints `▸ title: — → open … · as engineer`; `pearde` exits 0 and lists `title`; `pearde add "Ship the quickstart"` (the quickstart's third line, no `--as`) exits 0
- [x] in a second fresh shell holding the alias only, `pearde add "Without the export"` exits 0 ending ` · as engineer (default)`, and `pearde set without-the-export analyzing` exits 1 naming `PEARDE_AS` and `export PEARDE_AS=engineer`, the PRD still `state: open`
- [x] `references/install.md` contains `**Two lines.**`, `export PEARDE_AS=engineer` and `each runs as printed`
- [x] `git diff --stat -- resources/board/init.py` is empty
- [x] the live daemon's `resources/board/state/serve.json` is byte-identical before and after — the harness copies the repo and runs the copy's `serve.py` on a spare port

## Verify and Proof

```sh
bash prds/the-board-runs-itself/the-next-line-runs/probe/verify.sh
# sections E, F, G, and H's install.md lines are this spec's
bash resources/install.sh --apply "$(mktemp -d)" | tail -3
git diff --stat -- resources/board/init.py
grep -n 'Two lines\|export PEARDE_AS=engineer\|each runs as printed' references/install.md
```
