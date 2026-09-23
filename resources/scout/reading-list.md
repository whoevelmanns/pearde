# The reading list — repos to read, not install

The star chart is the discovery layer, not the value layer. This is the
curated residue of the sweeps: repos whose *content* or *mechanisms* are worth
reading, each mapped to the tree it improves and the thing to steal. A repo
lands here only with an answer to "what does this change in our trees" —
stars alone put a repo in the snapshot, never here.

Three genres, in rising order of value:

1. **Link-lists** (`awesome-*`) — discovery scaffolding. Use the index, move on.
2. **Case-study corpora** (awesome-scalability, system-design-101) — real
   architectures, organized by principle. The reading itself.
3. **Reference implementations** (codex, mem0, nextest) — code whose design
   answers a question our tree is asking. The copying itself.

## For mitosys — the harness (record, orchestration, plugins, surfaces)

| repo | ★ | what to read | what to steal |
|---|---|---|---|
| [openai/codex](https://github.com/openai/codex) | 117k | `core/src` — the turn loop, tool dispatch, sandbox policy | the turn-loop shape: how a harness interrupts a running tool, streams partial output, and enforces a permission boundary *without* losing the turn's record. mitosys's orchestration + surfaces face the same problem |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | 236k | the agent lifecycle — spawn, memory injection, growth | the "agent that grows with you" framing is mitosys's own thesis; read how they structure session→memory handoff vs our record spine |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | 64k | `mem0/` — the memory extraction + consolidation pipeline | their `add` → extract-facts → consolidate-into-graph flow is the same problem as mitosys's ingest→record compression, solved at production scale. Compare their consolidation triggers to ours |
| [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | 92k | session capture → AI compression → context re-injection | the *capture-everything, compress-later* stance is the opposite of our tick-requires-evidence stance. Read it as the reductio: what their compression loses that our record keeps, and what their injection does that our surfaces don't |
| [rtk-ai/rtk](https://github.com/rtk-ai/rtk) | 77k | a Rust CLI that compresses LLM I/O by 60-90% | single-binary, zero-dep Rust — the same packaging discipline as `conserved`. The token-compression tables are directly relevant to every LLM surface mitosys runs |
| [ratatui/ratzilla](https://github.com/ratatui/ratzilla) | 1.4k | `src/backend/` — same `ratatui::Widget` trait rendered through a WASM/canvas backend instead of a terminal one | `mitosys`'s `src/surfaces/tui` is already ratatui; this is the mechanism for a `p3-surfaces` web surface that reuses the same widget code instead of a second implementation — see "one widget API → terminal + web + native desktop" in `findings.md`. Rejected `Dioxus` for this: its TUI renderer (`dioxus-tui`) was dropped from the monorepo in 2024, two major versions behind current |

## For model — the learner (ledger, peer mesh, improving loop)

| repo | ★ | what to read | what to steal |
|---|---|---|---|
| [papers-we-love/papers-we-love](https://github.com/papers-we-love/papers-we-love) | 109k | the distributed-systems and ML sections | the primary sources behind the pattern lists — Lamport, PACELC, the gossip literature. model's peer mesh is a gossip problem; read the originals before the summaries |
| [binhnguyennus/awesome-scalability](https://github.com/binhnguyennus/awesome-scalability) | 74k | **Stability** (crash-safe replication, timeouts) and **Availability** (failover) sections | the case studies are the ledger's future: what happens to an append-only record under partition, failover, and crash — from Netflix/Twitter/Facebook systems that already hit it. Pushed 2026-01; the *pattern index* is stable even where links age |
| [ByteByteGoHq/system-design-101](https://github.com/ByteByteGoHq/system-design-101) | 88k | the diagrams — each pattern as one picture | the visual grammar for the shapes model already implements (quorum, leader election, anti-entropy). Unmaintained since 2025-04 — read the diagrams, do not cite the repo as current |
| [karanpratapsingh/system-design](https://github.com/karanpratapsingh/system-design) | 46k | the consistency and replication chapters, maintained 2026-07 | the freshest of the system-design corpora; the successor to system-design-101's abandoned text |

## For model — the support model that knows a harness

The job (`findings.md`: *give a general LLM knowledge of one tree it never
saw*) is a corpus→weights compile plus a two-arm comparative gate. These four
are the reference implementations of those two halves.

| repo | ★ | what to read | what to steal |
|---|---|---|---|
| [karpathy/nanochat](https://github.com/karpathy/nanochat) | 58k | the whole pipeline end to end — tokenizer, pretrain, mid-train, SFT, eval, serve — as one readable repo | the *shape of the compile*. `the-harness-is-its-own-corpus` says the record is the dataset; this is the only short repo that shows every stage between a text corpus and a served model without a framework in the way. Pushed 25d ago, active. The closest thing to a spec for what `src/learning/` + `src/teacher/` have to become |
| [karpathy/nanoGPT](https://github.com/karpathy/nanoGPT) | 63k | `model.py` — a decoder in ~300 lines; `train.py` for the loop | the minimal substrate against which `src/transformers/` is judged. Read it as the floor: anything we add on top of this has to justify itself. **Last push 288d — read as finished, not abandoned**; the scout's activity heuristic flags it "slow" and is wrong about what that means here |
| [EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | 14k | the task/model abstraction — one question set, many model backends, recorded results | the **two-arm gate** in `the-support-model-knows-the-harness`, which needs exactly this: our model and a general-model arm answering one human-authored set, with the gap as the reading. `src/grade/` currently has no notion of a second arm. Active, 0d |
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | 25k | the declarative config — assertions as data, providers swapped per run | the alternative to the above for the same slot, and the better one if the question set should be a *recorded file* rather than code. That framing matches DOGMA 8 (gates recorded, never claimed) more closely than a Python task class does. Active, 0d |

## For the whole family — testing the harness itself

| repo | ★ | what to read | what to steal |
|---|---|---|---|
| [nextest-rs/nextest](https://github.com/nextest-rs/nextest) | 3.2k | `nextest-runner/src/` — process-per-test supervision, the retry model | the supervision tree: how nextest kills a hung test *and its grandchildren* (a problem mitosys's orchestration shares — see `close_kills_a_grandchild_that_ignores_the_group_sigterm`, green today) |
| [spacejam/sled](https://github.com/spacejam/sled) | 9.1k | `tests/` — the crash-recovery and deterministic-simulation discipline | how a storage engine proves itself without a real crash: seeded fault injection, exhaustive partial-write tests. Directly applicable to the record spine and the ledger |
| [cargo-mutants](https://github.com/sourcefrog/cargo-mutants) | 1.3k | `src/mutate.rs` — the mutation grammar | which mutations a test suite is blind to, computed rather than guessed. The vacuity check our gates currently do by human judgement |

## Anti-list — high stars, no entry

- `affaan-m/ECC` (243k★), `Graphify-Labs/graphify` (110k★), `DietrichGebert/ponytail` (110k★) — the top of the agents bucket by stars. Star velocity without a describable mechanism is the hype signature; nothing to read that a description doesn't already say. Revisit only if a delta sweep shows them *holding* stars for a quarter.
- `langchain`, `crewAI` — framework shape is the opposite of ours (abstraction over many models vs one harness over one spine). Reading them teaches the trade we already declined.

## Maintenance

This list is hand-curated and intentionally short. The sweeps keep producing
candidates. An entry survives one question — *which file in which tree changes
because we read this* — and the answer is written into the table before the
repo is added.
