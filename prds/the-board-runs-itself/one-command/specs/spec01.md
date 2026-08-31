---
complexity: 6
workflow: implement-a-spec
footprint:
  - resources/memos.py
---

# spec01 — `memos.py` gains `add`: slug the subject, write from the template, print the path

`python3 resources/memos.py add <subject> [board]` writes
`prds/memos/<slug>.md` from `@references/templates/memo.md` and prints the
path. The dispatcher (spec02) forwards `pearde memo add` here untouched — a
dispatcher holds no logic, so the logic lands in the one reader of the memo
format.

Not in the PRD's `footprint:` — the contract table says `add` is new under
`memos.py`, and the footprint omits the file. This spec's footprint is the
correction.

## What already stands

`@prds/the-board-runs-itself/one-command/probe/pearde.py` carries the working
implementation under the heading `memo add — PROBE ONLY`: `slug_of(subject)`
and `memo_add(args)`. Seven lines of
`@prds/the-board-runs-itself/one-command/probe/verify.sh` prove it (the
`# ── memo` block): prints the path, `memo:` equals the slug, `subject:` kept
as written, `date:` is today, the new memo passes `check`, a second `add`
refuses, an external `memos:` dir refuses.

## What is left

1. Move `slug_of` and `memo_add` into `resources/memos.py` as `slug(subject)`
   and `add(board, subject)`; `main` takes the verb `add` with the subject as
   `argv[2]` and the optional board as `argv[3]` — the same positions every
   other verb uses. Board resolution stays `find_board`.
2. The template substitution stays line-based, as in the probe: `memo:
   <slug>`, `subject: …`, `date: …` and the `# <slug> — …` title line are
   replaced; every other template line, comments included, is kept.
3. Add the usage line to the module docstring, two spaces before the
   description, so `pearde help` reads it:
   `python3 memos.py add   <subject> [board]  slug it, write the memo from the template, print the path`
4. The slug rule of `@references/parts/handles.md` — lowercase, spaces to
   hyphens — is applied as `re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")`;
   a subject that slugs to nothing exits 2.
5. A path that exists exits 1 and names it. A board whose `settings.md` points
   `memos:` elsewhere exits 1 and writes nothing — `memos_dir` says that dir
   is another system's, mirrored read-only.

## Acceptance

- [x] On a temp board, `python3 resources/memos.py add "Dates are written" <board>` prints `<board>/memos/dates-are-written.md`, exits 0, and the file holds `memo: dates-are-written`, `subject: Dates are written` and `date: <today>`
- [x] `python3 resources/memos.py check <board>` is silent after that `add`
- [x] the same `add` a second time exits 1, prints the path with `exists`, and the file is byte-identical to before
- [x] on a temp board whose `settings.md` has `memos: ../records`, `add` exits 1 and `records/` stays empty
- [x] `python3 resources/memos.py` with no verb still runs `check` (the default did not move)
- [x] the docstring of `resources/memos.py` has one usage line starting `python3 memos.py add`

## Verify and Proof

```sh
D=$(mktemp -d); D=$(cd "$D" && pwd -P); trap 'rm -rf "$D"' EXIT
mkdir -p "$D/a/prds/memos" "$D/b/prds" "$D/b/records"
printf -- '---\nlanguage: English\n---\n' > "$D/a/prds/settings.md"
printf -- '---\nlanguage: English\nmemos: ../records\n---\n' > "$D/b/prds/settings.md"
OUT=$(python3 resources/memos.py add "Dates are written" "$D/a"); echo "rc=$? $OUT"
grep -E '^(memo|subject|date): ' "$OUT"
python3 resources/memos.py check "$D/a"; echo "check rc=$?"
cp "$OUT" "$D/before.md"; python3 resources/memos.py add "Dates are written" "$D/a"; echo "again rc=$?"; cmp "$OUT" "$D/before.md" && echo unchanged
python3 resources/memos.py add "x" "$D/b"; echo "external rc=$? records=$(ls "$D/b/records" | wc -l | tr -d ' ')"
grep -c '^    python3 memos.py add' resources/memos.py
```
