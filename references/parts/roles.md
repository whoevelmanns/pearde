# Roles

Who does what. The role is the job. The persona is who holds it.

| role             | does                                                        |
|------------------|--------------------------------------------------------------|
| **orchestrator** | works the board. The ONLY writer of PRD state — nothing to race, so no locking. One per board; on a master board it owns every member it merges |
| **analyst**      | turns one `open` PRD into specs, a split, or questions       |
| **implementer**  | turns one `specced` PRD's specs into verified code           |
| **consultant**   | a persona the orchestrator calls mid-round and talks to. Reads the session and the board, answers, writes nothing |

Workers do the work. The orchestrator moves the states. A consultant does
neither: it is called, it answers, and the exchange stays open until the
question is settled — @references/parts/personas.md.

The role is what the session does. The persona is who does it —
@references/personas/INDEX.md.
