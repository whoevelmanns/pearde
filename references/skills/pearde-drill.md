---
name: pearde-drill
description: Interview a vague request until it is a contract that can be specced — one round of questions covering the whole frontier at once, each carrying a recommended answer, until nothing is left that would change the work. Ends in a settled contract and a PRD tree, each branch a child. Use for "/drill", "drill this", "drill <prd>", "help me work out what I want", "this request is too vague", "ask me what you need to know", "turn this into a spec", "interview me about this feature", "what questions do you have before building". Run it before dispatching anything — a one-line title is too thin to spec.
---

Read @references/drill.md — one round over the whole frontier, the shape a
question must have, what one may never say, the exact round and answer
formats, that nothing is dispatched while a drill runs, and the tree it ends
in. The scope is `@@drill`. @references/templates/prd.md is the shape of each
branch it writes, @references/parts/contract.md the keys.

With no board in scope this still works: it is an interview, and the tree it
would write is the answer. Say so rather than creating `prds/` uninvited.
