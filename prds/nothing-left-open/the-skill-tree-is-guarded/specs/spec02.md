---
complexity: 4
footprint:
  - references/parts/guard.md
  - references/install.md
  - prds/memos/the-install-is-live-symlinks.md
---

# spec02 — the rule is written where a reader looks: the refusals table, the install page, and the memo closed

`references/parts/guard.md` carries the refusal as a row of `## What it
refuses` and, under the paragraph on real-path keying, the caveat that the
`Bash` hook is a reader's check and a shell write through a link goes through
it unrefused. `references/install.md` says, beside the five links, that the
links run the other way too and the guard refuses a write through them from
another board, naming the memo. The memo
`prds/memos/the-install-is-live-symlinks.md` records the road taken.

## What stands from the probe

`guard.md` and `install.md` are written (hunks at `guard.md` lines 20 and
33–38, `install.md` lines 71–76); the probe harness's `T1`–`T6` read them.

## What is left: the memo

`status:` is already `decided` (commit `ba0e061`, 2026-08-29) and stays so —
no `status:` change. The body moves from "recorded, not changed" to the road
taken, and the frontmatter gains two keys `resources/memos.py check` allows:

- `## Decision` — open with the guard row taken: `guard.py pre` refuses an
  `Edit` or `Write` under the skill root from a session whose board is not
  this repo's, naming the real path, this memo, and the two ways out; keep
  the count of seven sessions as the record of what it cost.
- `## Alternatives considered` — the second alternative is now the decision;
  say so in its first sentence; keep the other two as rejected.
- `## Consequences` — replace `Until a guard row exists, …` with what holds
  now: a `Bash` write is not matched, so `git status` here is still not
  evidence of what the sessions on this board did — the `Claude-Session:`
  trailer is.
- `prds:` gains `- the-skill-tree-is-guarded`; `updated:` set to the day the
  memo is rewritten, in ISO 8601, never earlier than `date:`.

## Acceptance

- [x] `references/parts/guard.md` `## What it refuses` has one row beginning `| an \`Edit\` or \`Write\` whose \`file_path\` resolves — through any install link, or by name — to a file under this skill's own root`, and the row names `the-install-is-live-symlinks`, `file a PRD on the skill's own board, or hand the edit to a session working it`
- [x] `references/parts/guard.md` holds the sentence `The skill-tree refusal matches \`Edit\` and \`Write\` only.` and, in the same paragraph, that a `>` or a `tee` through a link goes through unrefused
- [x] `references/install.md`'s `**Links, not copies.**` bullet holds `The links run the other way too` and names `prds/memos/the-install-is-live-symlinks.md` and `@references/parts/guard.md`
- [x] `prds/memos/the-install-is-live-symlinks.md` keeps `status: decided`, lists `- the-skill-tree-is-guarded` under `prds:`, carries `updated:`, and its `## Decision` names `guard.py pre` and the refusal; the phrase `Until a guard row exists` is gone
- [x] `python3 resources/memos.py check prds` prints nothing and exits 0
- [x] `python3 resources/index.py check` prints nothing — no anchor moved
- [x] `prds/the-board-runs-itself/the-next-line-runs/probe/verify.sh` still prints `96 checks · 96 pass · 0 fail` — its `install.md` needles hold

## Verify and Proof

```sh
grep -c '^| an `Edit` or `Write` whose `file_path` resolves' references/parts/guard.md
grep -c 'The skill-tree refusal matches `Edit` and `Write` only' references/parts/guard.md
grep -c 'The links run the other way too' references/install.md
grep -n 'the-install-is-live-symlinks' references/install.md references/parts/guard.md
grep -n '^status:\|^updated:\|the-skill-tree-is-guarded\|Until a guard row exists' prds/memos/the-install-is-live-symlinks.md
python3 resources/memos.py check prds; echo "exit=$?"
python3 resources/index.py check; echo "exit=$?"
bash prds/the-board-runs-itself/the-next-line-runs/probe/verify.sh </dev/null | tail -1
```
