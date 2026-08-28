# Where the pearde skill stands

*2026-08-28, late evening*

The board runs itself now, in the ways that were promised this morning.
`pearde` is one command in front of every tool; moving a piece of work
between states is a command that checks its own rule and refuses with the
rule named; spec files become "ready to build" and an oversized piece splits
into children by command; finished work is closed by one call that runs the
checks and commits only that work's own changes; a worker's brief is printed,
not composed; a board exists after one command that asks nothing; a board can
say where it is going and the plan orders toward it; the live page shows what
the session is doing and which workers have gone quiet; and the round itself
is written as the calls it makes, on one page a third of its former length.
Eleven of the thirteen pieces are landed and committed. The workflow routes
are landed too, and have been improved by twenty-four real runs today.

## In work

**The README for a newcomer — being worked out.** Sixty seconds to a running
board, the six files on disk, the nine states as one picture, three rings
that let a reader stop where they need to.

**A fix to how finished work is committed — being worked out.** Found today
while closing the page: on a tree two sessions write at once, one way of
staging a change can put a line in the wrong place and still look right. The
one-command close now rebuilds the file instead, and proves the placement
before any commit.

## Planned

- **The cost of each round on the page** — waits on a small crash guard
  another session is landing in the same file first.
- **The health check's false problem on a valid group of boards** — parked,
  nobody on it, as decided earlier.

## Undecided or failing

**One deletion waits on another session.** The board-level vision is built
and landed; the old script that computed it on the master board still has to
be deleted there, and that board belongs to the session working it. It has
been asked twice today and has not answered; nothing on that board moves
until it does.

Two calls made today without asking, both written down with what they beat:
the tool moves the states and the prose becomes its spec; and a new board
defaults its language to English rather than asking. Both are in effect.

Two of the three pieces set aside earlier have landed inside the work above
and are marked so; the third stays parked.
