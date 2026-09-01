#!/bin/bash
# pearde graph — graphify rounds over any folder, Obsidian vault out.
#
#   graph.sh extract [folder] [--force]   full extraction, clusters + Obsidian vault
#   graph.sh update [folder]              re-extract changed files only (AST, no LLM), vault rebuilt
#   graph.sh query [folder] "question"    BFS over graph.json, capped budget
#   graph.sh path [folder] "A" "B"        shortest path between two nodes
#   graph.sh explain [folder] "X"         one node and its neighbors, plain language
#   graph.sh god-nodes [folder]           most connected nodes
#   graph.sh open [folder]                open .pearde/graphify/obsidian as a vault
#
# Output lands in <folder>/.pearde/graphify/ — graphify's own default
# (graphify-out/ relative to cwd) is redirected there with GRAPHIFY_OUT, set
# absolute before every invocation so extract, update and every read command
# resolve to the same place with no --graph flag needed.
#
# Defaults come from here; PEARDE_GRAPH_MODEL / PEARDE_GRAPH_FOLDER override.
set -uo pipefail

# The skill root, resolved before any cd — `open` reads init.py's vault
# register writer from resources/board/.
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

BACKEND=ollama
MODEL="${PEARDE_GRAPH_MODEL:-glm-5.3-flash:cloud}"

cmd="${1:-help}"; [ $# -gt 0 ] && shift

case "$cmd" in
  extract|update|query|path|explain|god-nodes|open)
    : ;;
  help|-h|--help|"")
    awk 'NR>1 && /^#/ {sub(/^# ?/,""); print; next} NR>1 {exit}' "$0"; exit 0 ;;
  *)
    echo "unknown command: $cmd (extract | update | query | path | explain | god-nodes | open)" >&2
    exit 2 ;;
esac

# First positional arg that is a directory is the folder; the rest are args.
FOLDER="${PEARDE_GRAPH_FOLDER:-.}"
ARGS=()
for a in "$@"; do
  if [ -d "$a" ] && [ "${#ARGS[@]}" -eq 0 ]; then FOLDER="$a"; else ARGS+=("$a"); fi
done

cd "$FOLDER" || exit 1
FOLDER_ABS="$(pwd)"

# Absolute, so extract/update's target-relative writes (a resolved scan root
# and the .graphify_root marker) land under the FOLDER being graphed, not
# wherever the shell happened to start. graphify honours an absolute
# GRAPHIFY_OUT as-is (paths.py); every subcommand below gets it, so the read
# commands' own default (<GRAPHIFY_OUT>/graph.json) already resolves here —
# --graph is passed too, defensively, matching the PRD's stated shape.
export GRAPHIFY_OUT="$FOLDER_ABS/.pearde/graphify"
GRAPH_JSON="$GRAPHIFY_OUT/graph.json"

# The Obsidian vault is a product of a graph round, not a separate command a
# person has to know to run: the pearde-graph skill describes
# .pearde/graphify/obsidian/ as an output of extraction, and `graph.sh open`
# opens it. graphify writes it ONLY from `export obsidian` — its `extract`
# has no obsidian step at all — so every round that rebuilds graph.json ends
# here. Pure graph.json -> notes: no LLM call, no network. One function, so
# extract and update cannot drift apart.
export_vault() {
  # Export into an EMPTY directory. graphify refuses to overwrite notes it
  # did not itself create, so exporting over a previous vault silently skips
  # every colliding note — 16 of 1311 on this repo (Drill.md, PRD.md,
  # Settings.md, the templates...) — and warns instead of failing, leaving a
  # vault that is quietly short. Its own advice is to export into an empty
  # directory. The vault is pure output (references/graph.md: "edit nothing
  # in it, edit the corpus and re-extract instead") and graphify writes even
  # its .obsidian/ config, so nothing of anyone's is lost by clearing it.
  [ -n "${GRAPHIFY_OUT:-}" ] || { echo "export_vault: GRAPHIFY_OUT unset" >&2; return 1; }
  rm -rf "$GRAPHIFY_OUT/obsidian"
  graphify export obsidian --graph "$GRAPH_JSON"
}

case "$cmd" in
  extract)
    graphify extract "$FOLDER_ABS" --backend "$BACKEND" --model "$MODEL" --max-concurrency 1 ${ARGS[@]:-} \
      && export_vault
    ;;
  update)
    # Pass the resolved absolute path, not ".": update never writes the
    # .graphify_root marker (only extract does, cli.py, and both its writes
    # resolve) — it only READS it, to recover a scan root when no path
    # argument is given. Naming the folder absolutely keeps the scan root
    # _rebuild_code relativizes against independent of the caller's cwd.
    graphify update "$FOLDER_ABS" \
      && export_vault
    ;;
  query)
    graphify query "${ARGS[0]}" --graph "$GRAPH_JSON" ${ARGS[@]:1}
    ;;
  path)
    graphify path "${ARGS[0]}" "${ARGS[1]}" --graph "$GRAPH_JSON"
    ;;
  explain)
    graphify explain "${ARGS[0]}" --graph "$GRAPH_JSON"
    ;;
  god-nodes)
    graphify god-nodes --graph "$GRAPH_JSON"
    ;;
  open)
    # `obsidian://open?path=` only resolves a vault Obsidian has registered —
    # an unregistered folder opens its nearest registered ancestor instead
    # (the board's own vault, which is not this one). So the graph vault is
    # registered by exact path first, through init.py's own writer, and the
    # URI names it by id. Obsidian rewrites its register on quit: a
    # registration made while the app runs is certain after a restart.
    VAULT_URI=$(python3 -c "
import os, sys, urllib.parse
sys.path.insert(0, os.path.join('$SKILL_DIR', 'resources', 'board'))
vault = os.path.abspath(os.path.join('$GRAPHIFY_OUT', 'obsidian'))
try:
    import init
    _, vid = init.register_vault(vault)
except Exception:
    vid = None
print('obsidian://open?vault=' + vid if vid
      else 'obsidian://open?path=' + urllib.parse.quote(vault))
")
    open "$VAULT_URI"
    ;;
esac