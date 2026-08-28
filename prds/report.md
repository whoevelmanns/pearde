# Where the pearde skill stands

*2026-08-28*

Two streams are running on this board at once. Workflows are now a real
thing: a worker can be handed a written route instead of a description of
one, and when a run goes wrong the fix goes back into the route rather than
into someone's memory — five of six pieces landed, the sixth waiting on the
second stream to clear one shared file. The second stream is the bigger one:
making the board run itself, so that moving a piece of work is one command
rather than a dozen hand edits, and a newcomer has a board in five minutes.
Its contract is written and reviewed; six of its thirteen pieces are being
worked out right now. Eight of twenty-four pieces are finished today.

## In work

**Six pieces of the board running itself — being worked out.** A small example
board every check will run against; the single `pearde` command in front of
every script; the commands that move work between states and refuse what the
rules forbid; the command that turns spec files into "ready to build" and an
analyst's split into child pieces; the command that closes finished work —
runs the checks, commits only that work's own changes, marks it done; and a
board-level statement of where the work is going, so the plan orders toward
it. Each has a worker building a first pass to find out what it really takes,
and each turns into build-ready specs when that pass reports.

**The first set of routes — being closed out.** Five routes over thirteen
steps, written, checked, and already in use: the six workers above are all
running under one of them. Its checks are green; it waits on its worker's
final report.

## Planned

In the order they will happen:

- **The worker's brief printed by a command** instead of composed from three
  files at every dispatch.
- **A board that exists after one command** — no question asked; the
  language defaults to English and says so on its first line.
- **The live page shows the round** — what is finished, what waits on you,
  which workers are still moving and which have gone quiet.
- **Oversized work splits itself** — a size limit in the settings, and a
  piece over it becomes children without anyone being asked.
- **The round written as the commands it runs**, on one page under 120
  lines, with every rule the tool now enforces deleted from the prose.
- **The door to the routes** — asking for a route by name from anywhere the
  other tools are reached; held until the shared file above is committed.
- and three more behind these: the README rewritten for a person, the cost
  of each round shown on the page, and the workflows feature closing as one.

## Undecided or failing

Nothing is waiting on you.

Two calls made today without asking, both written down with what they beat:
the tool moves the states and the prose becomes its spec; and a new board
defaults its language to English rather than asking. If either is wrong, say
so — they are one file each to reverse.

Set aside, on your earlier decision: the manifest folder-row fix, the rule
for where throwaway test code lives, and the health check's false problem on
a valid group of boards. The first two are absorbed into the stream above
where its own checks need them — the folder row into the example board, the
test-code rule into the printed brief. The health-check one stays parked:
nobody is on it, and it says so here rather than pretending otherwise.
Nothing is lost.
