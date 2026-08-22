# Language

How everything here is written: this definition, the PRDs, the specs, the
reports workers hand back.

Short. On the point. Precise.

**One idea per sentence.** If a sentence needs a comma to hold two thoughts,
it is two sentences.

**Imperative.** Say what to do. "Set `specced`", not "the state should then be
set to specced".

**Name the thing.** The file, the state, the command, the field. Never "the
relevant config" when you mean `PRD_TEMPLATE.md`.

**No hedging.** No "might", "probably", "if you like", "consider". A rule is a
rule. If something is genuinely a choice, say who chooses and when.

**No meta.** Do not describe the document inside the document. No "this section
explains", no "as mentioned above".

**No legacy.** Describe what is true now. No former names, no migration notes,
no deprecated aliases, no "previously called". Rename and move on. History
lives in version control, not in the prose.

**Rationale only where it changes a decision.** "One writer means nothing to
race" earns its line — it tells you why there is no locking. "This is important
for correctness" does not.

**Delete, do not deprecate.** A stale line is worse than a missing one, because
it is read as current.

Prose in a PRD is a contract an analyst reads cold, without this conversation.
Prose in a spec is a checklist an implementer runs. Write for that reader.
