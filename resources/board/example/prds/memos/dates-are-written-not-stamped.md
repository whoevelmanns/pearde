---
memo: dates-are-written-not-stamped
kind: decision
status: decided
subject: Every date on this board is a fixed string, so a copy renders the same page every time
date: 2026-08-28
prds:
  - building
---

# dates-are-written-not-stamped — a fixed date, not the clock

## Decision

Every `claim:`, `date:` and `actual:` on this board is written by hand and
never updated by a tool. `building`'s claim reads `2026-08-28 13:49` and
stays there.

## Why

The board exists to be copied and compared. A claim stamped at copy time
would render the same holding time on every run and hide the one thing the
view's gate has to normalise; a claim written once renders a holding time
that grows, which is what the real board does, and the gate learns to read
past it.

## Alternatives considered

**Stamp the claim when the copy is made** — the page is identical on every
run, but the normaliser is never exercised and a regression in it goes
unseen.

**Carry no claim at all** — no holding time to normalise, and no in-flight
band to check.

## Consequences

- The rendered holding time on `building` is different on every run, and
  every snapshot comparison normalises it before reading.
- It does not fix a date that is wrong; it only fixes where a date comes
  from.
