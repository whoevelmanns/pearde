# The example board

One small board with a row in every band of the pressure order. Every check
in this repo runs against a copy of it, and it is the board the quickstart
opens. `python3 resources/board/plan.py example <dir>` copies it; nothing runs
it in place, because a check that ticks a box here changes what every other
check sees.

| PRD | state | shows |
|---|---|---|
| `landed` | `done` | the landed band — a `commit:` a reader can follow and an `actual:` the calibration reads |
| `building` | `claimed` | in flight — five boxes, three closed, a claim held since a written timestamp |
| `finished` | `claimed` | to collect — every box closed and `prd.md` clean, the band that leads every list |
| `asking` | `question` | waiting on you — one round, three answers, one recommended, rendered as picks |
| `next` | `open` | gated — it needs `building`, and the scan says so |
| `big` | `open` | the tree — a parent that weighs zero, with `big/first` landed and `big/second` open |

Beside them: `settings.md` names the board `example` in English, `memos/`
holds the one decision this board records, and `workflows/` holds one route of
two atomics that `building` follows.

Every date in here is written, never stamped. `building`'s claim reads
`2026-08-28 13:49`, so a rendered holding time grows with the clock and the
view's gate normalises it before comparing snapshots.
