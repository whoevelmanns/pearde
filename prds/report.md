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
Twelve of the fourteen pieces are landed and committed. The workflow routes
are landed too, and have been improved by twenty-four real runs today.

## In work

**The README for a newcomer — being closed out.** Sixty seconds to a
running board, the six files on disk, the nine states as one picture, three
rings that let a reader stop where they need to. Written and proven end to
end; the last checks are running.

**The round's cost on the page — being worked out.** How many calls each
step of a round spent, drawn over time, so a round that starts re-deriving
shows it while it happens.

**The first minute runs as printed — being worked out.** The line the
board prints as "run this next" was refused when typed, because it lacked a
flag a newcomer has never heard of. Found while proving the README; fixed
where it belongs.

**Workflows are finished except the door.** A worker can now be handed a
written route instead of a description of one: five routes over thirteen
steps, covering the jobs this repo actually repeats — adding a file, adding
a setting, building from a spec, working out what a vague request needs,
and correcting a claim that turns out to be written in three places. When a
run goes wrong, the fix goes back into the route rather than into someone's
memory, and the routes have been followed twenty-four times today. Their
"what went wrong and what to do" tables were written entirely from real
failures — nothing in them was invented. One piece is left: the door that
lets you ask for a route by name from anywhere the other tools are reached.
It is ready and waiting on the README, which is mid-edit in the same files.

## Planned

- **The door to the routes** — the moment the README lands.
- **Something that runs the checks.** This repo has about a thousand
  automated checks and nothing that runs them — no continuous integration,
  no hook, nothing in the health check. Every green result today happened
  because someone asked. That is now written down as a piece of work rather
  than left as a surprise; it also waits on the README.
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

**Separately, a defect that could stop everything was closed.** A single
mistyped number in any spec file used to crash the command every round
starts with, for every session at once, with nothing in the error to say
which file. Nine such unguarded numbers were found, not one, along with three
more crashes and a parser bug that made a template's own explanatory comment
parse as if it were a value. A bad number is now reported by name and the
work is treated as unsized, never as free.

**And one more closed:** the one-command close of finished work could put a
line in the wrong place on a tree several sessions write, and still look
right. It now rebuilds the file and proves the placement before any commit.

Two of the three pieces set aside earlier have landed inside the work above
and are marked so; the third stays parked.
