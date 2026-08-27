---
name: pearde-persona-create
description: Build a persona for a field the roster does not cover — research the field, research the real practitioners working in it, take one named trait from each, and compose a single fictional colleague holding the best of them. Written to references/personas/, registered, and selectable from that moment. Use for "/pearde-persona-create", "persona create <topic>", "make me a persona for <field>", "I need an expert in X", "we have no one for this field", "add a persona", "compose a specialist". A persona is built from research, never invented. Sibling skills: pearde-persona switches who is working, pearde-persona-ask puts one problem to an existing colleague.
---

Read @references/personas/INDEX.md — the section is **`persona create
<topic>`**, and it is the procedure, in order. The scope is `@@personas`.

- **Research, never invention.** Two passes: what the best work in this field
  actually does and what separates it from merely competent work, then the
  named practitioners actually doing it. The second is a fact, not a
  decision — look it up, dispatch workers for it, and never ask the user for
  names you could find.
- **One named trait per person.** A small biography each: who they are, what
  they are known for, and the one specific thing to take. A trait you cannot
  name is a person who does not belong in the persona.
- **Compose one, fictional, with its own name.** Its first line says it is a
  composite. No reader may be misled that a real person said this, and no
  real person is quoted.
- **The id is the profession in one lowercase word**, never the name.
- **Register it everywhere or it is not live**: the file, the Roster row in
  @references/personas/INDEX.md, the signals table in
  @references/parts/personas.md, `@@personas` in @index.md, and its row in
  @references/files.md. Then say it is selectable.
- **An id that already exists is a merge, not a new persona.** Fold the new
  research into that file's **Built from** and say what changed.

Then call it — `pearde-persona-ask` — or wear it with `pearde-persona`.
