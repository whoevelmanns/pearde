---
name: pearde-drill
description: Interview a vague request until it is a contract that can be specced — one round of questions covering the whole frontier at once, each carrying a recommended answer, until nothing is left that would change the work. Ends in a settled contract and a PRD tree, each branch a child. Use for "/drill", "drill this", "drill <prd>", "help me work out what I want", "this request is too vague", "ask me what you need to know", "turn this into a spec", "interview me about this feature", "what questions do you have before building". Run it before dispatching anything — a one-line title is too thin to spec.
---

Read @references/drill.md. The scope is `@@drill`.

- **One round, the whole frontier.** Not one question at a time — every
  question the work turns on, asked together, each with the answer you would
  give if the user said "you decide".
- **Recommend, do not survey.** A question with no recommendation attached
  hands the work back to the user.
- **It ends in a tree, not a transcript.** The settled contract becomes the
  body, each branch a child directory, `state: open`.
  @references/templates/prd.md is the shape, @references/parts/contract.md
  the keys.
- **Dispatch nothing while a drill is running.** The board picks the tree up
  when the drill is finished, per `@@loop`.

With no board in scope this still works: it is an interview, and the tree it
would write is the answer. Say so rather than creating `prds/` uninvited.
