# pearde — improvements report

Ranked by impact. Verified against the repo as of 2026-08-31.

## 1. Delete `resources/board/state/serve.log` — 2.3 MB

**The file:** 2,304,723 lines of the live view service's stdout log.  
**Tracked:** yes, gitignored in spirit but noise in practice — `git status` shows it as untracked and it clutters the working tree.  
**Read by:** nothing. Python's `serve.py` writes it; `doctor.sh` does not read it.  
**Fix:** `rm resources/board/state/serve.log`. Regenerable from the service.  
**Impact:** eliminates the single largest file in the repo, clears `git status` noise.

## 2. Delete `resources/board/__pycache__/` — compiled bytecode

**The problem:** six `.cpython-314.pyc` files checked in, including `_plan_at_HEAD.cpython-314.pyc` — a cache named as if permanent. Python regenerates these on import.  
**Read by:** nothing in source.  
**Fix:** `rm -rf resources/board/__pycache__`. Add `__pycache__/` to `.gitignore` (currently absent).

## 3. `references/plugins.md` & `resources/board/knowledge/WORKFLOW.md` — dead `vicky` calls

**The problem:** `WORKFLOW.md` (both the template copy and the live `prds/knowledge/WORKFLOW.md`) instructs rounds to call `vicky:research`, `vicky:learn`, `vicky:crystalize`. The vicky plugin was uninstalled on 2026-08-31 — see memory `pearde-knowledge-integration.md`. These are dead instructions.  
**Fix:** rewrite those four lines to call `graphify` directly (`graphify extract`, `graphify update`, `graphify query`), which is what actually ships on the machine at `~/.local/bin/graphify`.

## 4. Memory says skills live in `~/.claude/max/skills`; they live in `~/.claude/skills`

**The problem:** `pearde-install-layout.md` records the install path as `~/.claude/max/skills`. The real folders are `~/.claude/skills/pearde`, `pearde-doctor`, etc. — 14 folders, all symlinked into the repo. `~/.claude/max/skills` does not exist.  
**Fix:** correct the memory file. Anyone following it installs into the wrong directory.

## 5. `references/install.md` — wrong fallback path

**The problem:** the plugins row reads `$CLAUDE_CONFIG_DIR or ~/.claude`. The environment variable is `/Users/feb/.claude/litellm` — but this agent's real skills directory is `~/.claude/skills/`, which the doc never names.  
**Fix:** update the fallback path and name the real skills directory in the install instructions.

## 6. `prds/` has 48 PRDs with no lifecycle for finished ones

**The problem:** `doctor` reports 48 PRDs (39 requested, 9 derived, 7 live). Finished PRDs (`state: done`), parked ones (`a-parked-prd-comes-back`), and probe-only ones accumulate with no archive step. The scan walks all of them on every call.  
**Fix:** add an archive mechanism — a `pearde archive` command or an `archive/` folder, or at minimum document that old finished PRDs are swept manually.

## 7. `references/parts/*.md` (24 files) vs `skills/*.md` (14 files) — the same mechanisms described twice

**The problem:** `parts/loop.md`, `parts/round.md`, `parts/states.md` describe the round, states, and round file. `skills/pearde.md` is the entry point for the same round. `parts/board.md` and `skills/pearde-view.md` overlap on the view. The content has already drifted — README's nine-state diagram and round table are not mirrored in `parts/states.md`.  
**Fix:** pick one canonical description per mechanism and have the other link to it rather than duplicate.

## 8. `resources/scout/snapshots/` — dated TSVs, unbounded growth

**The problem:** `2026-08-25.tsv`, `2026-08-28.tsv`, … each ~700 lines of star counts, one per sweep.  
**Fix:** rotate or cap them — keep N, or fold into `routes.md`/`findings.md` summaries. These are the only unbounded-growing data in the tree.

## 9. `resources/board/obsidian/` and `resources/board/knowledge/` — two overlapping vault presets

**The problem:** `board/obsidian/` is the `.obsidian` preset (dataview + local-rest-api). `board/knowledge/` is the knowledge-layer seed. Both are copied by `init` into a new board, and `prds/knowledge/` is the live instance of the second.  
**Fix:** confirm both are still needed; if yes, document which `init` copies when. The `files.md` manifest describes them as separate but the distinction is not obvious to a reader.

## 10. `resources/board/viewtest.js` and `hotreload-test.js` — tests never run

**The problem:** neither is wired into `doctor.sh --harnesses` (the harness row only finds `verify.sh` files under the board). They are gates for the view service that nothing runs.  
**Fix:** wire them into the doctor harness list, or delete them.

## 11. `prds/.view.html` — generated render, committed

**The problem:** a self-contained HTML render of the board, listed in `install.md` as "machine-local and regenerable" but committed anyway.  
**Fix:** gitignore it like `.plan.json` and `.history.jsonl`, or stop committing it.

## 12. `prds/.plan.json`, `.history.jsonl`, `.transitions.jsonl` — three state files for one board

**The problem:** the board has `.round.md` (session state), `.plan.json` (the plan), `.history.jsonl` (transitions), `.transitions.jsonl` (appears to be the same thing), and `.view.html`. `.history.jsonl` and `.transitions.jsonl` look like the same record.  
**Fix:** confirm which is authoritative and drop the other, or merge them.
